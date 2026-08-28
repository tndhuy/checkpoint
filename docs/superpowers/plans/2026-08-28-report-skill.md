# Report skill implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a new `report` skill to the `checkpoint` plugin that persists an immutable, evidence-backed completion report per finished task, mirroring the depth of the user's chat-side Task Reporting convention.

**Architecture:** A new sibling skill directory `plugins/checkpoint/skills/report/` (single `SKILL.md`, no local assets — reuses `../checkpoint/assets/` and `../checkpoint/references/` exactly like `save`/`recall`/`list` already do) plus one new template asset `plugins/checkpoint/skills/checkpoint/assets/report-template.md`. Reports write to `.checkpoint/reports/<YYYY-MM-DD>-<slug>.md`, one immutable file per finished task — a distinct `type: report` frontmatter value, never touched by `list`/`recall`. No new hook: the skill proposes itself via its own `Decide` section, the same pattern `checkpoint/SKILL.md` already uses for unfinished-state checkpoints.

**Tech Stack:** Markdown skill files (Claude Code / Codex plugin format), Python `unittest` for static content tests, existing `scripts/validate_distribution.py` distribution validator.

**Spec:** `docs/superpowers/specs/2026-08-27-completion-report-skill-design.md`

## Global Constraints

- Report filename: `<YYYY-MM-DD>-<slug>.md` under `.checkpoint/reports/` (project scope) or the equivalent path under the resolved global root (global scope) — `slug` is a short kebab-case rendering of the task title; on a same-day collision append `-2`, `-3`, etc.; never overwrite an existing report.
- Report frontmatter keys, exact names and order: `type`, `created`, `profile`, `scope`, `role`, `project`, `branch`, `related_checkpoint`. `created` is ISO 8601 with time.
- No new hook. Self-suggestion is judgment-driven from the skill's own `Decide` section only.
- Reports are immutable — never edited or overwritten after being written.
- `report` reuses `../checkpoint/references/scope-and-role.md` and `../checkpoint/references/profiles.md` verbatim — no new config surface, no new resolution logic.
- Every generated report is written in the language used by the user in the current request, unless the user explicitly requests another language (same rule already centralized in `plugins/checkpoint/skills/checkpoint/SKILL.md`).
- Optional headings (`ELI5`, `Ghi chú thuật ngữ`, `Đề xuất mở rộng`) are omitted entirely when they don't apply — never padded with an empty section.
- Version bump touches exactly these 4 tracked manifests, all set to the same value: `plugins/checkpoint/.claude-plugin/plugin.json`, `plugins/checkpoint/.codex-plugin/plugin.json`, `pyproject.toml`, `.claude-plugin/marketplace.json` (`metadata.version`). Next version: `0.1.18`.

---

### Task 1: Report template asset

**Files:**
- Create: `plugins/checkpoint/skills/checkpoint/assets/report-template.md`
- Test: `tests/test_skill_instruction.py` (add methods; import already present)

**Interfaces:**
- Produces: a file at `plugins/checkpoint/skills/checkpoint/assets/report-template.md` with frontmatter keys `type`, `created`, `profile`, `scope`, `role`, `project`, `branch`, `related_checkpoint` and headings `## Kết quả & lý do`, `## Kỹ thuật đã dùng`, `## Thay đổi cụ thể`, `## ELI5`, `## Ghi chú thuật ngữ`, `## Đề xuất mở rộng`. Task 2's `report/SKILL.md` references this exact path as `../checkpoint/assets/report-template.md`.

- [ ] **Step 1: Write the failing test**

Open `tests/test_skill_instruction.py` and add this method to `SkillInstructionTests` (place it after `test_language_rule_addresses_mixed_language_sessions`):

```python
    def test_report_template_has_required_and_conditional_sections(self):
        template = (
            SKILLS / "checkpoint" / "assets" / "report-template.md"
        ).read_text(encoding="utf-8")
        for key in (
            "type: report",
            "created:",
            "profile:",
            "scope:",
            "role:",
            "project:",
            "branch:",
            "related_checkpoint:",
        ):
            with self.subTest(key=key):
                self.assertIn(key, template)
        for heading in (
            "## Kết quả & lý do",
            "## Kỹ thuật đã dùng",
            "## Thay đổi cụ thể",
            "## ELI5",
            "## Ghi chú thuật ngữ",
            "## Đề xuất mở rộng",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, template)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_skill_instruction.SkillInstructionTests.test_report_template_has_required_and_conditional_sections -v`
Expected: FAIL — `FileNotFoundError` (the template does not exist yet).

- [ ] **Step 3: Create the template asset**

Create `plugins/checkpoint/skills/checkpoint/assets/report-template.md` with exactly this content:

```markdown
---
type: report
created: YYYY-MM-DDTHH:MM:SS+00:00
profile: generic
scope: project
role: ""
project: ""
branch: ""
related_checkpoint: ""
---

# Report — <task title>

## Kết quả & lý do

<What was actually accomplished. Why this approach was picked over
alternatives — name at least one alternative considered and why it lost, or
say explicitly there wasn't a real alternative.>

## Kỹ thuật đã dùng

<The algorithm / data structure / pattern applied, why it fits here, whether
it's already best practice for this case or a more optimal option exists
worth flagging, and the one-line lesson learned.>

## Thay đổi cụ thể

<What changed, file by file if more than one was touched. Call out
explicitly which parts need careful review (risky, non-obvious, or
hard-to-reverse) versus which are routine.>

## ELI5

<Optional — only for genuinely non-trivial concepts. Omit this heading
entirely if nothing in the task needs it; don't force a trivial restatement.>

## Ghi chú thuật ngữ

<Optional. Footnote (¹ ² *) for a term used once or twice, inline with a
one-line explanation right after. Glossary (term → definition list) only
when 4+ new terms appear. Callout/sidebar (`> [!NOTE]`) for a tangential
explanation that would break the main narrative if inlined. Omit this
heading if nothing needs annotating.>

## Đề xuất mở rộng

<Optional. Further research or practical extensions worth considering later.
Omit if none.>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_skill_instruction.SkillInstructionTests.test_report_template_has_required_and_conditional_sections -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add plugins/checkpoint/skills/checkpoint/assets/report-template.md tests/test_skill_instruction.py
git commit -m "feat(checkpoint): add completion-report template asset"
```

---

### Task 2: `report` skill instructions and distribution wiring

**Files:**
- Create: `plugins/checkpoint/skills/report/SKILL.md`
- Modify: `scripts/validate_distribution.py:16` (`CODEX_SKILLS` tuple)
- Test: `tests/test_skill_instruction.py` (add methods); existing `tests/test_distribution.py::test_repository_distribution_is_valid` exercises the new skill automatically once wired

**Interfaces:**
- Consumes: `plugins/checkpoint/skills/checkpoint/assets/report-template.md` (Task 1), `../checkpoint/references/scope-and-role.md`, `../checkpoint/references/profiles.md` (both pre-existing, unmodified).
- Produces: `plugins/checkpoint/skills/report/SKILL.md` with frontmatter `name: report`, `argument-hint:`, `allowed-tools:`. Task 3's forward test dispatches a fresh agent with this file's full text.

- [ ] **Step 1: Write the failing tests**

Add these two methods to `SkillInstructionTests` in `tests/test_skill_instruction.py`, after the method added in Task 1:

```python
    def test_report_skill_carries_slash_command_frontmatter(self):
        content = (SKILLS / "report" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: report", content)
        self.assertIn("argument-hint:", content)
        self.assertIn("allowed-tools:", content)

    def test_report_skill_follows_the_users_language(self):
        content = (SKILLS / "report" / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(content.split())
        self.assertIn("language used by the user in the current request", normalized)
        self.assertIn("explicitly requests another language", normalized)

    def test_report_skill_proposes_before_writing_unless_explicit(self):
        content = (SKILLS / "report" / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(content.split())
        self.assertIn("ask before persisting", normalized)
        self.assertIn("write it directly", normalized)

    def test_report_skill_omits_inapplicable_optional_headings(self):
        content = (SKILLS / "report" / "SKILL.md").read_text(encoding="utf-8")
        normalized = " ".join(content.split())
        self.assertIn("Ghi chú thuật ngữ", normalized)
        self.assertIn("Đề xuất mở rộng", normalized)
        self.assertIn("don", normalized)  # "don't pad" — cheap smoke check
```

Also extend the two existing parametrized tests to cover `report` alongside `save`/`list`/`recall`:

```python
    def test_codex_namespaced_skills_are_self_contained(self):
        for name in ("save", "list", "recall", "report"):
            with self.subTest(name=name):
                content = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(f"name: {name}", content)
                self.assertNotIn("../../commands/", content)

    def test_skills_carry_slash_command_frontmatter(self):
        # No separate commands/ directory: Claude Code merges command and skill
        # invocation, and a skill takes precedence over any same-named commands/
        # file, so commands/ added nothing but a second place for this to drift.
        # Each skill's own frontmatter must carry what a command file used to.
        for name in ("save", "list", "recall", "report"):
            with self.subTest(name=name):
                content = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("argument-hint:", content)
                self.assertIn("allowed-tools:", content)
```

(Replace the two existing method bodies in place — same method names, `"report"` added to each tuple.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_skill_instruction -v`
Expected: FAIL — `FileNotFoundError` for the new methods; the two extended parametrized tests FAIL their `report` subtest.

- [ ] **Step 3: Write `plugins/checkpoint/skills/report/SKILL.md`**

Create the file with exactly this content:

```markdown
---
name: report
description: Persist a detailed, evidence-backed completion report for a finished substantive task — what was achieved and why, technique/algorithm assessment, diff highlights, and optional ELI5/glossary/further-research sections. Use when the user invokes $checkpoint:report, or proactively propose it right after finishing a substantive task (feature shipped, bug fixed, investigation concluded) the same way checkpoint proposes itself for unfinished state.
argument-hint: "[--scope project|global] [--role <text>] [optional note]"
allowed-tools: Read, Write, Edit
---

# Report — completion report

Persist an immutable retrospective for a finished task. Never edit or overwrite a written report — every report is a new file.

## Decide

Recommend a report right after finishing a substantive task whose rationale, technique, or diff would take real work to reconstruct later — a shipped feature, a fixed bug, a concluded investigation. Skip trivial completed Q&A.

If not explicitly requested, explain why it helps, propose the destination (`.checkpoint/reports/<date>-<slug>.md`) and ask before persisting. If the user explicitly invokes `$checkpoint:report`, write it directly instead of summarizing this process.

## Scope and role

Resolve `scope` (`project` default, or `global`) and `role` exactly as `save` does — see `../checkpoint/references/scope-and-role.md`. Reuse the same `.checkpoint/config.md` (or global config) already recorded for this project; never re-ask once a value exists. An explicit `--scope`/`--role` flag on this invocation overrides and re-persists the value for this project.

## Profile

Resolve exactly as `save` does — see `../checkpoint/references/profiles.md`. Use `developer` when repository, branch, test, or build evidence exists for the finished task; `operations`/`research` per their usual triggers; otherwise `generic`.

## Gather evidence

Capture only what's actually true: real alternatives actually considered (never invent one that wasn't weighed), the real technique or pattern applied, the real files changed, and a genuine one-line lesson learned. Never invent a lesson, an alternative, or a review-attention flag that has no basis in the actual work.

## Write

Use `../checkpoint/assets/report-template.md` as the exact skeleton, including its YAML frontmatter (`type: report`, `created`, `profile`, `scope`, `role`, `project`, `branch`, `related_checkpoint`). Name the file `<YYYY-MM-DD>-<slug>.md` under `.checkpoint/reports/` (or the equivalent path under the resolved global root), where `slug` is a short kebab-case rendering of the task title. On a same-day slug collision, append `-2`, `-3`, etc. — never overwrite an existing report.

Write the report in the language used by the user in the current request, unless the user explicitly requests another language — the same rule centralized in `../checkpoint/SKILL.md`. Keep technical identifiers, paths, commands, branch names, and error messages verbatim.

Omit the `ELI5`, `Ghi chú thuật ngữ`, and `Đề xuất mở rộng` headings entirely when they don't apply to this task — don't pad a report with a heading that has nothing under it.

## Quality gate

Before finishing, verify: does this report let someone who wasn't here understand what happened and why, without re-deriving it from the diff themselves? If not, the report is incomplete.
```

- [ ] **Step 4: Wire the skill into the distribution validator**

In `scripts/validate_distribution.py`, change line 16 from:

```python
CODEX_SKILLS = ("checkpoint", "save", "list", "recall")
```

to:

```python
CODEX_SKILLS = ("checkpoint", "save", "list", "recall", "report")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: PASS — all tests including `test_repository_distribution_is_valid` (which now validates `report/SKILL.md`'s frontmatter name and its `../checkpoint/assets/report-template.md` resource reference resolves to a real file).

- [ ] **Step 6: Commit**

```bash
git add plugins/checkpoint/skills/report/SKILL.md scripts/validate_distribution.py tests/test_skill_instruction.py
git commit -m "feat(checkpoint): add report skill for immutable completion reports"
```

---

### Task 3: Fresh-agent forward test

**Files:**
- Create (scratch, not committed): a temporary fixture prompt, dispatched via the `Agent` tool — no repo file needed for the fixture itself.
- Create: `benchmarks/results/2026-08-28/report-skill-forward-test.md` (evidence, committed)

**Interfaces:**
- Consumes: the full text of `plugins/checkpoint/skills/report/SKILL.md` (Task 2) and `plugins/checkpoint/skills/checkpoint/assets/report-template.md` (Task 1), read fresh — do not paraphrase them into the dispatch prompt.

- [ ] **Step 1: Set up an isolated scratch directory**

```bash
mkdir -p /tmp/report-skill-forward-test/.checkpoint
cat > /tmp/report-skill-forward-test/.checkpoint/config.md <<'EOF'
---
type: checkpoint-config
scope: project
role: ""
updated: 2026-08-28
---

Local project marker.
EOF
```

This pre-resolves scope/role so the forward test isolates report-writing behavior, not the (already-tested) first-run scope/role exchange.

- [ ] **Step 2: Dispatch a fresh agent with real file tools**

Use the `Agent` tool with `subagent_type: "general-purpose"` (fresh — do not use `fork`, which would inherit this session's context) and this prompt, with `{SKILL_TEXT}` and `{TEMPLATE_TEXT}` replaced by the literal file contents read in this step (do not summarize them):

```
You are testing a documentation skill in isolation. You have Read/Write/Edit
tools and a working directory at /tmp/report-skill-forward-test. Nothing
else about this session is real context — treat the task below as the only
thing that just happened.

You just finished this task in the project at
/tmp/report-skill-forward-test:

"Fixed a bug where the login form accepted empty passwords because a
client-side check used `if (password)` instead of `if (password.length > 0)`
— an empty string is falsy in JS either way, so this fix made no behavioral
difference and was reverted; the real fix was adding a server-side length
check in `POST /api/login`, since the client-side check can be bypassed
entirely. Considered adding a third-party validation library
(`validator.js`) instead of a hand-written length check, but rejected it —
one field, one condition, not worth a new dependency. Changed
`server/routes/login.js` (added the length check) and
`server/routes/login.test.js` (added a regression test for an
empty-password POST). Ran `npm test -- login.test.js`, both tests pass."

Follow this skill's instructions exactly:

--- plugins/checkpoint/skills/report/SKILL.md ---
{SKILL_TEXT}
--- end SKILL.md ---

--- plugins/checkpoint/skills/checkpoint/assets/report-template.md ---
{TEMPLATE_TEXT}
--- end report-template.md ---

The user's message was: "$checkpoint:report" (an explicit invocation — write
the report file now, do not just describe it).
```

- [ ] **Step 3: Inspect the produced file against this checklist**

```bash
find /tmp/report-skill-forward-test/.checkpoint/reports -type f
cat /tmp/report-skill-forward-test/.checkpoint/reports/*.md
```

Check each of the following and note pass/fail for each:
1. File path matches `<YYYY-MM-DD>-<slug>.md` under `.checkpoint/reports/`.
2. Frontmatter has all 8 keys (`type: report`, `created`, `profile`, `scope`, `role`, `project`, `branch`, `related_checkpoint`) with real (non-placeholder) values.
3. `## Kết quả & lý do` names the rejected alternative (`validator.js`) and why it lost.
4. `## Kỹ thuật đã dùng` names the actual fix (server-side length check) and a lesson.
5. `## Thay đổi cụ thể` lists both changed files.
6. `## ELI5` — this fixture has no genuinely non-trivial concept; confirm the heading is **omitted**, not present-and-empty.
7. `## Ghi chú thuật ngữ` — confirm omitted or, if present, actually annotates a term (not padding).
8. `## Đề xuất mở rộng` — confirm omitted or genuinely useful if present.
9. No invented facts (no test count, no coverage percentage, no detail not present in the fixture task description).

- [ ] **Step 4: Record the result**

Write `benchmarks/results/2026-08-28/report-skill-forward-test.md` following the shape of `benchmarks/results/2026-08-07/report.md` (Verdict, Method, Results, Findings, Fix if any, Verification). If any checklist item in Step 3 fails, revise `report/SKILL.md` or `report-template.md`, re-run Steps 2–3 with a second fresh agent, and record both runs (baseline-fail + corrected-pass) exactly as the 2026-08-07 precedent does. If everything passes on the first run, record a single-run PASS.

- [ ] **Step 5: Commit**

```bash
git add benchmarks/results/2026-08-28/report-skill-forward-test.md
git commit -m "test(checkpoint): forward-test the report skill with a fresh agent"
```

(If Step 4 required a fix to `report/SKILL.md` or `report-template.md`, stage and commit those alongside the evidence in this same commit, and re-run `python3 -m unittest discover -s tests -v` first to confirm the fix didn't break Task 1/2's static tests.)

---

### Task 4: Version bump and changelog

**Files:**
- Modify: `plugins/checkpoint/.claude-plugin/plugin.json:2`
- Modify: `plugins/checkpoint/.codex-plugin/plugin.json:2`
- Modify: `pyproject.toml:3`
- Modify: `.claude-plugin/marketplace.json:8`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: nothing new — this task only changes version literals and adds a changelog entry describing Tasks 1–3.

- [ ] **Step 1: Bump all 4 version manifests to `0.1.18`**

```bash
python3 - <<'EOF'
import re
from pathlib import Path

files = {
    "plugins/checkpoint/.claude-plugin/plugin.json": ('"version": "0.1.17"', '"version": "0.1.18"'),
    "plugins/checkpoint/.codex-plugin/plugin.json": ('"version": "0.1.17"', '"version": "0.1.18"'),
    "pyproject.toml": ('version = "0.1.17"', 'version = "0.1.18"'),
    ".claude-plugin/marketplace.json": ('"version": "0.1.17"', '"version": "0.1.18"'),
}
for path, (old, new) in files.items():
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    assert old in text, f"{path}: expected string not found"
    p.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"updated {path}")
EOF
```

- [ ] **Step 2: Add the changelog entry**

Open `CHANGELOG.md` and insert this new section immediately after the `# Changelog` header, before the existing `## [0.1.17] - 2026-08-27` entry:

```markdown
## [0.1.18] - 2026-08-28

### Added
- New `report` skill (`plugins/checkpoint/skills/report/SKILL.md`) persists an immutable, evidence-backed completion report per finished task at `.checkpoint/reports/<date>-<slug>.md` — what was achieved and why (with alternatives considered), the technique/pattern applied and whether it's optimal, a file-by-file diff summary flagging what needs careful review, and optional `ELI5`/`Ghi chú thuật ngữ`/`Đề xuất mở rộng` sections omitted when they don't apply. Proactively self-suggests after a substantive completed task the same way `checkpoint` already suggests itself for unfinished state — no new hook; Claude Code has no "task complete" lifecycle event, so this is judgment-driven from the skill's own `Decide` section, mirroring `checkpoint/SKILL.md`'s existing pattern. New template asset `plugins/checkpoint/skills/checkpoint/assets/report-template.md`. `scripts/validate_distribution.py`'s `CODEX_SKILLS` now includes `report`.

```

- [ ] **Step 3: Run full verification**

```bash
python3 scripts/verify.py
claude plugin validate --strict .
claude plugin validate --strict plugins/checkpoint
```

Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add plugins/checkpoint/.claude-plugin/plugin.json plugins/checkpoint/.codex-plugin/plugin.json pyproject.toml .claude-plugin/marketplace.json CHANGELOG.md
git commit -m "chore(checkpoint): bump version to 0.1.18 for the report skill"
```
