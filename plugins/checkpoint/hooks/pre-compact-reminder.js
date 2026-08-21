#!/usr/bin/env node
// pre-compact-reminder — PreCompact hook (matcher: manual|auto)
//
// Best-effort only: PreCompact fires once compaction is already underway.
// It cannot pause auto-compaction to let a skill run first, so this does
// not attempt to block (no `decision: "block"`) — it just leaves a plain-text
// marker in the transcript. The real, actionable reminder is
// post-compact-checkpoint.js on SessionStart(compact).

let input = '';
const stdinTimeout = setTimeout(() => finish('unknown'), 2000);
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => { input += chunk; });
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);
  let trigger = 'unknown';
  try {
    trigger = JSON.parse(input).trigger || 'unknown';
  } catch { /* ignore */ }
  finish(trigger);
});

function finish(trigger) {
  process.stdout.write(
    `Compaction is starting (trigger: ${trigger}). If there's unfinished work state worth ` +
    `preserving, run \`$checkpoint:save --trigger pre-compact\` before context is summarized away.`
  );
  process.exit(0);
}
