#!/usr/bin/env node
// waypoint-writer — Stop/PreCompact hook (async, additive to the existing
// synchronous stop-checkpoint.js / pre-compact-reminder.js entries — see
// docs/HOOKS.md's "Waypoint capture" subsection).
//
// Purely mechanical: appends {timestamp, cwd, branch, headSha, headMessage,
// statusShort} — read straight from local git output, no LLM, no judgment —
// to an append-only JSONL log that `save` later reads as evidence. Never
// writes a checkpoint file itself; this is a different file in a different
// location, consumed only as optional input to `save`'s own writes.
//
// Stored outside the project tree (under the user's home directory, not the
// OS tmp directory) specifically so `save` — which only has Read/Write/Edit,
// no Bash, no Glob — can compute the exact path itself: replace every `/` in
// its own absolute project path with `-` (same convention Claude Code uses
// for `~/.claude/projects/<slug>/`) and read `<dir>/<slug>.jsonl` directly.
// A SHA-256 hash was considered and rejected: an LLM restricted to
// Read/Write/Edit cannot compute one reliably, only a script can.
//
// Fail-open in every direction: a missing git repo, an unwritable target
// directory, a missing git binary, or a stdin read failure all result in a
// silent no-op, never a visible error, never a blocked Stop/PreCompact.

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');
const { readStdinJson } = require('./lib/read-stdin-json.js');
const { readProjectConfig } = require('./lib/read-project-config.js');

// Generous relative to the sync hooks' `timeout: 3` — this one is declared
// `async: true` in hooks.json, so it never blocks a turn, but still shouldn't
// hang indefinitely on a slow stdin write from the host.
const STDIN_READ_TIMEOUT_MS = 2000;

const WAYPOINTS_DIR =
  process.env.CHECKPOINT_WAYPOINTS_DIR ||
  path.join(os.homedir(), '.claude', 'checkpoint-skill', 'waypoints');

function slugify(absPath) {
  return absPath.replace(/\//g, '-');
}

function runGit(args, cwd) {
  return execFileSync('git', args, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
}

function readLastEntry(jsonlPath) {
  try {
    const lines = fs.readFileSync(jsonlPath, 'utf8').split('\n').filter(Boolean);
    return lines.length ? JSON.parse(lines[lines.length - 1]) : null;
  } catch {
    // Missing file, unreadable, or a corrupt last line — treat as "no prior
    // entry" so a single bad line can never permanently block future writes.
    return null;
  }
}

readStdinJson((parsed, stdinFailed) => {
  try {
    if (stdinFailed || !parsed.cwd) {
      process.exitCode = 0;
      return;
    }
    const cwd = parsed.cwd;
    if (!readProjectConfig(cwd).hooksEnabled) {
      process.exitCode = 0;
      return;
    }

    const headSha = runGit(['rev-parse', 'HEAD'], cwd);
    const branch = runGit(['branch', '--show-current'], cwd);
    const headMessage = runGit(['log', '-1', '--format=%s'], cwd);
    const statusShort = runGit(['status', '--porcelain'], cwd);

    const jsonlPath = path.join(WAYPOINTS_DIR, `${slugify(cwd)}.jsonl`);
    const previous = readLastEntry(jsonlPath);
    const isDuplicate =
      previous &&
      previous.headSha === headSha &&
      previous.branch === branch &&
      previous.statusShort === statusShort;

    if (!isDuplicate) {
      fs.mkdirSync(WAYPOINTS_DIR, { recursive: true });
      const entry = { timestamp: new Date().toISOString(), cwd, branch, headSha, headMessage, statusShort };
      fs.appendFileSync(jsonlPath, JSON.stringify(entry) + '\n');
    }
  } catch {
    // fail-open — see header comment
  }
  process.exitCode = 0;
}, { timeoutMs: STDIN_READ_TIMEOUT_MS });
