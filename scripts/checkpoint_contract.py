"""Deterministic checkpoint contract validation."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path

REQUIRED_HEADINGS = (
    "Outcome",
    "Scope and boundaries",
    "Current state",
    "Last verified evidence",
    "Files, artifacts and processes",
    "Next action",
    "Blocker or risk",
    "Done when",
)

TOTAL_WORD_CEILING = 400
SECTION_WORD_CEILING = 80

PROFILE_CONCEPTS = {
    "generic": (),
    "developer": (
        ("repository", "repo root", "working directory"),
        ("branch",),
        ("changed files",),
        ("test",),
        ("resume",),
    ),
    "research": (
        ("research question",),
        ("sources", "source state"),
        ("verified claim", "claim is marked verified"),
        ("open question", "question remains open"),
    ),
    "operations": (
        ("environment",),
        ("service", "process state"),
        ("metrics", "memory pressure", "swap"),
        ("recovery", "safe diagnostic"),
        ("diagnostic", "diagnosis"),
    ),
}


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    score: int
    maximum: int
    missing_headings: tuple[str, ...]
    missing_profile_terms: tuple[str, ...]
    missing_expected_terms: tuple[str, ...]
    verbosity_warnings: tuple[str, ...] = ()

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def headings(markdown: str) -> set[str]:
    return {match.strip() for match in re.findall(r"^##\s+(.+)$", markdown, re.MULTILINE)}


def word_count(text: str) -> int:
    return len(text.split())


def section_bodies(markdown: str) -> dict[str, str]:
    """Map each `## Heading` to the text before the next `##` heading."""
    parts = re.split(r"^##\s+(.+)$", markdown, flags=re.MULTILINE)
    bodies: dict[str, str] = {}
    for index in range(1, len(parts), 2):
        heading = parts[index].strip()
        body = parts[index + 1] if index + 1 < len(parts) else ""
        bodies[heading] = body
    return bodies


def verbosity_check(
    markdown: str,
    total_ceiling: int = TOTAL_WORD_CEILING,
    section_ceiling: int = SECTION_WORD_CEILING,
) -> tuple[str, ...]:
    """Soft, non-blocking word-count warnings. Never affects `passed`."""
    warnings: list[str] = []
    total = word_count(markdown)
    if total > total_ceiling:
        warnings.append(f"total body is {total} words, over the {total_ceiling}-word soft ceiling")
    for heading, body in section_bodies(markdown).items():
        count = word_count(body)
        if count > section_ceiling:
            warnings.append(
                f"'{heading}' section is {count} words, over the {section_ceiling}-word soft ceiling"
            )
    return tuple(warnings)


def normalize(value: str) -> str:
    """Ignore formatting, punctuation, articles and a tiny set of word forms."""
    aliases = {
        "paraphrased": "paraphrase",
        "paraphrasing": "paraphrase",
    }
    tokens = re.sub(r"[^a-z0-9]+", " ", value.lower()).split()
    canonical = (aliases.get(token, token) for token in tokens if token not in {"a", "an", "the"})
    return " ".join(canonical)


def concept_present(content: str, alternatives: tuple[str, ...]) -> bool:
    normalized = normalize(content)
    return any(normalize(term) in normalized for term in alternatives)


def validate(markdown: str, profile: str = "generic", expected_terms: tuple[str, ...] = ()) -> ValidationResult:
    if profile not in PROFILE_CONCEPTS:
        raise ValueError(f"unknown profile: {profile}")
    present = headings(markdown)
    missing_headings = tuple(item for item in REQUIRED_HEADINGS if item not in present)
    missing_profile = tuple(
        alternatives[0]
        for alternatives in PROFILE_CONCEPTS[profile]
        if not concept_present(markdown, alternatives)
    )
    missing_expected = tuple(term for term in expected_terms if not concept_present(markdown, (term,)))
    maximum = len(REQUIRED_HEADINGS) + len(PROFILE_CONCEPTS[profile]) + len(expected_terms)
    score = maximum - len(missing_headings) - len(missing_profile) - len(missing_expected)
    return ValidationResult(
        not any((missing_headings, missing_profile, missing_expected)),
        score,
        maximum,
        missing_headings,
        missing_profile,
        missing_expected,
        verbosity_check(markdown),
    )


def load_expectations(path: Path) -> tuple[str, tuple[str, ...]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return str(data["profile"]), tuple(str(item) for item in data.get("required_terms", []))
