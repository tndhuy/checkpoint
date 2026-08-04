# Changelog

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
