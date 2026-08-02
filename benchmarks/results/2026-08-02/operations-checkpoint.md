---
type: checkpoint
created: 2026-08-02
updated: 2026-08-02
status: active
profile: operations
project: "Local Ollama diagnosis"
branch: ""
owner: ""
---

# Checkpoint — Verify local Ollama is idle and record inventory

## Outcome

Confirm no Ollama model is loaded, memory pressure remains green, retained Steam and UTM data stays untouched, and record the current Ollama model inventory.

## Scope and boundaries
- Allowed: inspect Ollama model and process state; inspect the installed Ollama model inventory; stop an unexpectedly loaded model only after resolving its exact name.
- Do not: load or download a model; force swap purge; perform destructive cleanup; delete the Steam CrossOver bottle or UTM Windows VM; use broad kill commands.

## Current state

- Environment: macOS laptop with 32 GB RAM.
- Service under diagnosis: local Ollama.
- Model `qwen3.6` was removed after memory pressure.
- Memory pressure returned green after stopping the model.
- Swap remains 5.1 GB and should fall naturally.
- No model should be loaded during this task.
- Current Ollama process state and model inventory are not yet verified in this checkpoint.

## Last verified evidence
- Check/test/runtime: `ollama ps`, Activity Monitor inspection, and disk inventory were run before this checkpoint.
- Result: memory pressure returned green after the model stopped; swap remained 5.1 GB. Current process state and inventory remain unverified.

## Files, artifacts and processes
- Working directory: not provided.
- Environment: macOS laptop, 32 GB RAM.
- Service: local Ollama may remain installed.
- Model: `qwen3.6` removed after memory pressure.
- Running processes/sessions: unknown; must be checked before another download.
- Retained data: Steam CrossOver bottle and UTM Windows VM must remain untouched.

## Commands already run

- `ollama ps`
- Activity Monitor inspection
- Disk inventory

## Next action

1. Run `ollama ps`.
2. Run `ps -ax` filtered for Ollama.
3. If no model process exists, run `ollama list` without starting a model and record the inventory.

## Next safe diagnostic

Run `ollama ps`, then `ps -ax` filtered for Ollama. If no model process exists, inspect `ollama list` without starting a model.

## Blocker or risk

Closing the Ollama app does not prove the model process stopped. Verify process state before claiming success. No destructive cleanup is authorized.

## Risk boundary

- Do not start or download a model during diagnosis.
- Do not force swap cleanup.
- Do not use broad kill commands.
- Do not modify or delete retained Steam or UTM data.

## Rollback/recovery action

If a model is loaded unexpectedly, resolve its exact model name, then run `ollama stop <exact-model-name>`.

## Done when

- [ ] No model is loaded.
- [ ] Memory pressure is green.
- [ ] Steam CrossOver and UTM Windows VM data is untouched.
- [ ] Current Ollama model inventory is recorded.

## Open-loop lifecycle

- `park` — swap remains 5.1 GB; allow it to fall naturally and revisit only if memory pressure worsens.

## Resume command

```sh
ollama ps
ps -ax | grep '[O]llama'
ollama list
```
