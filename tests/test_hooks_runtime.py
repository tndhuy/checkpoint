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

    def test_reminder_scopes_the_forced_turn_to_persistence_only(self):
        # Regression: a prior wording only said "run save", which left the
        # forced turn free to redo/re-verify already-finished work and then
        # re-narrate it in chat — producing a near-duplicate of a report the
        # user had already been given a moment earlier.
        result = self.run_stop("{}")
        context = self.assert_blocked(result.stdout)
        self.assertIn("persist to file only", context)
        self.assertIn("do not redo, re-verify, or re-narrate", context)

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


class WaypointWriterTests(unittest.TestCase):
    def setUp(self):
        self._waypoints_dir = tempfile.TemporaryDirectory()
        self.waypoints_dir = self._waypoints_dir.name
        self._repo_dir = tempfile.TemporaryDirectory()
        self.repo_dir = self._repo_dir.name
        subprocess.run(["git", "init", "-q", "-b", "main", self.repo_dir], check=True)
        subprocess.run(["git", "-C", self.repo_dir, "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", self.repo_dir, "config", "user.name", "Test"], check=True)
        (Path(self.repo_dir) / "file.txt").write_text("hello")
        subprocess.run(["git", "-C", self.repo_dir, "add", "file.txt"], check=True)
        subprocess.run(["git", "-C", self.repo_dir, "commit", "-q", "-m", "init"], check=True)

    def tearDown(self):
        self._waypoints_dir.cleanup()
        self._repo_dir.cleanup()

    def slug(self) -> str:
        return self.repo_dir.replace("/", "-")

    def waypoint_file(self) -> Path:
        return Path(self.waypoints_dir) / f"{self.slug()}.jsonl"

    def run_waypoint(self, stdin: str, config_file: str | None = None) -> subprocess.CompletedProcess:
        env = {"CHECKPOINT_WAYPOINTS_DIR": self.waypoints_dir}
        if config_file is not None:
            env["CHECKPOINT_CONFIG_FILE"] = config_file
        return run_hook("waypoint-writer.js", stdin, env=env)

    def test_writes_one_line_for_clean_repo(self):
        result = self.run_waypoint(json.dumps({"cwd": self.repo_dir}))
        self.assertEqual(result.returncode, 0)
        lines = self.waypoint_file().read_text().strip().splitlines()
        self.assertEqual(len(lines), 1)
        entry = json.loads(lines[0])
        self.assertEqual(entry["cwd"], self.repo_dir)
        self.assertEqual(entry["branch"], "main")
        self.assertIn("headSha", entry)
        self.assertEqual(entry["statusShort"], "")

    def test_dedupes_identical_state(self):
        self.run_waypoint(json.dumps({"cwd": self.repo_dir}))
        self.run_waypoint(json.dumps({"cwd": self.repo_dir}))
        lines = self.waypoint_file().read_text().strip().splitlines()
        self.assertEqual(len(lines), 1, "identical git state must not be logged twice")

    def test_logs_again_after_new_commit(self):
        self.run_waypoint(json.dumps({"cwd": self.repo_dir}))
        (Path(self.repo_dir) / "file.txt").write_text("changed")
        subprocess.run(["git", "-C", self.repo_dir, "commit", "-aqm", "second"], check=True)
        self.run_waypoint(json.dumps({"cwd": self.repo_dir}))
        lines = self.waypoint_file().read_text().strip().splitlines()
        self.assertEqual(len(lines), 2)

    def test_logs_again_after_branch_change_at_same_commit(self):
        self.run_waypoint(json.dumps({"cwd": self.repo_dir}))
        subprocess.run(["git", "-C", self.repo_dir, "checkout", "-qb", "other"], check=True)
        self.run_waypoint(json.dumps({"cwd": self.repo_dir}))
        lines = self.waypoint_file().read_text().strip().splitlines()
        self.assertEqual(len(lines), 2)

    def test_hooks_enabled_false_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            config_file = str(Path(d) / "config.md")
            Path(config_file).write_text("---\nhooks_enabled: false\n---\n")
            result = self.run_waypoint(json.dumps({"cwd": self.repo_dir}), config_file=config_file)
            self.assertEqual(result.returncode, 0)
            self.assertFalse(self.waypoint_file().exists())

    def test_silent_on_non_git_directory(self):
        with tempfile.TemporaryDirectory() as d:
            result = self.run_waypoint(json.dumps({"cwd": d}))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_silent_on_empty_stdin(self):
        result = self.run_waypoint("")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(list(Path(self.waypoints_dir).iterdir()), [])

    def test_silent_on_malformed_stdin(self):
        result = self.run_waypoint("{not valid json")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_silent_when_cwd_missing(self):
        result = self.run_waypoint(json.dumps({"stop_hook_active": True}))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(list(Path(self.waypoints_dir).iterdir()), [])

    def test_silent_when_waypoints_dir_unwritable(self):
        parent = Path(self.waypoints_dir)
        parent.chmod(0o500)  # read + execute, no write
        try:
            result = self.run_waypoint(json.dumps({"cwd": self.repo_dir}))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
        finally:
            parent.chmod(0o700)  # restore so tearDown's cleanup() can delete it


class HooksRegistrationTests(unittest.TestCase):
    def test_waypoint_writer_registered_additively_as_async(self):
        hooks_json = json.loads((HOOKS / "hooks.json").read_text())
        expectations = {"Stop": "stop-checkpoint.js", "PreCompact": "pre-compact-reminder.js"}
        for event, existing_script in expectations.items():
            groups = hooks_json["hooks"][event]
            commands = [h["command"] for group in groups for h in group["hooks"]]
            self.assertTrue(
                any("waypoint-writer.js" in c for c in commands), f"{event} is missing waypoint-writer.js"
            )
            self.assertTrue(
                any(existing_script in c for c in commands), f"{event} lost its existing hook {existing_script}"
            )
            for group in groups:
                for h in group["hooks"]:
                    if "waypoint-writer.js" in h["command"]:
                        self.assertIs(h.get("async"), True, "waypoint-writer.js must be registered async")
                    else:
                        self.assertNotIn("async", h, f"{existing_script} must stay synchronous")


if __name__ == "__main__":
    unittest.main()
