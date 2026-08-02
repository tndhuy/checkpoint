#!/usr/bin/env python3
"""Validate the tracked plugin distribution without external dependencies."""
from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "checkpoint-skill"
PLUGIN = ROOT / "plugins" / PLUGIN_NAME
SKILL = PLUGIN / "skills" / "checkpoint"
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
PRIVATE_MARKERS = ("/Users/", "\\Users\\", "trannguyendanghuy", "Workspace/personal")


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def is_semver(value: object) -> bool:
    return isinstance(value, str) and bool(SEMVER.fullmatch(value))


def find_entry(marketplace: dict) -> dict | None:
    for item in marketplace.get("plugins", []):
        if isinstance(item, dict) and item.get("name") == PLUGIN_NAME:
            return item
    return None


def validate(root: Path = ROOT) -> list[str]:
    plugin = root / "plugins" / PLUGIN_NAME
    skill = plugin / "skills" / "checkpoint"
    errors: list[str] = []
    required = (
        root / "LICENSE",
        root / ".agents/plugins/marketplace.json",
        root / ".claude-plugin/marketplace.json",
        plugin / ".codex-plugin/plugin.json",
        plugin / ".claude-plugin/plugin.json",
        skill / "SKILL.md",
        skill / "agents/openai.yaml",
        skill / "assets/checkpoint-template.md",
        skill / "references/profiles.md",
    )
    for path in required:
        if not path.is_file():
            errors.append(f"missing required file: {path.relative_to(root)}")
    if errors:
        return errors

    codex = load_json(plugin / ".codex-plugin/plugin.json")
    claude = load_json(plugin / ".claude-plugin/plugin.json")
    codex_market = load_json(root / ".agents/plugins/marketplace.json")
    claude_market = load_json(root / ".claude-plugin/marketplace.json")
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    versions = {
        "project": project["project"]["version"],
        "codex plugin": codex.get("version"),
        "claude plugin": claude.get("version"),
        "claude marketplace": claude_market.get("metadata", {}).get("version"),
    }

    for label, version in versions.items():
        if not is_semver(version):
            errors.append(f"{label} version is not strict semver: {version!r}")
    if len(set(versions.values())) != 1:
        errors.append(f"version mismatch: {versions}")

    if codex.get("name") != PLUGIN_NAME or claude.get("name") != PLUGIN_NAME:
        errors.append("plugin manifest names must match the plugin directory")
    if codex.get("skills") != "./skills/":
        errors.append("Codex manifest skills path must be ./skills/")
    if not codex.get("author", {}).get("name"):
        errors.append("Codex manifest requires author.name")

    codex_entry = find_entry(codex_market)
    expected_source = {"source": "local", "path": "./plugins/checkpoint-skill"}
    if codex_entry is None:
        errors.append("Codex marketplace is missing checkpoint-skill")
    elif codex_entry.get("source") != expected_source:
        errors.append("Codex marketplace source must target ./plugins/checkpoint-skill")

    claude_entry = find_entry(claude_market)
    if claude_entry is None:
        errors.append("Claude marketplace is missing checkpoint-skill")
    elif claude_entry.get("source") != "./plugins/checkpoint-skill":
        errors.append("Claude marketplace source must target ./plugins/checkpoint-skill")

    for path in plugin.rglob("*"):
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        marker = next((item for item in PRIVATE_MARKERS if item in content), None)
        if marker:
            errors.append(f"private path marker {marker!r} in {path.relative_to(root)}")

    skill_text = (skill / "SKILL.md").read_text(encoding="utf-8")
    for relative in re.findall(r"(?:references|assets)/[A-Za-z0-9._/-]+", skill_text):
        if not (skill / relative.rstrip(".,;)")).is_file():
            errors.append(f"broken skill resource reference: {relative}")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: distribution manifests, versions, paths and privacy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
