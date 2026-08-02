# Reference implementations

Reviewed 2026-08-02.

## OpenAI Plugins

Source: https://github.com/openai/plugins and https://developers.openai.com/plugins/build/plugins

Adopted:

- marketplace root with `plugins/<name>/`;
- required `.codex-plugin/plugin.json`;
- semantic version, publisher metadata, skills path, interface metadata;
- local marketplace installation followed by a fresh-task test.

Not adopted:

- MCP, apps, hooks, icons, screenshots, privacy and terms links. The current skill does not need those surfaces.

## Anthropic Skills

Source: https://github.com/anthropics/skills

Adopted:

- self-contained skill folder;
- repository-level Claude marketplace;
- one source skill shared across hosts;
- strict host validation before release;
- explicit warning that examples do not replace environment-specific testing.

## Agent Skills specification

Source: https://agentskills.io/specification

Adopted:

- matching kebab-case folder and skill names;
- trigger-rich description;
- progressive disclosure through `SKILL.md`, `references/`, and `assets/`;
- relative, one-level resource references;
- runtime kept far below the 500-line recommendation.

## Superpowers

Source: https://github.com/obra/superpowers

Adopted:

- behavior-first tests with a no-skill/raw-state baseline;
- fresh isolated agents for forward tests;
- evidence-over-claims release gate;
- separate infrastructure validation from skill-behavior evaluation;
- cross-host compatibility as a release constraint.

Not adopted:

- session-start bootstrap and mandatory global workflow injection. Checkpoint should trigger only around real continuity risk.

## Repository decision

Use a hybrid:

1. Portable Agent Skill as the capability core.
2. Thin Codex and Claude manifests for host-native installation.
3. Deterministic tests for structure and distribution.
4. Fresh-agent fixtures for behavior.
5. Real multi-day use cases before claiming production proof.
