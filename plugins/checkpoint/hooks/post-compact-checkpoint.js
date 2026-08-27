#!/usr/bin/env node
// post-compact-checkpoint — SessionStart hook (matcher: compact)
//
// The reliable half of the pair (pre-compact-reminder.js is the other).
// Fires right as the new turn starts after compaction — this is the point
// where a real decision (offer to checkpoint, verify recovered state) can
// actually happen, unlike PreCompact which is too late to intervene.
//
// Per-project override: `.checkpoint/config.md` may set `hooks_enabled:
// false` to silence this hook entirely — see lib/read-project-config.js.
// Reading that config requires `cwd`, which only arrives via stdin, so this
// hook (unlike its original zero-stdin version) now waits on a stdin read
// first. That read fails toward "still emit" — an empty/unparseable/timed-
// out stdin must never suppress the reminder, since the whole point of this
// hook is to be the reliable half of the pair.

const { readStdinJson } = require('./lib/read-stdin-json.js');
const { readProjectConfig } = require('./lib/read-project-config.js');

// Must stay comfortably under this hook's own `timeout: 3` (3000ms) budget
// declared in hooks.json, leaving headroom for the write + process exit.
const STDIN_READ_TIMEOUT_MS = 2000;

readStdinJson((parsed, stdinFailed) => {
  if (!stdinFailed && !readProjectConfig(parsed.cwd).hooksEnabled) {
    process.exitCode = 0;
    return;
  }
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'SessionStart',
      additionalContext:
        'This session was just compacted. Before doing anything else: if the summary might ' +
        'have dropped load-bearing detail (open decisions, exact file states, pending ' +
        'approvals), run `$checkpoint:save --trigger pre-compact` NOW as your first action, ' +
        'don\'t just offer it — unless the pre-compaction work was trivial/completed with no ' +
        'follow-up, per the checkpoint skill\'s own gate.',
    },
  }));
  // exitCode (not exit()) so the process exits naturally once stdout has
  // actually flushed, instead of risking a truncated write under backpressure.
  process.exitCode = 0;
}, { timeoutMs: STDIN_READ_TIMEOUT_MS });
