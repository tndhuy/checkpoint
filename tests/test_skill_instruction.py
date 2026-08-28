import unittest
from pathlib import Path

from scripts.checkpoint_contract import REQUIRED_HEADINGS


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins" / "checkpoint" / "skills"
SKILL = SKILLS / "checkpoint" / "SKILL.md"


class SkillInstructionTests(unittest.TestCase):
    def test_explicit_invocation_requires_canonical_template(self):
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("including `$checkpoint`, `/checkpoint`", content)
        self.assertIn("`$checkpoint:checkpoint`", content)
        self.assertIn("always render the full canonical template", content)
        self.assertIn("Do not collapse it into a summary", content)

    def test_developer_unknowns_and_boundaries_are_explicit(self):
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("always include `Working directory`, `Branch`, `Changed files`", content)
        self.assertIn("write `Unknown` for any missing fact", content)
        self.assertIn("one line beginning `- Do not:`", content)

    def test_generated_checkpoints_follow_the_users_language(self):
        for name in ("checkpoint", "save"):
            with self.subTest(name=name):
                content = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
                normalized = " ".join(content.split())
                self.assertIn(
                    "language used by the user in the current request",
                    normalized,
                )
                self.assertIn("explicitly requests another language", normalized)
                self.assertIn("error messages verbatim", normalized)

    def test_recall_and_list_reports_follow_the_users_language(self):
        for name in ("recall", "list"):
            with self.subTest(name=name):
                content = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
                normalized = " ".join(content.split())
                self.assertIn(
                    "language used by the user in the current request",
                    normalized,
                )
                self.assertIn("explicitly requests another language", normalized)

    def test_language_rule_addresses_mixed_language_sessions(self):
        content = (SKILLS / "checkpoint" / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(content.split())
        self.assertIn("even when the surrounding session is", normalized)
        self.assertIn("do not default to English", normalized)

    def test_report_template_has_required_and_conditional_sections(self):
        template = (
            SKILLS / "checkpoint" / "assets" / "report-template.md"
        ).read_text(encoding="utf-8")
        for key in (
            "type: report",
            "created:",
            "profile:",
            "scope:",
            "role:",
            "project:",
            "branch:",
            "related_checkpoint:",
        ):
            with self.subTest(key=key):
                self.assertIn(key, template)
        for heading in (
            "## Kết quả & lý do",
            "## Kỹ thuật đã dùng",
            "## Thay đổi cụ thể",
            "## ELI5",
            "## Ghi chú thuật ngữ",
            "## Đề xuất mở rộng",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, template)

    def test_all_contract_headings_are_named_in_skill(self):
        content = SKILL.read_text(encoding="utf-8")
        for heading in REQUIRED_HEADINGS:
            with self.subTest(heading=heading):
                self.assertIn(f"- {heading}", content)

    def test_report_skill_carries_slash_command_frontmatter(self):
        content = (SKILLS / "report" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: report", content)
        self.assertIn("argument-hint:", content)
        self.assertIn("allowed-tools:", content)

    def test_report_skill_follows_the_users_language(self):
        content = (SKILLS / "report" / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(content.split())
        self.assertIn("language used by the user in the current request", normalized)
        self.assertIn("explicitly requests another language", normalized)

    def test_report_skill_proposes_before_writing_unless_explicit(self):
        content = (SKILLS / "report" / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(content.split())
        self.assertIn("ask before persisting", normalized)
        self.assertIn("write it directly", normalized)

    def test_report_skill_omits_inapplicable_optional_headings(self):
        content = (SKILLS / "report" / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(content.split())
        self.assertIn("Ghi chú thuật ngữ", normalized)
        self.assertIn("Đề xuất mở rộng", normalized)
        self.assertIn("don", normalized)  # "don't pad" — cheap smoke check

    def test_codex_namespaced_skills_are_self_contained(self):
        for name in ("save", "list", "recall", "report"):
            with self.subTest(name=name):
                content = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(f"name: {name}", content)
                self.assertNotIn("../../commands/", content)

    def test_skills_carry_slash_command_frontmatter(self):
        # No separate commands/ directory: Claude Code merges command and skill
        # invocation, and a skill takes precedence over any same-named commands/
        # file, so commands/ added nothing but a second place for this to drift.
        # Each skill's own frontmatter must carry what a command file used to.
        for name in ("save", "list", "recall", "report"):
            with self.subTest(name=name):
                content = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("argument-hint:", content)
                self.assertIn("allowed-tools:", content)

    def test_no_stray_commands_directory(self):
        self.assertFalse((ROOT / "plugins" / "checkpoint" / "commands").exists())


if __name__ == "__main__":
    unittest.main()
