# Benchmark protocol

## Goal

Measure whether a checkpoint lets a fresh agent resume with less reconstruction, fewer questions and fewer scope errors than an unstructured baseline.

## Procedure

1. Give a creator agent only one raw fixture and the checkpoint skill.
2. Save its checkpoint output without revealing expected terms.
3. Run `evaluate_checkpoint.py` against the private expectation file.
4. Give a fresh resume agent only the checkpoint and ask for current state, exact next action, boundaries and done gate.
5. Run the same resume prompt against the unstructured raw fixture as baseline.
6. Record missing facts, reconstructive questions, scope mistakes, time and evaluator score.

## Acceptance gate

- all required checkpoint sections present;
- all fixture-critical facts preserved;
- no invented evidence;
- resume agent identifies next action and safety boundary without source re-investigation;
- checkpoint case uses fewer reconstructive questions than baseline;
- developer, research and operations fixtures all pass.

Same-session tests validate structure and information preservation. Only a fresh-agent or later-session trial counts as cold-resume proof.
