# Operations task state

Environment: macOS laptop, 32 GB RAM. Service under diagnosis: local Ollama. Model `qwen3.6` was removed after memory pressure; no model should be loaded during this task.

Observed metrics: memory pressure returned green after stopping the model; swap remains 5.1 GB and should fall naturally rather than forcing purge. Ollama service may remain installed, but model processes must be checked before another download.

Commands already run: `ollama ps`, Activity Monitor inspection and disk inventory. No destructive cleanup is authorized. Do not delete the Steam CrossOver bottle or UTM Windows VM.

Next safe diagnostic: run `ollama ps`, then `ps -ax` filtered for Ollama; if no model process exists, inspect `ollama list` without starting a model.

Recovery action: if a model is loaded unexpectedly, run `ollama stop <exact-model-name>` after resolving the exact name. Do not use broad kill commands.

Done when: no model is loaded, memory pressure is green, retained Steam/UTM data is untouched and current Ollama model inventory is recorded.

Risk: closing the Ollama app does not necessarily prove the model process stopped; verify process state before claiming success.
