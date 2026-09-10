# Checkpoint waypoint logging tier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a mechanical, no-LLM "waypoint" logging tier that pre-captures git-state facts on `Stop`/`PreCompact`, so `$checkpoint:save` can read them as evidence instead of re-deriving everything from scratch.

**Architecture:** A new async hook script (`waypoint-writer.js`) appends deduped git-state facts to a JSONL file under `~/.claude/checkpoint-skill/waypoints/<slug>.jsonl`, keyed by a slash-to-hyphen slug of the project's absolute path. It runs as a second, additive entry alongside the existing synchronous `stop-checkpoint.js`/`pre-compact-reminder.js` hooks — nothing existing is replaced. `save/SKILL.md` gains a step that reads unconsumed lines (tracked via a sibling `.consumed` line-count marker) and uses them only for mechanically-derivable checkpoint fields, never narrative ones.

**Tech Stack:** Node.js (hook script, CommonJS, no new dependencies — reuses `lib/read-stdin-json.js` and `lib/read-project-config.js`), Python `unittest` (tests), Markdown (`SKILL.md` prose, docs).

**Spec:** `docs/superpowers/specs/2026-09-11-checkpoint-waypoint-design.md`

## Global Constraints

- No new runtime dependencies (Node's built-in `child_process`, `fs`, `os`, `path` only).
- No new `allowed-tools` grant on `save` (stays `Read, Write, Edit` — the whole point of the slug/line-count design in the spec is to make this feature usable without `Bash`/`Glob`).
- Every hook script must fail open: any error (missing git repo, unwritable directory, malformed stdin) is swallowed silently, never surfaces an error to the user, never blocks the turn.
- No hook may write, modify, or delete a checkpoint file. `waypoint-writer.js` only ever touches its own `.jsonl`/`.consumed` files.
- `hooks_enabled: false` in `.checkpoint/config.md` must silence `waypoint-writer.js` exactly like it silences the other three Tier-2 hooks.
- Version bump goes across all 4 tracked manifests together: `plugins/checkpoint/.claude-plugin/plugin.json`, `plugins/checkpoint/.codex-plugin/plugin.json`, `pyproject.toml`, `.claude-plugin/marketplace.json`. Current version: `0.1.20` → this feature ships as `0.1.21`.
- Full verification before the final commit: `python3 -m unittest discover -s tests -v`, `python3 scripts/verify.py`, `claude plugin validate --strict .` and `--strict plugins/checkpoint`.

---

### Task 1: `waypoint-writer.js` hook script

**Files:**
- Create: `plugins/checkpoint/hooks/waypoint-writer.js`
- Test: `tests/test_hooks_runtime.py` (new `WaypointWriterTests` class, appended to the existing file)

**Interfaces:**
- Consumes: `readStdinJson(onDone, opts)` from `./lib/read-stdin-json.js` — `onDone(parsed, stdinFailed)`, `parsed.cwd: string`. `readProjectConfig(cwd)` from `./lib/read-project-config.js` — returns `{ hooksEnabled: boolean, stopCooldownMinutes: number }`.
- Produces: a file at `<WAYPOINTS_DIR>/<slug>.jsonl` where `<slug>` is `cwd` with every `/` replaced by `-`, one JSON object per line: `{timestamp, cwd, branch, headSha, headMessage, statusShort}`. `WAYPOINTS_DIR` defaults to `path.join(os.homedir(), '.claude', 'checkpoint-skill', 'waypoints')`, overridable via `CHECKPOINT_WAYPOINTS_DIR` env var (test isolation, mirrors `CHECKPOINT_STOP_COOLDOWN_FILE`/`CHECKPOINT_CONFIG_FILE` in the existing hooks).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_hooks_runtime.py` (after the existing `PostCompactCheckpointTests` class, before the `if __name__ == "__main__":` block):

```python
class WaypointWriterTests(unittest.TestCase):
    def setUp(self):
        self._waypoints_dir = tempfile.TemporaryDirectory()
        self.waypoints_dir = self._waypoints_dir.name
        self._repo_dir = tempfile.TemporaryDirectory()
        self.repo_dir = self._repo_dir.name
        subprocess.run(["git", "init", "-q", "-b", "main", self.repo_dir], check=True)
        subprocess.run(["git", "-C", self.repo_dir, "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", self.repo_dir, "config", "user.name", "Test"], check=True)
        (Path(self.repo_dir) / "file.txt").write_text("hello")
        subprocess.run(["git", "-C", self.repo_dir, "add", "file.txt"], check=True)
        subprocess.run(["git", "-C", self.repo_dir, "commit", "-q", "-m", "init"], check=True)

    def tearDown(self):
        self._waypoints_dir.cleanup()
        self._repo_dir.cleanup()

    def slug(self) -> str:
        return self.repo_dir.replace("/", "-")

    def waypoint_file(self) -> Path:
        return Path(self.waypoints_dir) / f"{self.slug()}.jsonl"

    def run_waypoint(self, stdin: str, config_file: str | None = None) -> subprocess.CompletedProcess:
        env = {"CHECKPOINT_WAYPOINTS_DIR": self.waypoints_dir}
        if config_file is not None:
            env["CHECKPOINT_CONFIG_FILE"] = config_file
        return run_hook("waypoint-writer.js", stdin, env=env)

    def test_writes_one_line_for_clean_repo(self):
        result = self.run_waypoint(json.dumps({"cwd": self.repo_dir}))
        self.assertEqual(result.returncode, 0)
        lines = self.waypoint_file().read_text().strip().splitlines()
        self.assertEqual(len(lines), 1)
        entry = json.loads(lines[0])
        self.assertEqual(entry["cwd"], self.repo_dir)
        self.assertEqual(entry["branch"], "main")
        self.assertIn("headSha", entry)
        self.assertEqual(entry["statusShort"], "")

    def test_dedupes_identical_state(self):
        self.run_waypoint(json.dumps({"cwd": self.repo_dir}))
        self.run_waypoint(json.dumps({"cwd": self.repo_dir}))
        lines = self.waypoint_file().read_text().strip().splitlines()
        self.assertEqual(len(lines), 1, "identical git state must not be logged twice")

    def test_logs_again_after_new_commit(self):
        self.run_waypoint(json.dumps({"cwd": self.repo_dir}))
        (Path(self.repo_dir) / "file.txt").write_text("changed")
        subprocess.run(["git", "-C", self.repo_dir, "commit", "-aqm", "second"], check=True)
        self.run_waypoint(json.dumps({"cwd": self.repo_dir}))
        lines = self.waypoint_file().read_text().strip().splitlines()
        self.assertEqual(len(lines), 2)

    def test_logs_again_after_branch_change_at_same_commit(self):
        self.run_waypoint(json.dumps({"cwd": self.repo_dir}))
        subprocess.run(["git", "-C", self.repo_dir, "checkout", "-qb", "other"], check=True)
        self.run_waypoint(json.dumps({"cwd": self.repo_dir}))
        lines = self.waypoint_file().read_text().strip().splitlines()
        self.assertEqual(len(lines), 2)

    def test_hooks_enabled_false_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            config_file = str(Path(d) / "config.md")
            Path(config_file).write_text("---\nhooks_enabled: false\n---\n")
            result = self.run_waypoint(json.dumps({"cwd": self.repo_dir}), config_file=config_file)
            self.assertEqual(result.returncode, 0)
            self.assertFalse(self.waypoint_file().exists())

    def test_silent_on_non_git_directory(self):
        with tempfile.TemporaryDirectory() as d:
            result = self.run_waypoint(json.dumps({"cwd": d}))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_silent_on_empty_stdin(self):
        result = self.run_waypoint("")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(list(Path(self.waypoints_dir).iterdir()), [])

    def test_silent_on_malformed_stdin(self):
        result = self.run_waypoint("{not valid json")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_silent_when_cwd_missing(self):
        result = self.run_waypoint(json.dumps({"stop_hook_active": True}))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(list(Path(self.waypoints_dir).iterdir()), [])

    def test_silent_when_waypoints_dir_unwritable(self):
        parent = Path(self.waypoints_dir)
        parent.chmod(0o500)  # read + execute, no write
        try:
            result = self.run_waypoint(json.dumps({"cwd": self.repo_dir}))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
        finally:
            parent.chmod(0o700)  # restore so tearDown's cleanup() can delete it
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_hooks_runtime.WaypointWriterTests -v`
Expected: every test errors with something like `FileNotFoundError` / non-zero exit, since `waypoint-writer.js` doesn't exist yet.

- [ ] **Step 3: Write the implementation**

Create `plugins/checkpoint/hooks/waypoint-writer.js`:

```js
#!/usr/bin/env node
// waypoint-writer — Stop/PreCompact hook (async, additive to the existing
// synchronous stop-checkpoint.js / pre-compact-reminder.js entries — see
// docs/HOOKS.md's "Waypoint capture" subsection).
//
// Purely mechanical: appends {timestamp, cwd, branch, headSha, headMessage,
// statusShort} — read straight from local git output, no LLM, no judgment —
// to an append-only JSONL log that `save` later reads as evidence. Never
// writes a checkpoint file itself; this is a different file in a different
// location, consumed only as optional input to `save`'s own writes.
//
// Stored outside the project tree (under the user's home directory, not the
// OS tmp directory) specifically so `save` — which only has Read/Write/Edit,
// no Bash, no Glob — can compute the exact path itself: replace every `/` in
// its own absolute project path with `-` (same convention Claude Code uses
// for `~/.claude/projects/<slug>/`) and read `<dir>/<slug>.jsonl` directly.
// A SHA-256 hash was considered and rejected: an LLM restricted to
// Read/Write/Edit cannot compute one reliably, only a script can.
//
// Fail-open in every direction: a missing git repo, an unwritable target
// directory, a missing git binary, or a stdin read failure all result in a
// silent no-op, never a visible error, never a blocked Stop/PreCompact.

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');
const { readStdinJson } = require('./lib/read-stdin-json.js');
const { readProjectConfig } = require('./lib/read-project-config.js');

// Generous relative to the sync hooks' `timeout: 3` — this one is declared
// `async: true` in hooks.json, so it never blocks a turn, but still shouldn't
// hang indefinitely on a slow stdin write from the host.
const STDIN_READ_TIMEOUT_MS = 2000;

const WAYPOINTS_DIR =
  process.env.CHECKPOINT_WAYPOINTS_DIR ||
  path.join(os.homedir(), '.claude', 'checkpoint-skill', 'waypoints');

function slugify(absPath) {
  return absPath.replace(/\//g, '-');
}

function runGit(args, cwd) {
  return execFileSync('git', args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
}

function readLastEntry(jsonlPath) {
  try {
    const lines = fs.readFileSync(jsonlPath, 'utf8').split('\n').filter(Boolean);
    return lines.length ? JSON.parse(lines[lines.length - 1]) : null;
  } catch {
    // Missing file, unreadable, or a corrupt last line — treat as "no prior
    // entry" so a single bad line can never permanently block future writes.
    return null;
  }
}

readStdinJson((parsed, stdinFailed) => {
  try {
    if (stdinFailed || !parsed.cwd) {
      process.exitCode = 0;
      return;
    }
    const cwd = parsed.cwd;
    if (!readProjectConfig(cwd).hooksEnabled) {
      process.exitCode = 0;
      return;
    }

    const headSha = runGit(['rev-parse', 'HEAD'], cwd);
    const branch = runGit(['branch', '--show-current'], cwd);
    const headMessage = runGit(['log', '-1', '--format=%s'], cwd);
    const statusShort = runGit(['status', '--porcelain'], cwd);

    const jsonlPath = path.join(WAYPOINTS_DIR, `${slugify(cwd)}.jsonl`);
    const previous = readLastEntry(jsonlPath);
    const isDuplicate =
      previous &&
      previous.headSha === headSha &&
      previous.branch === branch &&
      previous.statusShort === statusShort;

    if (!isDuplicate) {
      fs.mkdirSync(WAYPOINTS_DIR, { recursive: true });
      const entry = { timestamp: new Date().toISOString(), cwd, branch, headSha, headMessage, statusShort };
      fs.appendFileSync(jsonlPath, JSON.stringify(entry) + '\n');
    }
  } catch {
    // fail-open — see header comment
  }
  process.exitCode = 0;
}, { timeoutMs: STDIN_READ_TIMEOUT_MS });
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_hooks_runtime.WaypointWriterTests -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/checkpoint/hooks/waypoint-writer.js tests/test_hooks_runtime.py
git commit -m "feat(checkpoint): add mechanical waypoint-writer hook"
```

---

### Task 2: Register `waypoint-writer.js` in `hooks.json`

**Files:**
- Modify: `plugins/checkpoint/hooks/hooks.json`
- Test: `tests/test_hooks_runtime.py` (new `HooksRegistrationTests` class)

**Interfaces:**
- Consumes: `plugins/checkpoint/hooks/waypoint-writer.js` from Task 1 (must already exist — `test_distribution.py::test_shipped_hooks_manifest_is_valid` fails otherwise, since `validate_hooks` checks every referenced script exists).
- Produces: two new hook-group entries, one under `hooks.Stop`, one under `hooks.PreCompact`, each with a single command entry carrying `"async": true`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_hooks_runtime.py`, after the `WaypointWriterTests` class from Task 1 and before the `if __name__ == "__main__":` block:

```python
class HooksRegistrationTests(unittest.TestCase):
    def test_waypoint_writer_registered_additively_as_async(self):
        hooks_json = json.loads((HOOKS / "hooks.json").read_text())
        expectations = {"Stop": "stop-checkpoint.js", "PreCompact": "pre-compact-reminder.js"}
        for event, existing_script in expectations.items():
            groups = hooks_json["hooks"][event]
            commands = [h["command"] for group in groups for h in group["hooks"]]
            self.assertTrue(
                any("waypoint-writer.js" in c for c in commands), f"{event} is missing waypoint-writer.js"
            )
            self.assertTrue(
                any(existing_script in c for c in commands), f"{event} lost its existing hook {existing_script}"
            )
            for group in groups:
                for h in group["hooks"]:
                    if "waypoint-writer.js" in h["command"]:
                        self.assertIs(h.get("async"), True, "waypoint-writer.js must be registered async")
                    else:
                        self.assertNotIn("async", h, f"{existing_script} must stay synchronous")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_hooks_runtime.HooksRegistrationTests -v`
Expected: FAIL — `waypoint-writer.js` not present in `Stop`/`PreCompact` yet.

- [ ] **Step 3: Edit `hooks.json`**

Replace the full contents of `plugins/checkpoint/hooks/hooks.json`:

```json
{
  "description": "Checkpoint auto-triggers (Tier 2, see docs/HOOKS.md). Message-only reminders around Stop and compaction that lead to an explicit $checkpoint:save invocation, plus a mechanical async waypoint-capture hook (git-state facts only) — neither ever writes a checkpoint file on their own.",
  "hooks": {
    "PreCompact": [
      {
        "matcher": "manual|auto",
        "hooks": [
          {
            "type": "command",
            "command": "node \"${CLAUDE_PLUGIN_ROOT}/hooks/pre-compact-reminder.js\"",
            "timeout": 3
          }
        ]
      },
      {
        "matcher": "manual|auto",
        "hooks": [
          {
            "type": "command",
            "command": "node \"${CLAUDE_PLUGIN_ROOT}/hooks/waypoint-writer.js\"",
            "timeout": 15,
            "async": true
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [
          {
            "type": "command",
            "command": "node \"${CLAUDE_PLUGIN_ROOT}/hooks/post-compact-checkpoint.js\"",
            "timeout": 3
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node \"${CLAUDE_PLUGIN_ROOT}/hooks/stop-checkpoint.js\"",
            "timeout": 3
          }
        ]
      },
      {
        "hooks": [
          {
            "type": "command",
            "command": "node \"${CLAUDE_PLUGIN_ROOT}/hooks/waypoint-writer.js\"",
            "timeout": 15,
            "async": true
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_hooks_runtime.HooksRegistrationTests tests.test_distribution -v`
Expected: all PASS (the second module covers `test_shipped_hooks_manifest_is_valid`, confirming the new entries are still well-formed — quoted path, `${CLAUDE_PLUGIN_ROOT}`, no trailing shell content, referenced file exists).

- [ ] **Step 5: Commit**

```bash
git add plugins/checkpoint/hooks/hooks.json tests/test_hooks_runtime.py
git commit -m "feat(checkpoint): register waypoint-writer as an additive async hook"
```

---

### Task 3: Document the threat review and fix the stale hook count in `docs/HOOKS.md`

**Files:**
- Modify: `docs/HOOKS.md`

**Interfaces:**
- Consumes: the finished behavior of `waypoint-writer.js` from Tasks 1–2 (this task documents what already exists; no code changes).
- Produces: nothing consumed by later tasks — purely documentation, verified by manual review (this repo does not unit-test doc prose, consistent with how `hooks_enabled`/`stop_cooldown_minutes` were documented in 0.1.16 without a dedicated test).

- [ ] **Step 1: Add the "Waypoint capture" subsection**

In `docs/HOOKS.md`, immediately after the existing line `**Not recommended:** a native \`PostToolUse\` hook duplicating the commit/push match Tier 1 already covers with less code.` (and before the `## Per-project settings` heading that follows it), insert:

```markdown

## Waypoint capture (mechanical, async, additive)

As of 0.1.21, a third Tier-2 script, `waypoint-writer.js`, is registered as a *second, independent* entry under both `Stop` and `PreCompact` — alongside, not replacing, `stop-checkpoint.js` and `pre-compact-reminder.js`. Unlike those two, it never surfaces a message: it silently appends `{timestamp, cwd, branch, headSha, headMessage, statusShort}` — read straight from local `git` output, no LLM, no judgment — to `~/.claude/checkpoint-skill/waypoints/<slug>.jsonl` (`<slug>` = the project's absolute path with every `/` replaced by `-`). `save` later reads this file as optional evidence for the mechanically-derivable parts of a checkpoint; see `skills/save/SKILL.md`'s "Waypoint evidence" section and `docs/superpowers/specs/2026-09-11-checkpoint-waypoint-design.md` for the full design.

**Threat review** (per this file's own opening bar — "documented need and threat review" for any autonomous write):

- **What is written:** exactly the six mechanical fields above, sourced from local `git` command output only. No user input, no LLM output, and no conversational content ever reaches this file.
- **Where it is written:** `~/.claude/checkpoint-skill/waypoints/` only — never inside the project tree, under either `scope`. The hook never resolves `scope`/`role` at all, sidestepping the `scope: global` "write nothing inside the project" invariant entirely rather than special-casing it.
- **What it cannot do:** write, modify, or delete a checkpoint file. It writes to a different file in a different location that `save` treats as optional evidence, never as an alternative destination.
- **Failure mode:** fail-open. A failed or missing waypoint write degrades `save` to exactly its pre-0.1.21 behavior — `save` already handles "no waypoints found" as its default path.
- **Kill switch:** `hooks_enabled: false` disables it exactly like the other three Tier-2 hooks (same shared `lib/read-project-config.js` check) — no separate, harder-to-discover toggle.

Deduping compares `headSha` + `branch` + `statusShort` against the log's last line, so repeated `Stop` fires with no intervening change never grow the file — this also catches a checkout to a different branch pointing at the same commit. The file is strictly append-only; `save` tracks its own read progress in a sibling `.consumed` marker (a plain line count) rather than mutating the log.
```

- [ ] **Step 2: Fix the stale hook count in "Per-project settings"**

Find this existing bullet in `docs/HOOKS.md`:

```markdown
- `hooks_enabled: true|false` — `false` silences all three Tier-2 hooks (`Stop`, `PreCompact`, `SessionStart`) for this project. Default `true`.
```

Replace with:

```markdown
- `hooks_enabled: true|false` — `false` silences all Tier-2 hooks for this project: `stop-checkpoint.js` (`Stop`), `pre-compact-reminder.js` (`PreCompact`), `post-compact-checkpoint.js` (`SessionStart`), and `waypoint-writer.js` (`Stop`/`PreCompact`). Default `true`.
```

- [ ] **Step 3: Commit**

```bash
git add docs/HOOKS.md
git commit -m "docs(checkpoint): document waypoint-writer threat review, fix stale hook count"
```

---

### Task 4: `save` skill reads waypoint evidence

**Files:**
- Modify: `plugins/checkpoint/skills/save/SKILL.md`
- Test: `tests/test_skill_instruction.py` (new tests appended)

**Interfaces:**
- Consumes: the `~/.claude/checkpoint-skill/waypoints/<slug>.jsonl` / `.consumed` file pair Task 1's hook produces (read-only from `save`'s side — `save` never invokes the hook script directly, it independently recomputes the same `<slug>`).
- Produces: nothing consumed by later tasks — this is the terminal consumer described in the spec.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_skill_instruction.py` (inside `SkillInstructionTests`, anywhere after `test_update_section_forbids_full_section_rewrites`):

```python
    def test_save_skill_documents_waypoint_evidence_step(self):
        content = (SKILLS / "save" / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(content.split())
        self.assertIn("checkpoint-skill/waypoints", normalized)
        self.assertIn(".consumed", normalized)
        self.assertIn("never for", normalized)
        self.assertIn("Never truncate or delete", content)

    def test_save_skill_waypoint_slug_matches_hook_convention(self):
        content = (SKILLS / "save" / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(content.split())
        self.assertIn("replace every `/` with `-`", normalized)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_skill_instruction.SkillInstructionTests.test_save_skill_documents_waypoint_evidence_step tests.test_skill_instruction.SkillInstructionTests.test_save_skill_waypoint_slug_matches_hook_convention -v`
Expected: both FAIL — `save/SKILL.md` doesn't mention waypoints yet.

- [ ] **Step 3: Edit `save/SKILL.md`**

In `plugins/checkpoint/skills/save/SKILL.md`, insert a new section immediately after `## Scope, role, and trigger flags` and before `## Profile and evidence`:

```markdown
## Waypoint evidence

Before gathering evidence, check for mechanically-captured waypoints: take this project's absolute path, replace every `/` with `-` to get `<slug>`, and `Read` `~/.claude/checkpoint-skill/waypoints/<slug>.jsonl`. If it doesn't exist, skip this step entirely and proceed exactly as before this feature existed.

If it exists, also `Read` the sibling `~/.claude/checkpoint-skill/waypoints/<slug>.consumed` (treat a missing or unparseable value as `0`) and skip that many lines from the top of the `.jsonl`. Use only the remaining lines, and only for facts this skill already treats as mechanical — `Working directory`, `Branch`, `Changed files` — never for `Outcome`, `Decision/learning`, or any section requiring judgment; conversational context always wins over a stale waypoint line for those.

After the checkpoint file is written, `Write` the `.consumed` marker with the `.jsonl`'s total line count at the time it was read. Never truncate or delete the `.jsonl` itself — it stays append-only; only the marker moves.
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_skill_instruction -v`
Expected: all PASS, including the two new tests and every pre-existing test in the file (confirms the insertion didn't disturb any other cross-reference assertion).

- [ ] **Step 5: Commit**

```bash
git add plugins/checkpoint/skills/save/SKILL.md tests/test_skill_instruction.py
git commit -m "feat(checkpoint): save reads waypoint evidence for mechanical fields"
```

---

### Task 5: Version bump, changelog, full verification

**Files:**
- Modify: `plugins/checkpoint/.claude-plugin/plugin.json`
- Modify: `plugins/checkpoint/.codex-plugin/plugin.json`
- Modify: `pyproject.toml`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: nothing new — this task packages the finished feature from Tasks 1–4.
- Produces: the shipped `0.1.21` release.

- [ ] **Step 1: Bump version in all 4 manifests**

In `plugins/checkpoint/.claude-plugin/plugin.json`, `plugins/checkpoint/.codex-plugin/plugin.json`: change `"version": "0.1.20"` to `"version": "0.1.21"`.

In `pyproject.toml`: change `version = "0.1.20"` to `version = "0.1.21"`.

In `.claude-plugin/marketplace.json`: change `"version": "0.1.20"` to `"version": "0.1.21"`.

- [ ] **Step 2: Add the CHANGELOG entry**

At the top of `CHANGELOG.md`, immediately after the `# Changelog` heading and before the existing `## [0.1.20] - 2026-09-10` entry, insert:

```markdown
## [0.1.21] - 2026-09-11

### Added
- New mechanical, no-LLM "waypoint" logging tier: `hooks/waypoint-writer.js` registered as a second, independent, `"async": true` entry under both `Stop` and `PreCompact` — alongside, not replacing, the existing synchronous `stop-checkpoint.js`/`pre-compact-reminder.js`. On fire it appends `{timestamp, cwd, branch, headSha, headMessage, statusShort}` (deduped against the log's last line) to `~/.claude/checkpoint-skill/waypoints/<slug>.jsonl`, where `<slug>` is the project's absolute path with every `/` replaced by `-` — the same convention Claude Code itself uses for `~/.claude/projects/<slug>/`. Stored under the user's home directory rather than the OS tmp directory, and keyed by a plain slug rather than a hash, specifically so `save` (`allowed-tools: Read, Write, Edit` — no `Bash`, no `Glob`) can compute the exact path itself with no new tool grant. `save/SKILL.md` gained a "Waypoint evidence" step: it reads unconsumed lines (tracked via a sibling `.consumed` line-count marker, never a byte offset) and uses them only for the mechanically-derivable parts of a checkpoint (`Working directory`, `Branch`, `Changed files`), never for `Outcome`/`Decision/learning`/anything requiring judgment. Respects `hooks_enabled: false` via the existing `lib/read-project-config.js` check; fails open on any error (no git repo, unwritable target, malformed stdin). No benefit to an in-session manual `save` — the payoff is specifically post-compact, fresh-session, and `recall`, where conversational context is already gone. Full design: `docs/superpowers/specs/2026-09-11-checkpoint-waypoint-design.md`.

### Changed
- `docs/HOOKS.md`'s "Per-project settings" section updated: `hooks_enabled: false` now correctly documents silencing four Tier-2 hooks, not three.

### Verified
- New `WaypointWriterTests` and `HooksRegistrationTests` (`tests/test_hooks_runtime.py`), new waypoint-evidence tests (`tests/test_skill_instruction.py`) — full suite passes.
- `python3 scripts/verify.py` and `claude plugin validate --strict .` / `--strict plugins/checkpoint` pass.
```

- [ ] **Step 3: Run full verification**

Run, in order:
```bash
python3 -m unittest discover -s tests -v
python3 scripts/verify.py
claude plugin validate --strict .
claude plugin validate --strict plugins/checkpoint
```
Expected: every command exits 0 / prints PASS, with no failing test.

- [ ] **Step 4: Commit**

```bash
git add plugins/checkpoint/.claude-plugin/plugin.json plugins/checkpoint/.codex-plugin/plugin.json pyproject.toml .claude-plugin/marketplace.json CHANGELOG.md
git commit -m "chore(checkpoint): release 0.1.21 — waypoint logging tier"
```

- [ ] **Step 5: Refresh the locally-installed plugin**

The marketplace source is a local directory pointing at this repo, so `claude plugin marketplace update` alone does not pick up the new version (established in the 0.1.19/0.1.20 releases). Force a reinstall:
```bash
claude plugin uninstall checkpoint@checkpoint-skill
claude plugin install checkpoint@checkpoint-skill
```
Confirm `~/.claude/plugins/installed_plugins.json`'s `gitCommitSha` for `checkpoint@checkpoint-skill` matches the new commit from Step 4.

- [ ] **Step 6: Fresh-agent forward-test (mandatory — this repo's 2026-08-07 precedent requires live verification for any `SKILL.md` instruction change, not just static content assertions)**

In a scratch git repository (not this one):
1. Make an initial commit, then send a `Stop` event to `waypoint-writer.js` (or simply let a real Claude Code session in that repo idle to a natural `Stop`) and confirm `~/.claude/checkpoint-skill/waypoints/<slug>.jsonl` now has one line, where `<slug>` is that scratch repo's absolute path with `/` replaced by `-`.
2. Make a second commit, trigger `Stop` again, and confirm the file now has two distinct lines (different `headSha`).
3. Run `$checkpoint:save` in that session and confirm the resulting checkpoint's `Branch`/`Changed files`/`Working directory` fields match the waypoint evidence, and that `~/.claude/checkpoint-skill/waypoints/<slug>.consumed` now reads `2`.
4. Run `$checkpoint:save` again with no new commits in between, and confirm it completes normally (falls back to direct git inspection for anything not covered by the now-fully-consumed waypoint log) without erroring or re-reading already-consumed lines.

Record the outcome in this release's `CHANGELOG.md` entry's `### Verified` section (append a line — this is a live-agent behavioral check, distinct from the static/unit tests already listed there).
