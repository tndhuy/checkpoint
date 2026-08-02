#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/checkpoint"


def validate_skill() -> bool:
    content = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not frontmatter:
        print("FAIL: missing SKILL.md frontmatter")
        return False
    metadata = frontmatter.group(1)
    checks = (
        "name: checkpoint" in metadata,
        "description:" in metadata,
        (SKILL / "agents/openai.yaml").is_file(),
        (SKILL / "assets/checkpoint-template.md").is_file(),
        (SKILL / "references/profiles.md").is_file(),
        "$checkpoint" in (SKILL / "agents/openai.yaml").read_text(encoding="utf-8"),
    )
    if not all(checks):
        print("FAIL: skill structure or metadata invalid")
        return False
    print("PASS: skill structure")
    return True


def main() -> int:
    structure_ok = validate_skill()
    tests = subprocess.run(
        (sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"),
        cwd=ROOT,
        check=False,
    )
    return 0 if structure_ok and tests.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
