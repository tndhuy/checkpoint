# Changelog

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
