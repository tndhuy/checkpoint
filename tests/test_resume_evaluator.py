import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluate_resume import evaluate


def output(questions: int = 0) -> dict:
    return {
        "current_state": "expected provider calls 1",
        "exact_next_action": "inspect service",
        "scope_boundary": "do not change public response shape",
        "done_gate": "focused test passes",
        "reconstructive_questions": ["question"] * questions,
    }


class ResumeEvaluatorTests(unittest.TestCase):
    def test_complete_resume_passes(self):
        result = evaluate(
            output(),
            ("expected provider calls 1", "do not change public response shape"),
        )
        self.assertTrue(result.passed)

    def test_missing_fact_fails(self):
        result = evaluate(output(), ("missing fact",))
        self.assertFalse(result.passed)
        self.assertEqual(result.missing_resume_terms, ("missing fact",))

    def test_checkpoint_must_need_fewer_questions_than_baseline(self):
        self.assertTrue(evaluate(output(1), (), output(2)).passed)
        self.assertFalse(evaluate(output(2), (), output(2)).passed)


if __name__ == "__main__":
    unittest.main()
