#!/usr/bin/env node
// pre-compact-reminder — PreCompact hook (matcher: manual|auto)
//
// Best-effort only: PreCompact fires once compaction is already underway.
// It cannot pause auto-compaction to let a skill run first, so this does
// not attempt to block (no `decision: "block"`) — it just leaves a plain-text
// marker in the transcript. The real, actionable reminder is
// post-compact-checkpoint.js on SessionStart(compact).

const { readStdinJson } = require('./lib/read-stdin-json.js');

// Must stay comfortably under this hook's own `timeout: 3` (3000ms) budget
// declared in hooks.json, leaving headroom for the write + process exit.
const STDIN_READ_TIMEOUT_MS = 2000;

readStdinJson((parsed, stdinFailed) => {
  const trigger = !stdinFailed && typeof parsed.trigger === 'string' ? parsed.trigger : 'unknown';
  process.stdout.write(
    `Compaction is starting (trigger: ${trigger}). If there's unfinished work state worth ` +
    `preserving, run \`$checkpoint:save --trigger pre-compact\` before context is summarized away.`
  );
  // exitCode (not exit()) so the process exits naturally once stdout has
  // actually flushed, instead of risking a truncated write under backpressure.
  process.exitCode = 0;
}, { timeoutMs: STDIN_READ_TIMEOUT_MS });
