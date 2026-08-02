# Research task state

Research question: does structured checkpointing reduce context reconstruction cost for multi-agent software work?

Sources checked: the local Checkpoint SOP, DORA 2025 AI-assisted software development report, Anthropic Economic Index September 2025 and OpenAI Harness Engineering. Verified claim: context curation and feedback loops affect agent effectiveness. Hypothesis, not yet verified: a canonical checkpoint reduces resume time below five minutes.

Citation state: all external claims have URLs in the working research note, but the DORA quotation was paraphrased and must not be presented as a direct quote.

Open question: which metric is least gameable—resume time, reconstructive questions or repeated tool calls? Next action: define the scoring rubric before collecting three trials.

Scope: compare checkpoint vs unstructured baseline on developer, research and operations work. Do not generalize to productivity or personality from three fixtures.

Done when: rubric is written, every claim is labelled verified/hypothesis and three trials have comparable observations.

Risk: same-session evaluation leaks context; cold-resume proof requires a fresh agent that sees only the checkpoint.
