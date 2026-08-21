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

let input = '';
const stdinTimeout = setTimeout(() => finish({}), 2000);
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => { input += chunk; });
process.stdin.on('end', () => {
  clearTimeout(stdinTimeout);
  let parsed = {};
  try { parsed = JSON.parse(input); } catch { /* ignore */ }
  finish(parsed);
});

function finish(parsed) {
  if (parsed.stop_hook_active) {
    process.exit(0);
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
  process.exit(0);
}
