# Host installation and behavior smoke test — 2026-08-02

## Scope

Verify package installation separately from skill behavior. Do not treat manifest validation, host discovery and workflow quality as the same claim.

## Package and installation

- Codex marketplace add: pass.
- Codex plugin install: pass, `checkpoint-skill@checkpoint-skill-local` version `0.1.0`, enabled.
- Claude marketplace add: pass.
- Claude plugin install: pass, `checkpoint-skill@checkpoint-skill` version `0.1.0`, user scope, enabled.
- OpenAI plugin validator: pass.
- OpenAI skill validator: pass.
- Claude strict marketplace and plugin validation: pass.
- Repository distribution validator: pass.
- Unit tests: 14/14 pass.

## Behavior

### Isolated source-controlled skill

A fresh ephemeral Codex process read the tracked `SKILL.md` and template, received a synthetic developer handoff, wrote no files and produced a canonical checkpoint.

Deterministic result: 19/19. No missing headings, profile concepts or expected facts.

### Installed-plugin discovery on the current Codex profile

The plugin is installed and enabled. A fresh CLI process received `$checkpoint`, but the host reported that its skill-context budget was exceeded and 160 additional skills were omitted. The process produced a semantic summary instead of loading the canonical skill contract.

Result: discovery test blocked by host-profile saturation. This is not counted as a behavior pass.

### Claude runtime

The plugin is installed, enabled and passes strict validation. A fresh no-tool runtime test could not start because the local Claude OAuth session was expired and could not refresh.

Result: runtime test blocked by host authentication. This is not counted as a behavior pass.

## Release decision

The repository is a real installable `0.1.0` package with deterministic distribution checks and a passing isolated behavior contract. Public release remains blocked until:

1. discovery passes in a clean Codex profile;
2. Claude authentication is restored and the no-tool runtime smoke test passes;
3. one multi-day real-project handoff is measured.
