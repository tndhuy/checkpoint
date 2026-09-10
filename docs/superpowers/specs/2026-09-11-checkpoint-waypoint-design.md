# Checkpoint waypoint logging tier — design

Status: approved (chat, 2026-09-11) — pending spec self-review and user sign-off on this document.

## Background

`$checkpoint:save` currently reconstructs project state (branch, changed files, recent activity, narrative context) purely from conversational memory and a fresh round of git inspection at write time. This works, but it makes every full checkpoint write as expensive as the first one, even when nothing mechanically relevant has changed since the last write.

This was raised by the user directly, alongside a real, disclosed reason: the user has ADHD-related working-memory difficulties and built this plugin specifically to offload state so it doesn't have to be held in the user's head. Two concrete defects in that promise were already fixed this cycle (v0.1.19/v0.1.20: language drift on update, wholesale-rewrite-on-update). This spec addresses a third, different problem: the *cost* of producing a checkpoint at all, not its correctness once produced.

The user asked whether checkpoint-skill should adopt an "ambient" background-capture model similar to the separately-installed `claude-mem` plugin, while keeping the two tools' purposes distinct. Direct inspection of `claude-mem`'s bundled hooks (`~/.claude/plugins/cache/thedotmack/claude-mem/13.24.5/hooks/hooks.json`) found it registers `PostToolUse`/`Stop` hooks with `"async": true`, dispatching to a background worker process that uses a cheap Haiku-tier model for summarization. That specific mechanism — an LLM summarizing in the background — is deliberately **not** adopted here: it would blur the boundary between the two tools and reintroduce the same "who decides what's worth remembering" judgment call that `claude-mem` already owns. Instead, this design borrows only the async-hook *delivery pattern*, not the LLM-summarization step, and keeps the captured data purely mechanical (git/session facts, no synthesis).

Two design points were corrected during this process rather than assumed correct on first pass, both worth recording so they aren't re-litigated:

1. **Async hook semantics.** Initial design assumed making the existing `stop-checkpoint.js` nudge `async: true` would reduce interruption while preserving the safety net. Official docs (`https://code.claude.com/docs/en/hooks`) confirm async hook output is delivered only while the session runs / on the next conversation turn — if the session ends before another turn, the result is never delivered. Since `Stop` exists specifically to catch the case where the session is ending, making it async would silently disable it. Resolved: `stop-checkpoint.js` stays synchronous and unchanged; a **separate, additional** hook entry, async, is added purely for waypoint-writing, which has no such delivery requirement (a missed waypoint just means slightly less mechanical evidence next time, not a broken safety net).
2. **Storage location vs. the `scope: global` invariant.** An earlier pass of this design put the waypoint log at `.checkpoint/waypoints.jsonl` inside the project. `references/scope-and-role.md` (line 21) is explicit: under `scope: global`, write nothing inside the project. A second `/advisor` review caught this contradiction. Resolved: waypoints live in the OS tmp directory, keyed by the project's absolute path — mirroring the existing cooldown-marker precedent in `stop-checkpoint.js` — so the hook never needs to resolve `scope` at all (resolving scope/role inside a hook script was already forbidden as of the 0.1.13 decision).

## Goals

- Reduce the effective cost of producing a full checkpoint by pre-capturing mechanically-derivable facts (git state, timestamps) as they naturally occur, instead of re-deriving all of them at `save` time.
- Reuse the existing `save` skill as the sole consumer — no new "squash" skill or command.
- Zero LLM involvement in capture. Waypoints are written by a plain script from `git` output; no summarization, no judgment calls.
- Preserve every existing safety invariant: hooks never write a checkpoint file autonomously; `stop-checkpoint.js`'s synchronous nudge is untouched; no hook resolves `scope`/`role`.
- Fail-open: any failure to write or read a waypoint degrades silently to today's behavior (`save` re-derives everything itself), never blocks or errors visibly.

## Non-goals (explicitly out of scope for this pass)

- **No benefit to in-session manual `save`.** When the user runs `$checkpoint:save` mid-session, the agent already has full conversational context; waypoints add nothing there. The payoff is specifically post-compact, fresh-session, and `recall` — where that context is gone and would otherwise have to be reconstructed from git alone.
- **No LLM-based summarization at capture time.** This is the deliberate point of difference from `claude-mem` — waypoints are mechanical facts only, never narrative. `claude-mem` and checkpoint-skill remain two tools with two distinct jobs; this design does not make checkpoint-skill dependent on `claude-mem` being installed, and does not attempt to replace it.
- **No new skill or slash command.** Consumption is folded into the existing `save` skill, not a separate "waypoint" or "squash" verb.
- **No recall of a specific historical waypoint.** The log is consumed forward-only as evidence for the next `save`; it is not a browsable history in its own right (that role already belongs to the revision history design, `2026-08-27-checkpoint-revisions-design.md`).
- **No cross-machine or cross-session sync of the waypoint log.** It lives in local tmp storage; if tmp is cleared (reboot, `/tmp` cleanup), `save` simply falls back to today's from-scratch behavior. This is acceptable because waypoints are a cost optimization, not a durability guarantee — durability is the checkpoint file's job.

## Storage layout

```
<os-tmpdir>/checkpoint-waypoints/
├── <sha256(project-abs-path)>.jsonl      # append-only waypoint log
└── <sha256(project-abs-path)>.consumed   # marker: last-consumed position
```

No file is ever written inside the project, under either `scope: project` or `scope: global` — the hook does not resolve or read `scope` at all, sidestepping the invariant entirely rather than special-casing it. Keying by a hash of the project's absolute path mirrors the existing tmp-dir cooldown-marker mechanism in `stop-checkpoint.js`, so this introduces no new pattern, only a second use of one already reviewed and shipped.

## Capture: `waypoint-writer.js`

New hook script, registered as a **second, independent entry** under the existing `Stop` and `PreCompact` events in `hooks.json` — alongside, not replacing, `stop-checkpoint.js`'s existing synchronous entry. This new entry is declared `"async": true`.

On fire:
1. Run local, read-only git commands: `git rev-parse HEAD`, `git branch --show-current`, `git log -1 --format=%s`, `git status --porcelain`.
2. Compare the resulting `headSha` + `statusShort` against the last line of this project's `.jsonl` (if any). If identical, do nothing (dedupe — avoids logging the same state repeatedly across several `Stop` fires with no intervening work).
3. Otherwise append one JSON line:
   ```json
   {"timestamp": "2026-09-11T14:32:00+07:00", "cwd": "/abs/project/path", "branch": "main", "headSha": "a1b2c3d", "headMessage": "fix(checkpoint): ...", "statusShort": " M file.js\n?? new.md"}
   ```
4. Any failure at any step (not a git repo, tmp-dir unwritable, git binary missing) is caught and swallowed — no output, no exit-code failure, no chat message. This event is purely for future `save` calls to find; it has nothing useful to say to the user in the moment.

This keeps `waypoint-writer.js` a pure, mechanical script — no LLM call, no synthesis, matching the Goals section directly.

## Consumption: `save` skill changes

`plugins/checkpoint/skills/save/SKILL.md` gains a step, before evidence-gathering, that:

1. Computes the same `sha256(project-abs-path)` key and checks for a matching `.jsonl` in the tmp waypoint directory.
2. If present, reads only the lines after the position recorded in the sibling `.consumed` marker (or from the start, if no marker exists yet).
3. Uses those lines **only** for the mechanically-derivable parts of the checkpoint the plugin already treats as factual (branch, changed files, last commit, working-directory state) — never for `Outcome`, `Decision/learning`, or any section requiring judgment. This is the same boundary already drawn between "facts" and "narrative" that governs the diff-only update rule from v0.1.19/v0.1.20, and it is stated explicitly rather than left implicit, so a future editor doesn't blur it.
4. After the checkpoint file is successfully written, updates the `.consumed` marker to the newest position read. The waypoint `.jsonl` itself is never truncated or deleted — it is strictly append-only, and the marker is the only thing that moves.

This ordering (write checkpoint, then update marker) means a `save` that dies between the two steps simply leaves the marker stale — the next `save` re-reads a few already-used lines, which are harmless duplicate evidence, not corrupted state. There is no scenario in which a crash loses waypoint data or produces an inconsistent read, because the marker update is the only mutation and it happens last.

Reading the waypoint log is unconditional in `save` — every invocation checks for one — since the read is a small local file and effectively free. What is *not* unconditional is where the value shows up: after a compact, in a fresh session, or during `recall`, the waypoint log is the only mechanical evidence available and materially reduces re-derivation cost. Mid-session, the agent already has this information from conversation, so the read is a no-op in practice, not a special case that needs separate gating logic.

## Safety and threat review

This is a new autonomous write (`waypoint-writer.js` writes without an explicit `$checkpoint:save` invocation), which per `docs/DISTRIBUTION.md`'s bar requires documented need and threat review. Addressed as follows:

- **What is written:** exactly the six mechanical fields listed above, sourced from local `git` command output. No user input, no LLM output, and no conversational content ever reaches this file.
- **Where it is written:** OS tmp directory only, never inside the project tree, under either scope. This is strictly narrower than the existing cooldown-marker precedent's threat surface, which already established tmp-dir writes as acceptable for this plugin.
- **What it cannot do:** it cannot write, modify, or delete a checkpoint file. The invariant "hooks must never write a checkpoint on their own" is unchanged — this hook writes to a different file, in a different location, that `save` treats as optional evidence, never as an alternative destination.
- **Failure mode:** fail-open. A failed or missing waypoint write degrades `save` to exactly its current (pre-this-feature) behavior. There is no failure mode where a missing or corrupt waypoint file causes `save` to fail, since `save` treats the log as purely additive evidence and already handles "no waypoints found" as its default path.

A new subsection will be added to `docs/HOOKS.md` documenting this, following the same structure already used there for the cooldown-marker mechanism.

## Testing

- Unit tests for `waypoint-writer.js`, mirroring `tests/test_hooks_runtime.py`'s existing patterns: writes a correctly-keyed `.jsonl` line for a clean git repo; dedupes correctly when fired twice with no intervening commit or working-tree change; degrades silently (no thrown error, no output) when run outside a git repository or against a read-only tmp path.
- Unit test confirming the new `Stop`/`PreCompact` hook entries are registered as `"async": true"` and are additive (the existing synchronous `stop-checkpoint.js` entry is still present and unchanged) in `hooks.json`.
- Static content tests (same style as `tests/test_skill_instruction.py`) asserting `save/SKILL.md` documents: the waypoint read step, the facts-only boundary (never used for narrative sections), and the append-only/marker-only consumption model (no truncation language).
- Fresh-agent forward-test (mandatory for `SKILL.md` instruction changes per this repo's 2026-08-07 precedent): in a scratch project, trigger `Stop` twice with a commit in between, confirm two distinct waypoint lines are written; run `$checkpoint:save` and confirm the resulting checkpoint's mechanical fields match the waypoint evidence; run `save` again with no new waypoints and confirm it falls back to direct git inspection without erroring.

## Rollout

Version bump across all 4 tracked manifests and a `CHANGELOG.md` entry, matching this repo's established convention. Implementation proceeds via `writing-plans` once this document is approved — this is a single cohesive feature with sequential dependencies (hook script, then `hooks.json` registration, then `save` changes, then `docs/HOOKS.md` threat-review section, then tests), not independent parallelizable sub-projects.
