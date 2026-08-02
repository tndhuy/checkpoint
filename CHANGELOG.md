# Changelog

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
