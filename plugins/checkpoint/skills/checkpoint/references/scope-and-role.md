# Scope and role

Extends the canonical template. Resolve both once per project, then reuse — never re-ask or re-infer once a value is recorded.

## Scope

Two values: `project` (default) or `global`.

- `project` — the checkpoint lives inside the current repository. Keep using an existing project checkpoint/notes convention when one is already in use (unchanged from the base "Choose destination" order); otherwise fall back to `.checkpoint/` at the repository root.
- `global` — every project's checkpoints write into one root the user names once (for example `~/.checkpoint/`, or an existing personal notes vault). Nothing is written inside the project repository in this mode.

### Resolution order (on every `save`)

1. An explicit `--scope` flag on the invocation — use it, and persist it as the new default for this project (see "Recording the choice" below).
2. No flag, but a value is already recorded for this project — use it silently. Do not re-ask.
3. No flag and nothing recorded — first run for this project. **This never blocks writing the checkpoint.** `save` still renders and persists the checkpoint in this same response, using the default `scope: project` and `role: Unknown`, exactly as it would with no scope/role feature at all — the explicit-invocation "write it now" guarantee is never gated on this question. In the same response, after (or alongside) the checkpoint, ask exactly one question, in the user's language: *save checkpoints in this project, or in a global store? and what's your role on this work?* If the user has never chosen `global` before anywhere and picks it now, ask where the global root should live, offering `~/.checkpoint/` as a default. Persist the answer as the new default and, if it changes the destination or role, update the just-written checkpoint's frontmatter to match rather than leaving it stale.

### Recording the choice

- If `scope: project` — write `.checkpoint/config.md` at the project root using `assets/scope-config-template.md`. When `.checkpoint/` is created for the first time, also write `.checkpoint/.gitignore` containing a single `*` line so the directory self-excludes from git. Skip this write if `.checkpoint/.gitignore` already exists. Never touch or create the project's own root `.gitignore` for this purpose — the internal file is self-contained and needs no permission to add.
- If `scope: global` — write nothing inside the project. Instead add or update one entry for this project's absolute path inside the global config at `<global_root>/config.md` (same file that stores `global_root` itself). Checkpoints for this project are written under `<global_root>/<project-slug>/`.

## Role

Free text, not a closed set like `profile`. Describes who the user is relative to this work — for example "implementer", "reviewer", "status-checking PM" — and changes what the checkpoint assumes its reader already knows. It does not change which evidence fields are required; that is `profile`'s job (see `references/profiles.md`). The two are independent: the same `profile: developer` checkpoint reads differently for an implementer ("Next action: keep building X") than for a reviewer ("Next action: flag Y in review feedback").

Never infer role from context. Only read back a previously confirmed value.

### Resolution order (identical shape to scope)

1. An explicit `--role` flag — use it, persist as the new default for this project.
2. No flag, but a value is recorded for this project — use it silently.
3. No flag, nothing recorded — same non-blocking first-run exchange as scope: the checkpoint is still written now with `role: Unknown`, and the role question rides along in the same response. Persist the answer alongside `scope` in whichever config file scope resolution wrote (project-local `.checkpoint/config.md`, or the project's entry in the global config).

## Provenance: the `--trigger` flag

`save` also accepts `--trigger manual|post-commit|post-push|stop|pre-compact`, defaulting to `manual`. It does not select scope or role — it records *why* this save is happening, for the `Decision/learning` section and for later judging which automated triggers are worth keeping. See `docs/HOOKS.md` in the repository root for how automated triggers are wired (message-only reminders that lead an agent to invoke `save` with this flag — never a hook that writes a checkpoint by itself).
