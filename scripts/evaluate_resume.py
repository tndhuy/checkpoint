#!/usr/bin/env python3
"""Evaluate whether a cold agent can resume from a checkpoint."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from checkpoint_contract import concept_present

REQUIRED_KEYS = (
    "current_state",
    "exact_next_action",
    "scope_boundary",
    "done_gate",
    "reconstructive_questions",
)


@dataclass(frozen=True)
class ResumeResult:
    passed: bool
    missing_keys: tuple[str, ...]
    invalid_keys: tuple[str, ...]
    missing_resume_terms: tuple[str, ...]
    reconstructive_questions: int
    baseline_questions: int | None
    fewer_questions_than_baseline: bool | None

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def question_count(data: dict) -> int:
    questions = data.get("reconstructive_questions")
    return len(questions) if isinstance(questions, list) else 0


def evaluate(data: dict, expected_terms: tuple[str, ...], baseline: dict | None = None) -> ResumeResult:
    missing_keys = tuple(key for key in REQUIRED_KEYS if key not in data)
    invalid_keys = tuple(
        key for key in REQUIRED_KEYS[:-1] if key in data and not isinstance(data[key], str)
    )
    if "reconstructive_questions" in data and not isinstance(data["reconstructive_questions"], list):
        invalid_keys += ("reconstructive_questions",)

    content = "\n".join(str(data.get(key, "")) for key in REQUIRED_KEYS[:-1])
    missing_expected = tuple(
        term for term in expected_terms if not concept_present(content, (term,))
    )
    questions = question_count(data)
    baseline_questions = question_count(baseline) if baseline is not None else None
    fewer = questions < baseline_questions if baseline_questions is not None else None
    passed = not missing_keys and not invalid_keys and not missing_expected
    if baseline is not None:
        passed = passed and bool(fewer)

    return ResumeResult(
        passed,
        missing_keys,
        invalid_keys,
        missing_expected,
        questions,
        baseline_questions,
        fewer,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("resume", type=Path)
    parser.add_argument("expectations", type=Path)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()

    resume = load_json(args.resume)
    expected = load_json(args.expectations)
    baseline = load_json(args.baseline) if args.baseline else None
    terms = expected.get("resume_required_terms", expected.get("required_terms", []))
    result = evaluate(resume, tuple(str(item) for item in terms), baseline)
    print(result.to_json())
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
