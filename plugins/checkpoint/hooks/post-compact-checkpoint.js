#!/usr/bin/env node
// post-compact-checkpoint — SessionStart hook (matcher: compact)
//
// The reliable half of the pair (pre-compact-reminder.js is the other).
// Fires right as the new turn starts after compaction — this is the point
// where a real decision (offer to checkpoint, verify recovered state) can
// actually happen, unlike PreCompact which is too late to intervene.

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
