// Shared stdin-read-and-parse helper for checkpoint hooks.
//
// Every native hook that needs input from Claude Code follows the same
// shape: read stdin up to a size cap, wait up to a timeout, then parse as
// JSON — treating an empty/oversized/unparseable/timed-out read as a
// distinct `stdinFailed` case so callers can choose a safe fallback
// direction instead of guessing (see stop-checkpoint.js's fail-toward-
// not-blocking policy — a failed read must never quietly become "no
// signal, proceed as if everything is fine").

const MAX_STDIN_BYTES = 64 * 1024; // generous cap — these payloads are small JSON objects, not a real limit

function readStdinJson(onDone, { timeoutMs } = {}) {
  let input = '';
  let capped = false;
  let done = false;

  function finish(parsed, stdinFailed) {
    if (done) return;
    done = true;
    clearTimeout(timer);
    onDone(parsed, stdinFailed);
  }

  const timer = setTimeout(() => finish({}, true), timeoutMs);

  process.stdin.setEncoding('utf8');
  process.stdin.on('data', (chunk) => {
    if (capped) return;
    input += chunk;
    if (Buffer.byteLength(input, 'utf8') > MAX_STDIN_BYTES) {
      capped = true;
      process.stdin.destroy();
      finish({}, true);
    }
  });
  process.stdin.on('end', () => {
    if (capped) return;
    let parsed = {};
    let stdinFailed = false;
    try {
      parsed = JSON.parse(input);
    } catch {
      stdinFailed = true;
    }
    if (parsed === null || typeof parsed !== 'object') {
      parsed = {};
      stdinFailed = true;
    }
    finish(parsed, stdinFailed);
  });
}

module.exports = { readStdinJson, MAX_STDIN_BYTES };
