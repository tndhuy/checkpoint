---
type: checkpoint-config
scope: project
role: ""
language: ""
updated: YYYY-MM-DD
---

Local project marker. Excluded from git via the sibling `.checkpoint/.gitignore` file (not the project's root `.gitignore`).

<!--
Optional Tier-2 hook settings (see `docs/HOOKS.md`) — not written by `save`,
add them by hand if you want non-default behavior. Both fail open to the
defaults shown below on any missing field, missing file, or malformed value:

---
type: checkpoint-config
scope: project
role: ""
language: ""                 # e.g. "vi" — once set, wins over the current request's language
updated: YYYY-MM-DD
hooks_enabled: true          # false silences all 3 Tier-2 hooks (Stop, PreCompact, SessionStart)
stop_cooldown_minutes: 20    # minutes between repeat Stop-hook blocks; 0 = never suppress
---

Global config (`<global_root>/config.md`) uses the same frontmatter shape plus
one extra field, `global_root`, and one table row per project:

---
type: checkpoint-config
global_root: "~/.checkpoint"
updated: YYYY-MM-DD
---

| Project path | Role | Language |
|---|---|---|
| /absolute/path/to/repo-a | implementer | vi |
| /absolute/path/to/repo-b | reviewer | |
-->
