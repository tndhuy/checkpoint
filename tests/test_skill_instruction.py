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

    def test_hook_triggered_invocation_collapses_chat_output(self):
        for name in ("checkpoint", "save"):
            with self.subTest(name=name):
                content = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
                normalized = " ".join(content.split())
                self.assertIn("A hook-triggered invocation", normalized)
                self.assertIn("chat response collapses to one line", normalized)
                self.assertIn(
                    "do not redo, re-verify, or re-narrate work already completed",
                    normalized,
                )

    def test_developer_unknowns_and_boundaries_are_explicit(self):
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("always include `Working directory`, `Branch`, `Changed files`", content)
        self.assertIn("write `Unknown` for any missing fact", content)
        self.assertIn("one line beginning `- Do not:`", content)

    def test_generated_checkpoints_resolve_language_via_scope_and_role(self):
        for name in ("checkpoint", "save"):
            with self.subTest(name=name):
                content = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
                normalized = " ".join(content.split())
                self.assertIn("scope-and-role.md", normalized)
                self.assertIn("Language section", normalized)
                self.assertIn("persisted", normalized)
                self.assertIn("error messages verbatim", normalized)

    def test_recall_and_list_reports_resolve_language_via_scope_and_role(self):
        for name in ("recall", "list"):
            with self.subTest(name=name):
                content = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
                normalized = " ".join(content.split())
                self.assertIn("scope-and-role.md", normalized)
                self.assertIn("Language section", normalized)

    def test_scope_and_role_reference_defines_language_resolution(self):
        content = (
            SKILLS / "checkpoint" / "references" / "scope-and-role.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(content.split())
        self.assertIn("## Language", content)
        self.assertIn("--language", normalized)
        self.assertIn(
            "language used by the user in the current request",
            normalized,
        )
        self.assertIn("persist", normalized)
        self.assertIn("overrides the current-request fallback", normalized)

    def test_scope_config_template_declares_language_field(self):
        content = (
            SKILLS / "checkpoint" / "assets" / "scope-config-template.md"
        ).read_text(encoding="utf-8")
        self.assertIn('language: ""', content)

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

    def test_report_skill_resolves_language_via_scope_and_role(self):
        content = (SKILLS / "report" / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(content.split())
        self.assertIn("scope-and-role.md", normalized)
        self.assertIn("Language section", normalized)

    def test_update_section_forbids_full_section_rewrites(self):
        content = SKILL.read_text(encoding="utf-8")
        normalized = " ".join(content.split())
        self.assertIn("diff the new facts against what the existing file already says", normalized)
        self.assertIn("keep its existing wording verbatim", normalized)
        self.assertIn("5 lines", normalized)

    def test_save_skill_documents_waypoint_evidence_step(self):
        content = (SKILLS / "save" / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(content.split())
        self.assertIn("checkpoint-skill/waypoints", normalized)
        self.assertIn(".consumed", normalized)
        self.assertIn("never for", normalized)
        self.assertIn("Never truncate or delete", content)

    def test_save_skill_waypoint_slug_matches_hook_convention(self):
        content = (SKILLS / "save" / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(content.split())
        self.assertIn("replace every `/` with `-`", normalized)

    def test_save_skill_cross_references_update_rule(self):
        content = (SKILLS / "save" / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(content.split())
        self.assertIn("checkpoint/SKILL.md", normalized)
        self.assertIn("Update section", normalized)
        self.assertIn("length ceiling", normalized)

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
        self.assertIn(
            "Omit the `ELI5`, `Ghi chú thuật ngữ`, and `Đề xuất mở rộng` headings entirely when they don't apply",
            normalized,
        )

    def test_list_and_recall_exclude_report_files(self):
        for name in ("list", "recall"):
            with self.subTest(name=name):
                content = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
                normalized = " ".join(content.split())
                self.assertIn(
                    "Exclude `type: report` files and anything under a `reports/` subtree",
                    normalized,
                )

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
