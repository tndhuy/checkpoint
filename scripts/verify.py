#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins/checkpoint-skill/skills/checkpoint"


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


def run(command: tuple[str, ...]) -> bool:
    return subprocess.run(command, cwd=ROOT, check=False).returncode == 0


def main() -> int:
    checks = (
        validate_skill(),
        run((sys.executable, "-B", "scripts/validate_distribution.py")),
        run((sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v")),
    )
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
