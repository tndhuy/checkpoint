import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from checkpoint_contract import REQUIRED_HEADINGS, validate


def checkpoint(extra: str = "") -> str:
    sections = "\n\n".join(f"## {heading}\ncontent" for heading in REQUIRED_HEADINGS)
    return sections + "\n" + extra


class ContractTests(unittest.TestCase):
    def test_generic_contract_passes(self):
        self.assertTrue(validate(checkpoint()).passed)

    def test_missing_required_heading_fails(self):
        result = validate(checkpoint().replace("## Next action", "## Later"))
        self.assertFalse(result.passed)
        self.assertIn("Next action", result.missing_headings)

    def test_developer_profile_requires_resume_evidence(self):
        body = checkpoint("repository branch changed files tests resume")
        self.assertTrue(validate(body, "developer").passed)

    def test_expected_facts_are_checked(self):
        result = validate(checkpoint(), expected_terms=("unique blocker",))
        self.assertEqual(result.missing_expected_terms, ("unique blocker",))

    def test_formatting_and_minor_word_forms_do_not_cause_false_negative(self):
        body = checkpoint(
            "expected provider calls `1`; do not: change the public response shape; "
            "citation is a paraphrase"
        )
        result = validate(
            body,
            expected_terms=(
                "expected provider calls 1",
                "do not change public response shape",
                "paraphrased",
            ),
        )
        self.assertTrue(result.passed)

    def test_profile_concepts_accept_clear_equivalents(self):
        developer = checkpoint("working directory branch changed files test resume")
        operations = checkpoint("environment process state memory pressure recovery diagnostic")
        self.assertTrue(validate(developer, "developer").passed)
        self.assertTrue(validate(operations, "operations").passed)

    def test_unknown_profile_rejected(self):
        with self.assertRaises(ValueError):
            validate(checkpoint(), "finance")


if __name__ == "__main__":
    unittest.main()
