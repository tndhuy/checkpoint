#!/usr/bin/env python3
"""Validate the tracked plugin distribution without external dependencies."""
from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = "checkpoint"
PLUGIN_NAME = "checkpoint"
PLUGIN = ROOT / "plugins" / PLUGIN_DIR
SKILL = PLUGIN / "skills" / "checkpoint"
CODEX_SKILLS = ("checkpoint", "save", "list", "recall")
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
    plugin = root / "plugins" / PLUGIN_DIR
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
        plugin / "hooks/hooks.json",
        *(plugin / "skills" / name / "SKILL.md" for name in CODEX_SKILLS),
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

    if plugin.name != PLUGIN_NAME:
        errors.append("plugin directory must match the plugin namespace")
    if codex.get("name") != PLUGIN_NAME or claude.get("name") != PLUGIN_NAME:
        errors.append("plugin manifest names must match the plugin directory")
    if codex.get("skills") != "./skills/":
        errors.append("Codex manifest skills path must be ./skills/")
    if not codex.get("author", {}).get("name"):
        errors.append("Codex manifest requires author.name")

    codex_entry = find_entry(codex_market)
    expected_source = {"source": "local", "path": "./plugins/checkpoint"}
    if codex_entry is None:
        errors.append("Codex marketplace is missing checkpoint")
    elif codex_entry.get("source") != expected_source:
        errors.append("Codex marketplace source must target ./plugins/checkpoint")

    claude_entry = find_entry(claude_market)
    if claude_entry is None:
        errors.append("Claude marketplace is missing checkpoint")
    elif claude_entry.get("source") != "./plugins/checkpoint":
        errors.append("Claude marketplace source must target ./plugins/checkpoint")

    for name in CODEX_SKILLS:
        skill_file = plugin / "skills" / name / "SKILL.md"
        text = skill_file.read_text(encoding="utf-8")
        if not re.search(rf"^name:\s*{re.escape(name)}\s*$", text, re.MULTILINE):
            errors.append(f"Codex skill {name!r} has a mismatched frontmatter name")

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

    errors.extend(validate_hooks(plugin))
    return errors


def validate_hooks(plugin: Path) -> list[str]:
    errors: list[str] = []
    hooks_file = plugin / "hooks" / "hooks.json"
    try:
        manifest = load_json(hooks_file)
    except (json.JSONDecodeError, ValueError) as exc:
        return [f"hooks/hooks.json is not valid JSON: {exc}"]

    events = manifest.get("hooks")
    if not isinstance(events, dict) or not events:
        return ["hooks/hooks.json must have a non-empty top-level \"hooks\" object"]

    command_pattern = re.compile(r'"\$\{CLAUDE_PLUGIN_ROOT\}([^"]+)"')
    for event, groups in events.items():
        if not isinstance(groups, list) or not groups:
            errors.append(f"hooks.{event} must be a non-empty array")
            continue
        for group in groups:
            entries = group.get("hooks") if isinstance(group, dict) else None
            if not isinstance(entries, list) or not entries:
                errors.append(f"hooks.{event} has a group with no \"hooks\" array")
                continue
            for entry in entries:
                command = entry.get("command") if isinstance(entry, dict) else None
                if not isinstance(command, str) or "${CLAUDE_PLUGIN_ROOT}" not in command:
                    errors.append(f"hooks.{event} command must reference ${{CLAUDE_PLUGIN_ROOT}}: {command!r}")
                    continue
                match = command_pattern.search(command)
                if not match:
                    errors.append(f"hooks.{event} command has an unparseable ${{CLAUDE_PLUGIN_ROOT}} path: {command!r}")
                    continue
                referenced = plugin / match.group(1).lstrip("/")
                if not referenced.is_file():
                    errors.append(f"hooks.{event} references a missing script: {referenced.relative_to(plugin.parent.parent)}")
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
