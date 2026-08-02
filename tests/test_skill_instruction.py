import unittest
from pathlib import Path

from scripts.checkpoint_contract import REQUIRED_HEADINGS


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins" / "checkpoint-skill" / "skills" / "checkpoint" / "SKILL.md"


class SkillInstructionTests(unittest.TestCase):
    def test_explicit_invocation_requires_canonical_template(self):
        content = SKILL.read_text(encoding="utf-8")
        self.assertIn("explicitly invokes `$checkpoint` or `/checkpoint`", content)
        self.assertIn("always render the full canonical template", content)
        self.assertIn("Do not collapse it into a summary", content)

    def test_all_contract_headings_are_named_in_skill(self):
        content = SKILL.read_text(encoding="utf-8")
        for heading in REQUIRED_HEADINGS:
            with self.subTest(heading=heading):
                self.assertIn(f"- {heading}", content)


if __name__ == "__main__":
    unittest.main()
