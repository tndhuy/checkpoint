import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1] / "plugins" / "checkpoint" / "hooks"


def run_hook(name: str, stdin: str, env: dict | None = None, timeout: float = 5.0) -> subprocess.CompletedProcess:
    full_env = {**os.environ, **(env or {})}
    return subprocess.run(
        ["node", str(HOOKS / name)],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=full_env,
    )


class StopCheckpointTests(unittest.TestCase):
    def setUp(self):
        # Isolate the cooldown marker per test — the real hook shares one
        # file across invocations by design, which would make these tests
        # order-dependent (and flaky under repeated runs) if left unset.
        self._cooldown_dir = tempfile.TemporaryDirectory()
        self.cooldown_file = str(Path(self._cooldown_dir.name) / "cooldown.json")

    def tearDown(self):
        self._cooldown_dir.cleanup()

    def run_stop(self, stdin: str, config_file: str | None = None) -> subprocess.CompletedProcess:
        env = {"CHECKPOINT_STOP_COOLDOWN_FILE": self.cooldown_file}
        if config_file is not None:
            env["CHECKPOINT_CONFIG_FILE"] = config_file
        return run_hook("stop-checkpoint.js", stdin, env=env)

    @staticmethod
    def assert_blocked(stdout: str) -> str:
        # Documented Stop-hook decision control (Claude Code hooks reference):
        # hookSpecificOutput.additionalContext forces the same extra-turn
        # continuation as decision: "block" (same stop_hook_active /
        # continuation-cap protections), but the transcript labels it "Stop
        # hook feedback" instead of a "hook error" notice — deliberately not
        # using decision/reason, which IS documented but renders as an error
        # even when the hook is working exactly as designed.
        payload = json.loads(stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        assert payload["hookSpecificOutput"]["hookEventName"] == "Stop"
        return context

    def test_blocks_on_normal_stop(self):
        result = self.run_stop("{}")
        self.assertEqual(result.returncode, 0)
        context = self.assert_blocked(result.stdout)
        self.assertIn("checkpoint:save", context)

    def test_does_not_block_when_stop_hook_active(self):
        result = self.run_stop(json.dumps({"stop_hook_active": True}))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_fails_safe_not_block_on_empty_stdin(self):
        result = self.run_stop("")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "", "empty/unparseable stdin must not force a block")

    def test_fails_safe_not_block_on_malformed_json(self):
        result = self.run_stop("{not valid json")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "", "malformed stdin must not force a block")

    def test_cooldown_suppresses_repeat_block(self):
        first = self.run_stop("{}")
        self.assert_blocked(first.stdout)
        second = self.run_stop("{}")
        self.assertEqual(second.stdout, "", "a second Stop within the cooldown window must not block again")

    def test_cooldown_expires(self):
        Path(self.cooldown_file).write_text(json.dumps({"lastBlockedAt": 0}))  # far in the past
        result = self.run_stop("{}")
        self.assert_blocked(result.stdout)

    def test_corrupt_cooldown_file_does_not_crash(self):
        Path(self.cooldown_file).write_text("not json")
        result = self.run_stop("{}")
        self.assertEqual(result.returncode, 0)
        self.assert_blocked(result.stdout)

    def test_hooks_enabled_false_suppresses_block(self):
        with tempfile.TemporaryDirectory() as d:
            config_file = str(Path(d) / "config.md")
            Path(config_file).write_text("---\nhooks_enabled: false\n---\n")
            result = self.run_stop("{}", config_file=config_file)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_custom_cooldown_zero_never_suppresses(self):
        with tempfile.TemporaryDirectory() as d:
            config_file = str(Path(d) / "config.md")
            Path(config_file).write_text("---\nstop_cooldown_minutes: 0\n---\n")
            first = self.run_stop("{}", config_file=config_file)
            self.assert_blocked(first.stdout)
            second = self.run_stop("{}", config_file=config_file)
            self.assert_blocked(second.stdout)

    def test_missing_config_file_defaults_to_enabled_with_20min_cooldown(self):
        with tempfile.TemporaryDirectory() as d:
            config_file = str(Path(d) / "does-not-exist.md")
            result = self.run_stop("{}", config_file=config_file)
            self.assert_blocked(result.stdout)

    def test_malformed_config_file_fails_open_to_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            config_file = str(Path(d) / "config.md")
            Path(config_file).write_text("not frontmatter at all")
            result = self.run_stop("{}", config_file=config_file)
            self.assertEqual(result.returncode, 0)
            self.assert_blocked(result.stdout)

    def test_invalid_cooldown_value_falls_back_to_default(self):
        with tempfile.TemporaryDirectory() as d:
            config_file = str(Path(d) / "config.md")
            Path(config_file).write_text("---\nstop_cooldown_minutes: not-a-number\n---\n")
            first = self.run_stop("{}", config_file=config_file)
            self.assert_blocked(first.stdout)
            second = self.run_stop("{}", config_file=config_file)
            self.assertEqual(
                second.stdout, "", "an invalid cooldown value must fall back to the 20-minute default, not 0"
            )


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

    def test_hooks_enabled_false_suppresses_reminder(self):
        with tempfile.TemporaryDirectory() as d:
            config_file = str(Path(d) / "config.md")
            Path(config_file).write_text("---\nhooks_enabled: false\n---\n")
            result = run_hook(
                "pre-compact-reminder.js",
                json.dumps({"trigger": "manual"}),
                env={"CHECKPOINT_CONFIG_FILE": config_file},
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")


class PostCompactCheckpointTests(unittest.TestCase):
    def test_emits_session_start_context(self):
        result = run_hook("post-compact-checkpoint.js", "")
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn("checkpoint:save", payload["hookSpecificOutput"]["additionalContext"])

    def test_still_emits_context_when_stdin_is_empty(self):
        # Empty stdin means stdinFailed=true means cwd is unknown — this
        # must never suppress the reminder (see the hook's own comment on
        # fail-open-to-emit). Config-driven suppression only applies when
        # cwd/config were actually readable.
        with tempfile.TemporaryDirectory() as d:
            config_file = str(Path(d) / "config.md")
            Path(config_file).write_text("---\nhooks_enabled: false\n---\n")
            result = run_hook(
                "post-compact-checkpoint.js", "", env={"CHECKPOINT_CONFIG_FILE": config_file}
            )
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "SessionStart")

    def test_hooks_enabled_false_suppresses_context_with_valid_stdin(self):
        with tempfile.TemporaryDirectory() as d:
            config_file = str(Path(d) / "config.md")
            Path(config_file).write_text("---\nhooks_enabled: false\n---\n")
            result = run_hook(
                "post-compact-checkpoint.js",
                json.dumps({"cwd": d}),
                env={"CHECKPOINT_CONFIG_FILE": config_file},
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
