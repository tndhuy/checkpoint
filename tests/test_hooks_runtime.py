import json
import subprocess
import sys
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1] / "plugins" / "checkpoint" / "hooks"


def run_hook(name: str, stdin: str, timeout: float = 5.0) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["node", str(HOOKS / name)],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class StopCheckpointTests(unittest.TestCase):
    def test_blocks_on_normal_stop(self):
        result = run_hook("stop-checkpoint.js", "{}")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "block")
        self.assertIn("checkpoint:save", payload["reason"])

    def test_does_not_block_when_stop_hook_active(self):
        result = run_hook("stop-checkpoint.js", json.dumps({"stop_hook_active": True}))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_fails_safe_not_block_on_empty_stdin(self):
        result = run_hook("stop-checkpoint.js", "")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "", "empty/unparseable stdin must not force a block")

    def test_fails_safe_not_block_on_malformed_json(self):
        result = run_hook("stop-checkpoint.js", "{not valid json")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "", "malformed stdin must not force a block")


class PreCompactReminderTests(unittest.TestCase):
    def test_echoes_known_trigger(self):
        result = run_hook("pre-compact-reminder.js", json.dumps({"trigger": "manual"}))
        self.assertEqual(result.returncode, 0)
        self.assertIn("trigger: manual", result.stdout)
        self.assertIn("checkpoint:save", result.stdout)

    def test_falls_back_to_unknown_on_malformed_json(self):
        result = run_hook("pre-compact-reminder.js", "not json")
        self.assertEqual(result.returncode, 0)
        self.assertIn("trigger: unknown", result.stdout)

    def test_falls_back_to_unknown_on_empty_stdin(self):
        result = run_hook("pre-compact-reminder.js", "")
        self.assertEqual(result.returncode, 0)
        self.assertIn("trigger: unknown", result.stdout)


class PostCompactCheckpointTests(unittest.TestCase):
    def test_emits_session_start_context(self):
        result = run_hook("post-compact-checkpoint.js", "")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn("checkpoint:save", payload["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
