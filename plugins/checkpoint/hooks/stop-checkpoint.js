#!/usr/bin/env node
// stop-checkpoint — Stop hook
//
// Forces (not nudges) a checkpoint pass before the session is allowed to
// actually end. Stop hooks CAN block (unlike PreCompact), so this uses that:
// on a normal stop it blocks once with a reason, which makes Claude take one
// more turn; `stop_hook_active` (set by Claude Code on that forced turn) is
// checked so the block never fires twice and can't loop.
//
// The forced turn still carries the checkpoint skill's own triviality gate
// in the reason text ("skip trivial completed Q&A") — automatic here means
// enforced-if-warranted, not an unconditional checkpoint on every session.
//
// Fail-safe direction: an empty/unparseable stdin, or the read timing out,
// is treated the SAME as `stop_hook_active: true` (i.e. don't block) rather
// than the same as "no signal, block anyway". A failure to read the one
// field that prevents re-blocking must never itself cause a block — that
// would fail exactly on the path the guard exists to prevent.

const { readStdinJson } = require('./lib/read-stdin-json.js');

// Must stay comfortably under this hook's own `timeout: 3` (3000ms) budget
// declared in hooks.json, leaving headroom for the write + process exit.
const STDIN_READ_TIMEOUT_MS = 2000;

readStdinJson((parsed, stdinFailed) => {
  if (parsed.stop_hook_active || stdinFailed) {
    process.exitCode = 0;
    return;
  }
  process.stdout.write(JSON.stringify({
    decision: 'block',
    reason:
      'Before actually ending this session: if there is unfinished/reconstructable state ' +
      '(open decisions, exact file states, pending approvals — reconstruction would take a ' +
      'human more than 5 minutes), run `$checkpoint:save --trigger stop` now. Skip it for ' +
      'trivial completed Q&A with no follow-up, per the checkpoint skill\'s own gate. Then stop.',
  }));
  // exitCode (not exit()) so the process exits naturally once stdout has
  // actually flushed, instead of risking a truncated write under backpressure.
  process.exitCode = 0;
}, { timeoutMs: STDIN_READ_TIMEOUT_MS });
