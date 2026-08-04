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

    def test_all_contract_headings_are_named_in_skill(self):
        content = SKILL.read_text(encoding="utf-8")
        for heading in REQUIRED_HEADINGS:
            with self.subTest(heading=heading):
                self.assertIn(f"- {heading}", content)

    def test_codex_namespaced_skills_are_self_contained(self):
        for name in ("save", "list", "recall"):
            with self.subTest(name=name):
                content = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(f"name: {name}", content)
                self.assertNotIn("../../commands/", content)

    def test_claude_commands_delegate_to_host_neutral_skills(self):
        commands = ROOT / "plugins" / "checkpoint" / "commands"
        for name in ("save", "list", "recall"):
            with self.subTest(name=name):
                content = (commands / f"{name}.md").read_text(encoding="utf-8")
                self.assertIn(f"@./skills/{name}/SKILL.md", content)


if __name__ == "__main__":
    unittest.main()
