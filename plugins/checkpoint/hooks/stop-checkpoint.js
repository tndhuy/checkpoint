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
//
// Cooldown: real-world use surfaced this blocking too often in a session
// with many short Stop events close together (e.g. one every reply, since
// several other host plugins also register Stop hooks and the two are easy
// to conflate). A lightweight cross-invocation cooldown (default 20 min,
// tracked in a tmp-dir marker file — no filesystem knowledge of where any
// checkpoint actually lives, deliberately dumb) skips repeat blocks within
// the window instead of nagging every single stop.
//
// Per-project override: `.checkpoint/config.md` may set `hooks_enabled:
// false` to silence this hook entirely, or `stop_cooldown_minutes: N` to
// change the cooldown window — see lib/read-project-config.js. Both fail
// open to the pre-existing defaults (enabled, 20 minutes) on any read or
// parse error.

const fs = require('fs');
const os = require('os');
const path = require('path');
const { readStdinJson } = require('./lib/read-stdin-json.js');
const { readProjectConfig } = require('./lib/read-project-config.js');

// Must stay comfortably under this hook's own `timeout: 3` (3000ms) budget
// declared in hooks.json, leaving headroom for the write + process exit.
const STDIN_READ_TIMEOUT_MS = 2000;

const COOLDOWN_FILE =
  process.env.CHECKPOINT_STOP_COOLDOWN_FILE || path.join(os.tmpdir(), 'checkpoint-skill-stop-cooldown.json');

function withinCooldown(cooldownMs) {
  try {
    const { lastBlockedAt } = JSON.parse(fs.readFileSync(COOLDOWN_FILE, 'utf8'));
    return typeof lastBlockedAt === 'number' && Date.now() - lastBlockedAt < cooldownMs;
  } catch {
    return false;
  }
}

function recordBlock() {
  try {
    fs.writeFileSync(COOLDOWN_FILE, JSON.stringify({ lastBlockedAt: Date.now() }));
  } catch {
    // best-effort — a failed write just means the next invocation won't see a cooldown
  }
}

readStdinJson((parsed, stdinFailed) => {
  const config = readProjectConfig(parsed.cwd);
  if (!config.hooksEnabled) {
    process.exitCode = 0;
    return;
  }
  const cooldownMs = config.stopCooldownMinutes * 60 * 1000;
  if (parsed.stop_hook_active || stdinFailed || withinCooldown(cooldownMs)) {
    process.exitCode = 0;
    return;
  }
  recordBlock();
  process.stdout.write(JSON.stringify({
    decision: 'block',
    reason:
      'Unsaved state? Run `$checkpoint:save --trigger stop` now (skip trivial Q&A, ' +
      'per the checkpoint skill\'s own gate).',
  }));
  // exitCode (not exit()) so the process exits naturally once stdout has
  // actually flushed, instead of risking a truncated write under backpressure.
  process.exitCode = 0;
}, { timeoutMs: STDIN_READ_TIMEOUT_MS });
