# Changelog

## [Unreleased]

### Added
- Standalone repository structure and local discovery symlink contract.
- Generic, developer, research and operations checkpoint profiles.
- Deterministic checkpoint contract and cold-resume evaluators.
- Ten regression tests covering structure, formatting tolerance, profile concepts, fact preservation and baseline comparison.
- Three isolated-agent fixture scenarios with dated creator, resume and baseline artifacts.
- Benchmark report for 2026-08-02.

### Changed
- Global checkpoint discovery path now resolves to the maintained runtime in this repository.
- Evaluators distinguish facts that must survive checkpoint creation from concepts needed for immediate resume.

### Verified
- Official skill-creator validator passes.
- Contract scores: developer 19/19, research 18/18, operations 20/20.
- Cold-resume reconstructive questions: 5 total versus 14 from raw-state baselines.
