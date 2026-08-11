---
type: checkpoint-config
scope: project
role: ""
updated: YYYY-MM-DD
---

Local project marker. Excluded from git via the sibling `.checkpoint/.gitignore` file (not the project's root `.gitignore`).

<!--
Global config (`<global_root>/config.md`) uses the same frontmatter shape plus
one extra field, `global_root`, and one table row per project:

---
type: checkpoint-config
global_root: "~/.checkpoint"
updated: YYYY-MM-DD
---

| Project path | Role |
|---|---|
| /absolute/path/to/repo-a | implementer |
| /absolute/path/to/repo-b | reviewer |
-->
