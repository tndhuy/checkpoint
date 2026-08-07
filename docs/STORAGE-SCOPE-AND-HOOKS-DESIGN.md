# Storage Scope, Flags, and Auto-Trigger Hooks — Design

Status: proposal, not implemented. Written 2026-08-07 in response to a user design brief covering: project vs. global checkpoint storage, `.gitignore` handling, flags instead of new commands, auto-trigger hooks after commit/push, a distinct "role" field, and closing the gap on two instructions (language-of-user, anti-rambling) that were already specified but apparently not holding in practice.

## Problem

`save`, `checkpoint`, `list`, and `recall` currently only say: prefer an existing project checkpoint/note, then today's Daily note, then a dedicated handoff note, then chat-only. There is no folder convention, no scope concept (project-only vs. one cross-project store the user controls), no `.gitignore` handling, and no auto-trigger. Anyone working across multiple repos in one session has no way to say "always put my checkpoints in one place" without the agent re-deriving a destination every time. (This session is itself an example: one turn touched `personal/developer-vault` and `personal/checkpoint-skill`, and the checkpoint ended up in the vault's Daily note by convention-following, not by configuration.)

## 1. Storage scope model

Two scopes:

- **`project`** (default) — checkpoint lives inside the current repo. If the repo already has a notes/vault convention the skill would otherwise prefer, keep using it (existing destination order is unchanged). Otherwise, fall back to a new top-level `.checkpoint/` directory.
- **`global`** — every project's checkpoints write into one root the user names once (e.g. `~/.checkpoint/<project-slug>/`, or an existing personal vault, as happened by convention this session). This makes that choice explicit and persistent instead of re-derived per save.

Resolution order on each `save`:

1. Explicit `--scope` flag → use it, and persist it as the new default for this project.
2. No flag, but a config marker already exists for this project (`.checkpoint/config.md` locally, or an entry in the global config keyed by project path) → use the recorded scope silently.
3. No flag, no marker → first run for this project. Ask exactly one question, reusing `recall`'s existing "ask exactly one multiple-choice question in the user's language" convention: *save checkpoints in this project, or in your global store at `<path>`?* Persist the answer.

This gets "ask once, remember, stay adjustable" without a dedicated init command — `save` does double duty as init on first use, which keeps the command surface at three.

Global root itself is asked for once, the first time any project picks `global` — offer a sensible default (`~/.checkpoint/`) or let the user point at an existing notes system — and store it in one user-level config. Keep the config format identical across hosts; only the storage root differs. This matches the repo's own model in `docs/DISTRIBUTION.md`: one tracked `SKILL.md`, host adapters only wrap it.

## 2. `.gitignore`

When scope is `project` and `.checkpoint/` is newly created, append `.checkpoint/` to the project's `.gitignore` — append, never overwrite; skip silently if already present. If the project has no `.gitignore` at all, ask before creating one — creating a new repo-root file is a bigger footprint than a checkpoint save should take on its own. Global scope needs no `.gitignore` handling since it lives outside any repo.

## 3. Command surface — flags, not new commands

Extend the three existing commands; no `/checkpoint:init`:

- `/checkpoint:save [--scope project|global]` — overrides the recorded scope for this save and updates the stored default.
- `/checkpoint:list [--scope project|global|all]` — default stays `all` (current behavior); the flag narrows.
- `/checkpoint:recall [--scope project|global]` — same narrowing, useful on the rare project that has checkpoints in both scopes after a scope change.

Document the flag in each `commands/*.md` `argument-hint`; each skill gains a short "Scope" section next to the existing "Choose destination" / "Destination" section — no new files.

## 4. `profile` vs. the requested "role" field — needs one decision before spec

These are different axes; don't merge them silently:

- **`profile`** (existing, `references/profiles.md`): what *kind of evidence* the checkpoint carries — `developer` / `research` / `operations` / `generic`. Inferred from context on every save.
- **The "role" ask**: sounds like a fact about *the human* — who they are relative to this work (implementer vs. reviewer vs. status-checking PM, for instance) — which would change what the checkpoint should assume its reader already knows, not what evidence type it holds.

**Decided: (b), scoped per project — not a single global value.**

Not (a): role is a relatively stable fact within one project's context; inferring it fresh on every `save` risks guessing wrong and violates the same evidence discipline the skill already applies elsewhere ("never invent"). Not a single global (b): the whole reason scope has both `project` and `global` storage is that this skill is used across many repos, and role plausibly differs across them (owner on your own vault, reviewer on someone else's PR-only repo).

Mechanism: reuse the config file and resolution order already specified for `--scope` in section 1 — no new infrastructure.

- Store `role` alongside `scope` in the same per-project config marker (`.checkpoint/config.md`).
- Resolution order, identical shape to scope: `--role` flag on `save` → override and persist as the new default for this project; no flag but a recorded value exists → use it silently; neither → ask once (can be the same first-run prompt that already asks about scope) and persist.
- Never inferred, never guessed — only read back a previously confirmed value, the same pattern `Meta/user-profile.md` already uses in the vault repo.

`role`'s field values are open (free text, not a closed enum like `profile`) since "implementer" / "reviewer" / "status-checking PM" isn't an exhaustive set — validate only that it's non-empty when scope resolution first runs.

## 5. Hooks — shortlist and justification

`docs/DISTRIBUTION.md` already sets the bar: *"Do not publish hooks, MCP servers, telemetry, network access, or autonomous writes unless a release has a documented need and threat review."* This section is that documentation.

Evidence used, not recalled from memory: this machine's own `~/.claude/settings.json` has `hooks` configured for `Stop, SessionStart, PostToolUse, PreToolUse, SubagentStop, PreCompact, FileChanged` — confirmed live event names on at least one supported host. Codex's equivalent hook surface was not checked this session; a Codex-side hook needs its own verification against Codex's actual plugin docs before shipping — don't assume symmetry with Claude's event names.

Two tiers, in preference order:

**Tier 1 — no compiled hook, use `hookify` (already installed on this machine, message-only, no new permission surface).**
A `.claude/hookify.suggest-checkpoint.local.md` rule: `event: bash`, pattern `git commit|git push`, `action: warn`, message pointing at `$checkpoint:save`. This covers the user's named triggers ("sau khi commit, sau khi push") directly, ships zero code, cannot block or write anything on its own, and is removable by deleting one file. Threat surface: a text nudge, nothing else.

**Tier 2 — native plugin hook, only if Tier 1 proves insufficient.**
If a reminder isn't enough and the ask is for the agent to actually reason and act, not just be nudged, the smallest justified pair is:

- **`Stop`** — before the agent ends a turn or session, check for uncommitted work or an open next-action with no recent checkpoint, and if so run the recommend-and-ask flow the `checkpoint` skill already specifies (*"If checkpointing was not explicitly requested, explain why it helps, propose a destination and ask before persistent writing"*). This is the one hook that maps onto a behavior the skill already promises but has no enforcement for today — nothing currently makes that instruction actually fire.
- **`PreCompact`** — the skill's own description already lists compaction as a trigger moment. A `PreCompact` hook is the only reliable way to guarantee that fires, since the agent has no way to reliably notice compaction is imminent from inside the conversation itself.

**Not recommended:** a native `PostToolUse` hook matching `git commit`/`git push` — Tier 1's `hookify` rule already covers this with less code and no new permission surface; don't duplicate it as a compiled hook unless `hookify` itself stops being a viable dependency.

**Do not implement:** any hook that writes the checkpoint file itself without asking. The skill's core safety property is "ask before persistent writing" unless explicitly invoked. A hook that auto-saves turns a suggestion mechanism into a silent side-effect and breaks that property.

### Trigger knobs — what's actually configurable at each tier

Verified directly against this machine's `~/.claude/settings.json`, not assumed:

- **Native `PostToolUse` matcher is tool-name-only** (e.g. `"matcher": "Bash|Edit|Write"`), not command-content. It cannot isolate "the bash command was `git commit`" by itself — a wired script would receive the full tool-call payload and would have to grep the command string itself for `git commit|git push`. This is strictly more code than Tier 1 for the same result.
- **`hookify`'s `bash` event matches directly on the `command` field** (`pattern` or `conditions` against `command`), which is exactly the git-subcommand distinction the user asked for, with no script to write. This is the concrete reason Tier 1 is preferred for the commit/push trigger specifically, not just a style preference.
- Neither `hookify` nor the native hook schema observed here has a built-in cooldown/debounce field. A rule fires every time its pattern matches — every commit, every push. For `hookify` (message-only, `action: warn`) that's cheap enough to leave as-is; the message is easy to ignore. For a Tier-2 `Stop`/`PreCompact` script, cooldown would have to be implemented in the script itself (e.g. compare `mtime` of the most recent checkpoint file to "now," skip the nudge if under N minutes) — this belongs in the hook script, not as a checkpoint-skill command flag.

Proposed flag, scoped to `save` only, for provenance rather than triggering:

- `/checkpoint:save [--trigger manual|post-commit|post-push|stop|pre-compact]` — defaults to `manual`. When a hook-injected reminder (`hookify` message or a Tier-2 `Stop`/`PreCompact` note) leads the agent to run `save`, it passes the matching value so the resulting checkpoint records *why* it exists (useful in `Decision/learning`, and later for tuning which triggers are actually worth keeping).

This is deliberately the only new flag tied to triggering. The trigger *condition* itself (which events fire, with what pattern) lives entirely in `hookify` rule frontmatter or the native hook script — not in checkpoint-skill's own command surface — so enabling/disabling/adjusting a trigger is "edit or delete one rule file," matching the plugin's existing no-new-commands, no-hidden-config posture.

One more piece of same-session evidence worth citing directly: this very conversation already carries a working precedent for the injected-reminder pattern — several turns above include a system-reminder along the lines of *"The task tools haven't been used recently... consider using TaskCreate"* fired by this host's own hook config. A `Stop`/`PreCompact` checkpoint nudge should copy that exact shape (inject a reminder for the agent to weigh, never auto-write), not invent a new mechanism.

## 6. Conciseness and language — compliance gap, not a missing instruction

Both asks map to instructions that already exist:

- Language-of-user: `save/SKILL.md:24-27`, `checkpoint/SKILL.md:39-42`.
- Anti-rambling: *"Keep it scannable in under one minute"* (`save/SKILL.md:40`) plus the fixed skeleton.

`scripts/checkpoint_contract.py` — the deterministic validator — checks required headings and profile-concept presence only. It has **no length or verbosity check at all**. That is the real gap: nothing measures the "under one minute" instruction, so a checkpoint with every heading present but rambling inside each one still passes `verify.py` and any CI gate today.

Proposed fix: add a soft ceiling to `checkpoint_contract.py` — flag, don't fail, when total word count exceeds roughly 350–400 words or any single section exceeds roughly 80 words — surfaced as a new `verbosity_warnings` field on `ValidationResult`. That gives "scannable in under one minute" something a benchmark run can actually catch, instead of depending on the model re-reading its own instruction correctly every time.

## Status

Approved and implemented. Section 5's hook shortlist now lives as the maintained doc at `docs/HOOKS.md`; section 4's role decision and section 1's scope resolution are specified in `plugins/checkpoint/skills/checkpoint/references/scope-and-role.md`. This file stays as the historical rationale record; edit the referenced files, not this one, for future behavior changes.
