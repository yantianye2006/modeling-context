#!/usr/bin/env python3
"""Validate a generated modeling-start Obsidian context.

The validator intentionally uses only the Python standard library so it can run
in the same environments as init_modeling_context.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable


STAGES = ("problem-framing", "analysis", "implementation", "validation", "writing")
STAGE_ORDER = {stage: index for index, stage in enumerate(STAGES)}
FILE_STATUSES = ("draft", "active", "validated", "superseded")
ITEM_STATUSES = ("planned", "drafted", "active", "superseded")
DELIVERABLE_KINDS = ("figure", "table", "rule", "threshold", "schedule", "plan")
GATE_STATUSES = ("not-checked", "blocked", "passed", "waived")
PROJECT_GATES = ("GP",)
QUESTION_GATES = ("G0", "G0.5", "G1", "G2", "G3")
PLACEHOLDER_RE = re.compile(r"\{\{[^{}]+\}\}")
QUESTION_FILE_RE = re.compile(r"^问题(\d+)_分析卡\.md$")
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
FIELD_RE = re.compile(r"^([A-Za-z_\u4e00-\u9fff][\w\u4e00-\u9fff-]*):\s*(.*)$")
GATE_SUMMARY_START = "<!-- modeling-start:gate-summary:start -->"
GATE_SUMMARY_END = "<!-- modeling-start:gate-summary:end -->"
BUDGET_SUMMARY_START = "<!-- modeling-start:budget-summary:start -->"
BUDGET_SUMMARY_END = "<!-- modeling-start:budget-summary:end -->"
QUESTION_BLOCK_RE = re.compile(
    r"<!-- modeling-start:question:(\d+):start -->(.*?)<!-- modeling-start:question:\1:end -->",
    re.DOTALL,
)
G0_AUDIT_START = "<!-- modeling-start:g0-audit:v1:start -->"
G0_AUDIT_END = "<!-- modeling-start:g0-audit:v1:end -->"
G05_DIAGNOSTIC_START = "<!-- modeling-start:g0-5-diagnostic:v1:start -->"
G05_DIAGNOSTIC_END = "<!-- modeling-start:g0-5-diagnostic:v1:end -->"
G05_ROUTES = ("simple", "nonlinear", "structured", "information_limited")
G05_REFORMULATIONS = ("none", "target", "information", "output")
G05_PROBE_STATUSES = ("planned", "executed", "not-applicable")
MODEL_STATUSES = ("候选", "主模型", "辅助模型", "备用", "淘汰")
G05_CRITERIA_FIELDS = (
    "最小有意义增益",
    "最差情形退化容忍度",
    "泛化差距容忍度",
    "方向一致性参考",
    "主指标、辅助指标及优先级",
    "指标冲突时的取舍原则",
    "复杂度升级条件",
    "停止搜索条件",
)
G05_PROBE_HASH_FIELDS = (
    "探针 ID",
    "探针角色",
    "实现候选",
    "检验的假设",
    "共享划分",
    "适用性、理由与误判风险",
    "是否调参",
)
G05_RESULT_VALUE_FIELDS = (
    "主指标",
    "关键辅助指标",
    "波动",
    "最差情形",
    "训练—验证差距",
    "相对基线差异",
)
G0_AUDIT_FIELDS = (
    "目标量",
    "观测机制",
    "信息坍缩链",
    "相关结构",
    "基线难度",
    "输出分辨率",
    "判定",
    "处置",
    "证据",
)
PARAMETER_CHECK_START = "<!-- modeling-start:parameter-check:v1:start -->"
PARAMETER_CHECK_END = "<!-- modeling-start:parameter-check:v1:end -->"
SELF_CHECK_STATUSES = ("passed", "not-applicable")
NEGATIVE_CLOSURE_START = "<!-- modeling-start:negative-closure:v1:start -->"
NEGATIVE_CLOSURE_END = "<!-- modeling-start:negative-closure:v1:end -->"
NEGATIVE_DISPOSITIONS = ("替代方案", "缩小范围", "负结论即答案", "未解决")
BUDGET_PLAN_START = "<!-- modeling-start:budget-plan:v1:start -->"
BUDGET_PLAN_END = "<!-- modeling-start:budget-plan:v1:end -->"
BUDGET_LEVELS = ("M1", "M2", "M3")
BUDGET_STATUSES = ("planned", "in-progress", "done", "paused")
DELIVERY_SKELETON_START = "<!-- modeling-start:delivery-skeleton:v1:start -->"
DELIVERY_SKELETON_END = "<!-- modeling-start:delivery-skeleton:v1:end -->"
REQUIREMENT_TRACE_START = "<!-- modeling-start:requirement-trace:v1:start -->"
REQUIREMENT_TRACE_END = "<!-- modeling-start:requirement-trace:v1:end -->"
SKELETON_FIELDS = ("形态", "字段/结构", "单位", "粒度", "使用方式")
# 形态为“结论”的交付对象没有对应的交付物 kind，因此不要求回填交付物 ID。
SKELETON_FORMS_WITHOUT_ID = ("结论",)
TRACE_FIELDS = ("类型", "对应交付物或必做分析", "证据位置")
TRACE_OPEN_STATUS = "planned"


@dataclass(frozen=True)
class Diagnostic:
    severity: str
    code: str
    path: str
    line: int
    message: str


@dataclass
class Note:
    path: Path
    relative: str
    text: str
    lines: list[str]
    frontmatter: dict[str, str | list[str]]
    field_lines: dict[str, int]
    body_start: int


@dataclass
class GateRecord:
    gate: str
    question: str
    line: int
    fields: dict[str, str | list[str]]
    field_lines: dict[str, int]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a modeling-start context directory.")
    parser.add_argument("--context", required=True, type=Path, help="Generated modeling directory")
    parser.add_argument(
        "--mode",
        choices=("auto", "full", "minimal"),
        default="auto",
        help="Context layout; auto detects from filenames",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Return a failing exit code when warnings are present",
    )
    parser.add_argument(
        "--require-gates",
        action="store_true",
        help="Treat legacy contexts without GP/G0/G0.5/G1-G3 records as errors instead of compatibility warnings",
    )
    parser.add_argument(
        "--write-summary",
        action="store_true",
        help="Refresh only the marked derived gate and budget tables in full-mode 项目设计总览.md",
    )
    return parser.parse_args()


def clean_scalar(value: str) -> str:
    value = value.strip()
    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_frontmatter(path: Path, root: Path) -> tuple[Note | None, list[Diagnostic]]:
    relative = path.relative_to(root).as_posix()
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        return None, [Diagnostic("error", "E_READ", relative, 1, f"cannot read UTF-8 text: {exc}")]

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, [Diagnostic("error", "E_FRONTMATTER_MISSING", relative, 1, "missing YAML frontmatter")]

    closing = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
    if closing is None:
        return None, [Diagnostic("error", "E_FRONTMATTER_UNCLOSED", relative, 1, "frontmatter is not closed")]

    data: dict[str, str | list[str]] = {}
    field_lines: dict[str, int] = {}
    current_list: str | None = None
    for index in range(1, closing):
        raw = lines[index]
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[:1].isspace():
            if current_list and raw.strip().startswith("-"):
                item = clean_scalar(raw.strip()[1:].strip())
                assert isinstance(data[current_list], list)
                data[current_list].append(item)
            continue
        match = FIELD_RE.match(raw)
        if not match:
            continue
        key, raw_value = match.groups()
        value = clean_scalar(raw_value)
        field_lines[key] = index + 1
        if value == "":
            data[key] = []
            current_list = key
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [clean_scalar(item) for item in inner.split(",") if item.strip()] if inner else []
            current_list = None
        else:
            data[key] = value
            current_list = None

    return Note(path, relative, text, lines, data, field_lines, closing + 1), []


def scalar(note: Note, key: str) -> str | None:
    value = note.frontmatter.get(key)
    return value if isinstance(value, str) else None


def parse_gate_records(note: Note) -> dict[str, dict[str, GateRecord]]:
    """Parse the intentionally small gate subset of YAML without a PyYAML dependency."""
    records: dict[str, dict[str, GateRecord]] = {}
    gate_start = next(
        (
            index
            for index in range(1, note.body_start - 1)
            if note.lines[index].strip() == "gates:" and not note.lines[index][:1].isspace()
        ),
        None,
    )
    if gate_start is None:
        return records

    end = note.body_start - 1
    for index in range(gate_start + 1, note.body_start - 1):
        raw = note.lines[index]
        if raw.strip() and not raw[:1].isspace():
            end = index
            break

    current: GateRecord | None = None
    current_indent = -1
    current_list: str | None = None
    question_group: str | None = None
    for index in range(gate_start + 1, end):
        raw = note.lines[index]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))

        if stripped.endswith(":"):
            key = clean_scalar(stripped[:-1])
            if indent == 2 and key.isdigit():
                question_group = key
                current = None
                current_list = None
                continue
            if key in PROJECT_GATES + QUESTION_GATES and indent in {2, 4}:
                question = question_group if indent == 4 and question_group else (scalar(note, "question") or "global")
                current = GateRecord(key, question, index + 1, {}, {})
                records.setdefault(question, {})[key] = current
                current_indent = indent
                current_list = None
                continue

        if current and indent == current_indent + 2:
            match = FIELD_RE.match(stripped)
            if not match:
                continue
            key, raw_value = match.groups()
            value = clean_scalar(raw_value)
            current.field_lines[key] = index + 1
            if key == "evidence":
                if value.startswith("[") and value.endswith("]"):
                    inner = value[1:-1].strip()
                    current.fields[key] = [clean_scalar(item) for item in inner.split(",") if item.strip()] if inner else []
                elif value:
                    current.fields[key] = [value]
                else:
                    current.fields[key] = []
                current_list = key
            else:
                current.fields[key] = value
                current_list = None
            continue

        if current and current_list == "evidence" and indent >= current_indent + 4 and stripped.startswith("-"):
            evidence = current.fields.setdefault("evidence", [])
            assert isinstance(evidence, list)
            evidence.append(clean_scalar(stripped[1:].strip()))

    return records


def add(
    diagnostics: list[Diagnostic], severity: str, code: str, note: Note | None, line: int, message: str, path: str = "."
) -> None:
    diagnostics.append(Diagnostic(severity, code, note.relative if note else path, line, message))


def detect_mode(root: Path, requested: str, diagnostics: list[Diagnostic]) -> str | None:
    has_full = (root / "01_数据理解.md").is_file() or any(root.glob("问题*_分析卡.md"))
    has_minimal = (root / "01_数据与口径.md").is_file()
    if requested != "auto":
        if requested == "full" and not has_full:
            diagnostics.append(Diagnostic("error", "E_MODE", ".", 1, "--mode full does not match context files"))
        if requested == "minimal" and not has_minimal:
            diagnostics.append(Diagnostic("error", "E_MODE", ".", 1, "--mode minimal does not match context files"))
        return requested
    if has_full and has_minimal:
        diagnostics.append(Diagnostic("error", "E_MODE_AMBIGUOUS", ".", 1, "both full and minimal layouts are present"))
        return None
    if has_full:
        return "full"
    if has_minimal:
        return "minimal"
    diagnostics.append(Diagnostic("error", "E_MODE_UNKNOWN", ".", 1, "cannot detect full or minimal layout"))
    return None


def required_files(mode: str) -> tuple[str, ...]:
    if mode == "full":
        return (
            "00_赛题总览.md",
            "01_数据理解.md",
            "02_统一口径.md",
            "03_假设与风险.md",
            "模型候选与淘汰.md",
            "决策日志.md",
            "项目设计总览.md",
        )
    return ("00_赛题总览.md", "01_数据与口径.md", "02_问题分析卡.md", "03_决策日志.md")


def validate_required_files(root: Path, mode: str, diagnostics: list[Diagnostic]) -> None:
    for filename in required_files(mode):
        if not (root / filename).is_file():
            diagnostics.append(Diagnostic("error", "E_REQUIRED_FILE", filename, 1, "required context file is missing"))
    if mode == "full" and not any(QUESTION_FILE_RE.match(path.name) for path in root.glob("问题*_分析卡.md")):
        diagnostics.append(Diagnostic("error", "E_QUESTION_FILES", ".", 1, "full mode requires at least one 问题N_分析卡.md"))
    if mode == "full":
        current = (root / "交付物清单.md").is_file()
        legacy = (root / "图表清单.md").is_file()
        if not current and not legacy:
            diagnostics.append(
                Diagnostic("error", "E_REQUIRED_FILE", "交付物清单.md", 1, "required deliverable registry is missing")
            )
        elif current and legacy:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "E_DELIVERABLE_REGISTRY_AMBIGUOUS",
                    ".",
                    1,
                    "交付物清单.md and legacy 图表清单.md both exist; resolve explicitly before continuing",
                )
            )
    if mode == "minimal" and (root / "02_问题分析卡.md").is_file():
        text = (root / "02_问题分析卡.md").read_text(encoding="utf-8-sig")
        if not re.search(r"^## 问题\s+\d+\s*$", text, re.MULTILINE):
            diagnostics.append(Diagnostic("error", "E_QUESTION_SECTIONS", "02_问题分析卡.md", 1, "minimal mode has no 问题 N section"))


def validate_note(note: Note, diagnostics: list[Diagnostic]) -> None:
    required = ("title", "stage", "status", "question", "depends_on", "feeds_into", "updated")
    for key in required:
        if key not in note.frontmatter:
            add(diagnostics, "error", "E_FRONTMATTER_FIELD", note, 1, f"missing frontmatter field: {key}")

    stage = scalar(note, "stage")
    status = scalar(note, "status")
    if stage not in STAGES:
        add(diagnostics, "error", "E_STAGE", note, note.field_lines.get("stage", 1), f"invalid stage: {stage!r}")
    if status not in FILE_STATUSES:
        add(diagnostics, "error", "E_STATUS", note, note.field_lines.get("status", 1), f"invalid file status: {status!r}")

    if stage in STAGES and status in FILE_STATUSES and status != "superseded":
        # Normative source: references/workflow-rules.md §2 "stage 与 status 的兼容表".
        # superseded is a history marker and is exempt. Change the rule there first, then here.
        allowed = {
            "problem-framing": {"draft", "active"},
            "analysis": {"active", "validated"},
            "implementation": {"active", "validated"},
            "validation": {"validated"},
            "writing": {"validated"},
        }[stage]
        if status not in allowed:
            add(
                diagnostics,
                "error",
                "E_STAGE_STATUS",
                note,
                note.field_lines.get("status", 1),
                f"stage {stage!r} is incompatible with file status {status!r}",
            )

    updated = scalar(note, "updated")
    if updated:
        try:
            date.fromisoformat(updated)
        except ValueError:
            add(diagnostics, "error", "E_UPDATED", note, note.field_lines.get("updated", 1), f"invalid ISO date: {updated!r}")

    question = scalar(note, "question")
    match = QUESTION_FILE_RE.match(note.path.name)
    if match and question != match.group(1):
        add(
            diagnostics,
            "error",
            "E_QUESTION_ID",
            note,
            note.field_lines.get("question", 1),
            f"frontmatter question {question!r} does not match filename question {match.group(1)!r}",
        )
    if question is not None and question != "global" and not question.isdigit():
        add(diagnostics, "error", "E_QUESTION_VALUE", note, note.field_lines.get("question", 1), f"invalid question value: {question!r}")

    if PLACEHOLDER_RE.search(note.text):
        for line_number, line in enumerate(note.lines, 1):
            if PLACEHOLDER_RE.search(line):
                add(diagnostics, "error", "E_PLACEHOLDER", note, line_number, "unresolved {{...}} placeholder")

    body_head = "\n".join(note.lines[note.body_start : note.body_start + 60])
    if "> [!context]" not in body_head:
        add(diagnostics, "error", "E_CONTEXT_CALLOUT", note, note.body_start + 1, "missing [!context] callout near file top")


def null_value(value: str | None) -> bool:
    return value is None or value.strip().lower() in {"", "null", "~"}


def gate_value(record: GateRecord, key: str) -> str | None:
    value = record.fields.get(key)
    return value if isinstance(value, str) else None


def validate_gate_record(note: Note, record: GateRecord, diagnostics: list[Diagnostic]) -> None:
    required = ("status", "checked_at", "blocker", "waiver_reason", "evidence")
    for key in required:
        if key not in record.fields:
            add(diagnostics, "error", "E_GATE_FIELD", note, record.line, f"{record.gate} is missing gate field: {key}")

    status = gate_value(record, "status")
    checked_at = gate_value(record, "checked_at")
    blocker = gate_value(record, "blocker")
    waiver_reason = gate_value(record, "waiver_reason")
    evidence_value = record.fields.get("evidence", [])
    evidence = evidence_value if isinstance(evidence_value, list) else []

    if status not in GATE_STATUSES:
        add(
            diagnostics,
            "error",
            "E_GATE_STATUS",
            note,
            record.field_lines.get("status", record.line),
            f"invalid {record.gate} status: {status!r}",
        )
        return

    if not null_value(checked_at):
        try:
            date.fromisoformat(checked_at or "")
        except ValueError:
            add(
                diagnostics,
                "error",
                "E_GATE_DATE",
                note,
                record.field_lines.get("checked_at", record.line),
                f"invalid {record.gate} checked_at ISO date: {checked_at!r}",
            )

    line = record.field_lines.get("status", record.line)
    if status == "not-checked":
        if not null_value(checked_at) or not null_value(blocker) or not null_value(waiver_reason) or evidence:
            add(diagnostics, "error", "E_GATE_FIELDS", note, line, f"{record.gate} not-checked must have no date, blocker, waiver reason, or evidence")
    elif status == "blocked":
        if null_value(checked_at) or null_value(blocker) or not null_value(waiver_reason):
            add(diagnostics, "error", "E_GATE_FIELDS", note, line, f"{record.gate} blocked requires checked_at and blocker, with no waiver_reason")
    elif status == "passed":
        if null_value(checked_at) or not evidence or not null_value(blocker) or not null_value(waiver_reason):
            add(diagnostics, "error", "E_GATE_FIELDS", note, line, f"{record.gate} passed requires checked_at and evidence, with no blocker or waiver_reason")
    elif status == "waived":
        if record.gate != "G2":
            add(diagnostics, "error", "E_GATE_WAIVER", note, line, "only G2 may use waived")
        if null_value(checked_at) or null_value(waiver_reason) or not evidence or not null_value(blocker):
            add(diagnostics, "error", "E_GATE_FIELDS", note, line, f"{record.gate} waived requires checked_at, waiver_reason, and evidence, with no blocker")

    if record.gate == "G0.5":
        extra = ("route", "reformulation", "diagnosis_version")
        for key in extra:
            if key not in record.fields:
                add(diagnostics, "error", "E_G05_GATE_FIELD", note, record.line, f"G0.5 is missing field: {key}")
        route = gate_value(record, "route")
        reformulation = gate_value(record, "reformulation")
        version = gate_value(record, "diagnosis_version")
        if status == "passed":
            if route not in G05_ROUTES:
                add(diagnostics, "error", "E_G05_ROUTE", note, record.field_lines.get("route", line), f"invalid G0.5 route: {route!r}")
            if reformulation not in G05_REFORMULATIONS:
                add(diagnostics, "error", "E_G05_REFORMULATION", note, record.field_lines.get("reformulation", line), f"invalid G0.5 reformulation: {reformulation!r}")
            if null_value(version):
                add(diagnostics, "error", "E_G05_VERSION", note, record.field_lines.get("diagnosis_version", line), "G0.5 passed requires diagnosis_version")
        elif any(not null_value(value) for value in (route, reformulation, version)):
            add(diagnostics, "error", "E_G05_ROUTE_STATE", note, line, "G0.5 route, reformulation, and diagnosis_version must be null unless passed")


def missing_gate(
    note: Note,
    require_gates: bool,
    diagnostics: list[Diagnostic],
    message: str,
) -> None:
    severity = "error" if require_gates else "warning"
    code = "E_GATE_MISSING" if require_gates else "W_LEGACY_GATES"
    add(diagnostics, severity, code, note, note.field_lines.get("gates", 1), message)


def question_sections(note: Note) -> list[str]:
    return re.findall(r"^## 问题\s+(\d+)\s*$", note.text, re.MULTILINE)


def question_content_blocks(notes: list[Note], mode: str) -> list[tuple[Note, str, str, int]]:
    blocks: list[tuple[Note, str, str, int]] = []
    if mode == "full":
        for note in notes:
            match = QUESTION_FILE_RE.match(note.path.name)
            if match and scalar(note, "status") != "superseded":
                blocks.append((note, match.group(1), note.text, 0))
        return blocks

    note = next((item for item in notes if item.relative == "02_问题分析卡.md"), None)
    if not note:
        return blocks
    for match in QUESTION_BLOCK_RE.finditer(note.text):
        blocks.append((note, match.group(1), match.group(2), match.start(2)))
    return blocks


def marked_region(text: str, start_marker: str, end_marker: str) -> tuple[str, int] | None:
    start = text.find(start_marker)
    if start < 0:
        return None
    end = text.find(end_marker, start + len(start_marker))
    if end < 0:
        return None
    body_start = start + len(start_marker)
    return text[body_start:end], body_start


def two_column_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = split_table_row(line)
        if len(cells) >= 2 and cells[0] not in {"项目", "---", ""}:
            fields[cells[0]] = cells[1]
    return fields


def bullet_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"^-\s+([^：:]+)[：:]\s*(.*?)\s*$", line.strip())
        if match:
            fields[match.group(1).strip()] = match.group(2).strip()
    return fields


def table_records(text: str, first_header: str) -> list[dict[str, str]]:
    headers: list[str] | None = None
    records: list[dict[str, str]] = []
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            if headers and records:
                break
            continue
        cells = split_table_row(line)
        if cells and cells[0] == first_header:
            headers = cells
            continue
        if not headers or not cells or all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        padded = cells + [""] * (len(headers) - len(cells))
        records.append(dict(zip(headers, padded)))
    return records


def numbered_subsections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^#{3,6}\s+([1-7])\.\s+.*$", text, re.MULTILINE))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1)] = text[match.end():end]
    return sections


def g05_region(text: str) -> tuple[str, int] | None:
    return marked_region(text, G05_DIAGNOSTIC_START, G05_DIAGNOSTIC_END)


def g05_criteria_material(text: str) -> tuple[dict[str, object] | None, list[str]]:
    region = g05_region(text)
    if region is None:
        return None, ["missing structured G0.5 region"]
    sections = numbered_subsections(region[0])
    if "3" not in sections or "4" not in sections:
        return None, ["missing G0.5 section 3 or 4"]

    issues: list[str] = []
    probes: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in table_records(sections["3"], "探针 ID"):
        probe_id = row.get("探针 ID", "").strip()
        if unfilled(probe_id):
            continue
        status = leading_status(row.get("状态"), G05_PROBE_STATUSES)
        if status not in G05_PROBE_STATUSES:
            issues.append(f"probe {probe_id!r} has invalid status {status!r}")
            continue
        if probe_id in seen:
            issues.append(f"duplicate probe id {probe_id!r}")
        seen.add(probe_id)
        if status == "not-applicable":
            continue
        item: dict[str, str] = {}
        for field in G05_PROBE_HASH_FIELDS:
            value = row.get(field, "").strip()
            if unfilled(value):
                issues.append(f"probe {probe_id!r} has empty hash field {field}")
            item[field] = value
        probes.append(item)

    if not probes:
        issues.append("no applicable G0.5 probes")

    fields = bullet_fields(sections["4"])
    criteria: dict[str, str] = {}
    for field in G05_CRITERIA_FIELDS:
        value = fields.get(field, "").strip()
        if unfilled(value):
            issues.append(f"empty criterion {field}")
        criteria[field] = value

    probes.sort(key=lambda item: item.get("探针 ID", ""))
    payload: dict[str, object] = {
        "schema": "modeling-start-g0.5-criteria-v1",
        "probes": probes,
        "criteria": criteria,
    }
    return payload, issues


def criteria_hash_from_g05(text: str) -> str:
    payload, issues = g05_criteria_material(text)
    if payload is None or issues:
        raise ValueError("; ".join(issues))
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def parse_zoned_timestamp(raw: str | None) -> datetime | None:
    value = (raw or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})", value):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def clean_output_reference(raw: str) -> str:
    value = raw.strip().strip("`").strip()
    if value.startswith("[[") and value.endswith("]]"):
        value = value[2:-2]
    return value.split("#", 1)[0].strip().replace("\\", "/")


def resolve_output_reference(root: Path, raw: str) -> Path | None:
    value = clean_output_reference(raw)
    if not value.startswith("outputs/") or ":" in value:
        return None
    candidate = (root.parent / Path(*value.split("/"))).resolve()
    output_root = (root.parent / "outputs").resolve()
    try:
        candidate.relative_to(output_root)
    except ValueError:
        return None
    return candidate


def preregistration_matches(note: Note | None, question: str, registered_at: str, criteria_hash: str) -> bool:
    if note is None:
        return False
    headings = list(re.finditer(r"^##\s+.*$", note.text, re.MULTILINE))
    for index, match in enumerate(headings):
        if not re.search(r"G0\.5\s+判据预登记\s*$", match.group(0)):
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(note.text)
        block = note.text[match.end():end]
        fields = bullet_fields(block)
        involved = fields.get("涉及问题", "").strip()
        if involved not in {question, f"问题 {question}", f"问题{question}"}:
            continue
        if fields.get("registered_at", "").strip() != registered_at:
            continue
        if fields.get("criteria_hash", "").strip() != criteria_hash:
            continue
        if leading_status(fields.get("状态"), ("proposed", "active", "rejected", "superseded")) not in {"proposed", "active"}:
            continue
        return True
    return False


def question_label_matches(raw: str, question: str) -> bool:
    return re.sub(r"\s+", "", raw.strip()) in {question, f"问题{question}"}


def has_frozen_main_model(
    note_map: dict[str, Note], mode: str, question: str, question_text: str
) -> tuple[bool, Note | None, int]:
    if mode == "full":
        note = note_map.get("模型候选与淘汰.md")
        if note:
            for row in table_records(note.text, "问题"):
                if question_label_matches(row.get("问题", ""), question) and leading_status(
                    row.get("状态"), MODEL_STATUSES
                ) == "主模型":
                    return True, note, 1
        return False, note, 1

    note = note_map.get("02_问题分析卡.md")
    start = question_text.find("<!-- modeling-start:section:main-model:start -->")
    end = question_text.find("<!-- modeling-start:section:main-model:end -->", start + 1)
    if start >= 0 and end >= 0:
        for row in table_records(question_text[start:end], "模型"):
            if leading_status(row.get("状态"), MODEL_STATUSES) == "主模型":
                return True, note, 1
    return False, note, 1


def leading_status(raw: str | None, allowed: Iterable[str]) -> str:
    """取字段的前导状态词。

    手写的状态字段常带括注或简短说明（`passed（三种子重复）`、`planned 待实现`）。
    判定只看前导状态词，其后必须是非字母数字分隔符，因此 `passedX` 不会被误判为 `passed`，
    而 `not-checked（实现阶段执行）` 也不会被误判为已完成。无法识别时原样返回，交由调用方报错。
    """
    text = (raw or "").strip()
    for value in sorted(allowed, key=len, reverse=True):
        if text.lower().startswith(value.lower()):
            rest = text[len(value):]
            if not rest or not (rest[0].isalnum() or rest[0] in "-_"):
                return value
    return text


def validate_g0_5(root: Path, notes: list[Note], mode: str, diagnostics: list[Diagnostic]) -> None:
    note_map = {note.relative: note for note in notes}
    gate_notes = {note.relative: parse_gate_records(note) for note in notes}
    log_note = note_map.get("决策日志.md" if mode == "full" else "03_决策日志.md")
    evidence_rows: list[tuple[Note, str, dict[str, str], int]] = []
    routes: dict[str, list[tuple[Note, str, int]]] = {}

    for note, question, text, offset in question_content_blocks(notes, mode):
        records = gate_notes.get(note.relative, {}).get(question, {})
        g05 = records.get("G0.5")
        if not g05:
            continue
        status = gate_value(g05, "status")
        g1 = records.get("G1")
        g1_status = gate_value(g1, "status") if g1 else None
        line = g05.field_lines.get("status", g05.line)

        if status != "passed":
            if g1_status == "passed":
                add(diagnostics, "error", "E_G05_G1_LOCK", note, line, f"question {question} has G0.5={status} but G1=passed")
            frozen, model_note, model_line = has_frozen_main_model(note_map, mode, question, text)
            if frozen:
                add(
                    diagnostics,
                    "error",
                    "E_G05_MAIN_MODEL_LOCK",
                    model_note,
                    model_line,
                    f"question {question} freezes a 主模型 before G0.5 passed",
                )
            if g1 and not null_value(gate_value(g1, "unlocked_by")):
                add(diagnostics, "error", "E_G05_UNLOCK_STATE", note, g1.field_lines.get("unlocked_by", g1.line), "G1 unlocked_by must be null unless G1 passed")
            continue

        g0 = records.get("G0")
        if not g0 or gate_value(g0, "status") != "passed":
            add(diagnostics, "error", "E_G05_G0_REQUIRED", note, line, f"question {question} cannot pass G0.5 before G0 passed")

        region = g05_region(text)
        if region is None:
            add(diagnostics, "error", "E_G05_STRUCTURE", note, line, f"question {question} has G0.5=passed but no structured diagnostic section")
            continue
        body, relative_start = region
        region_line = note.text[: offset + relative_start].count("\n") + 1
        sections = numbered_subsections(body)
        missing_sections = [number for number in map(str, range(1, 8)) if number not in sections]
        if missing_sections:
            add(diagnostics, "error", "E_G05_STRUCTURE", note, region_line, f"question {question} G0.5 is missing subsections: {', '.join(missing_sections)}")
            continue

        route = gate_value(g05, "route") or ""
        reformulation = gate_value(g05, "reformulation") or ""
        version = gate_value(g05, "diagnosis_version") or ""
        routes.setdefault(route, []).append((note, question, line))

        conclusion = bullet_fields(sections["7"])
        body_status = conclusion.get("gate_status", "").strip()
        if body_status != status or conclusion.get("route", "").strip() != route or conclusion.get("reformulation", "").strip() != reformulation:
            add(diagnostics, "error", "E_G05_ROUTE_MIRROR", note, region_line, f"question {question} G0.5 route conclusion does not match frontmatter")
        conclusion_required = (
            "核心证据",
            "多指标取舍与裁决理由",
            "已否决路线",
            "否决证据",
            "适用边界",
            "G1 获准范围",
            "重新开启条件",
        )
        missing_conclusion = [field for field in conclusion_required if unfilled(conclusion.get(field))]
        if missing_conclusion:
            add(diagnostics, "error", "E_G05_CONCLUSION", note, region_line, f"question {question} G0.5 conclusion is incomplete: {', '.join(missing_conclusion)}")

        probe_rows = [
            row
            for row in table_records(sections["3"], "探针 ID")
            if not unfilled(row.get("探针 ID"))
        ]
        probe_statuses: dict[str, str] = {}
        for row in probe_rows:
            probe_id = row.get("探针 ID", "").strip()
            probe_status = leading_status(row.get("状态"), G05_PROBE_STATUSES)
            if probe_id in probe_statuses:
                add(diagnostics, "error", "E_G05_PROBE_ID", note, region_line, f"question {question} duplicates probe id {probe_id!r}")
            probe_statuses[probe_id] = probe_status
            if probe_status not in G05_PROBE_STATUSES:
                add(diagnostics, "error", "E_G05_PROBE_STATUS", note, region_line, f"question {question} probe {probe_id!r} has invalid status {probe_status!r}")
            elif probe_status == "planned":
                add(diagnostics, "error", "E_G05_PROBE_PENDING", note, region_line, f"question {question} passed G0.5 with planned probe {probe_id!r}")
            elif probe_status == "not-applicable" and unfilled(row.get("适用性、理由与误判风险")):
                add(diagnostics, "error", "E_G05_PROBE_REASON", note, region_line, f"question {question} probe {probe_id!r} is not-applicable without reason and misclassification risk")

        material, material_issues = g05_criteria_material(text)
        if material is None or material_issues:
            add(diagnostics, "error", "E_G05_CRITERIA", note, region_line, f"question {question} invalid preregistration material: {'; '.join(material_issues)}")
            computed_hash = None
        else:
            canonical = json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            computed_hash = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        criteria_fields = bullet_fields(sections["4"])
        registered_at = criteria_fields.get("registered_at", "").strip()
        criteria_hash = criteria_fields.get("criteria_hash", "").strip()
        registered_time = parse_zoned_timestamp(registered_at)
        if registered_time is None:
            add(diagnostics, "error", "E_G05_REGISTERED_AT", note, region_line, f"question {question} registered_at must be a timezone-aware second-resolution timestamp")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", criteria_hash):
            add(diagnostics, "error", "E_G05_CRITERIA_HASH", note, region_line, f"question {question} has invalid criteria_hash")
        elif computed_hash and criteria_hash != computed_hash:
            add(diagnostics, "error", "E_G05_CRITERIA_HASH", note, region_line, f"question {question} criteria_hash does not match the normalized probe and criterion declaration")
        if not preregistration_matches(log_note, question, registered_at, criteria_hash):
            add(diagnostics, "error", "E_G05_PREREG_LOG", log_note or note, 1, f"question {question} has no matching active/proposed G0.5 preregistration in the decision log")

        result_rows = [
            row
            for row in table_records(sections["5"], "evidence_id")
            if not unfilled(row.get("探针 ID")) or not unfilled(row.get("evidence_id"))
        ]
        results_by_probe: dict[str, dict[str, str]] = {}
        for row in result_rows:
            probe_id = row.get("探针 ID", "").strip()
            if probe_id in results_by_probe:
                add(diagnostics, "error", "E_G05_RESULT_DUPLICATE", note, region_line, f"question {question} duplicates result for probe {probe_id!r}")
            results_by_probe[probe_id] = row
            if probe_statuses.get(probe_id) != "executed":
                add(diagnostics, "error", "E_G05_RESULT_SCOPE", note, region_line, f"question {question} result probe {probe_id!r} was not declared executed")
            missing_values = [field for field in G05_RESULT_VALUE_FIELDS if unfilled(row.get(field))]
            if unfilled(row.get("evidence_id")):
                missing_values.append("evidence_id")
            if missing_values:
                add(diagnostics, "error", "E_G05_RESULT_VALUES", note, region_line, f"question {question} probe {probe_id!r} has empty result fields: {', '.join(missing_values)}")

            artifact_raw = row.get("权威产物", "")
            manifest_raw = row.get("run manifest", "")
            artifact_path = resolve_output_reference(root, artifact_raw)
            manifest_path = resolve_output_reference(root, manifest_raw)
            if artifact_path is None or not artifact_path.is_file():
                add(diagnostics, "error", "E_G05_ARTIFACT", note, region_line, f"question {question} probe {probe_id!r} artifact must be an existing outputs/ file: {artifact_raw!r}")
            if manifest_path is None or not manifest_path.is_file():
                add(diagnostics, "error", "E_G05_MANIFEST", note, region_line, f"question {question} probe {probe_id!r} manifest must be an existing outputs/ file: {manifest_raw!r}")
            else:
                try:
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
                except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                    add(diagnostics, "error", "E_G05_MANIFEST", note, region_line, f"question {question} probe {probe_id!r} cannot read JSON manifest: {exc}")
                    manifest = None
                if not isinstance(manifest, dict):
                    if manifest is not None:
                        add(diagnostics, "error", "E_G05_MANIFEST", note, region_line, f"question {question} probe {probe_id!r} manifest must be a JSON object")
                else:
                    run_time = parse_zoned_timestamp(str(manifest.get("run_started_at", "")))
                    if run_time is None:
                        add(diagnostics, "error", "E_G05_RUN_TIME", note, region_line, f"question {question} probe {probe_id!r} manifest has invalid run_started_at")
                    elif registered_time is not None and registered_time >= run_time:
                        add(diagnostics, "error", "E_G05_PREREG_ORDER", note, region_line, f"question {question} probe {probe_id!r} was not started after preregistration")
                    if manifest.get("criteria_hash") != criteria_hash:
                        add(diagnostics, "error", "E_G05_MANIFEST_HASH", note, region_line, f"question {question} probe {probe_id!r} manifest criteria_hash differs from preregistration")
                    if unfilled(str(manifest.get("split_id", ""))):
                        add(diagnostics, "error", "E_G05_MANIFEST_SPLIT", note, region_line, f"question {question} probe {probe_id!r} manifest has no split_id")
                    manifest_probes = manifest.get("probe_ids", [manifest.get("probe_id")])
                    if not isinstance(manifest_probes, list) or probe_id not in [str(item) for item in manifest_probes]:
                        add(diagnostics, "error", "E_G05_MANIFEST_PROBE", note, region_line, f"question {question} probe {probe_id!r} is absent from manifest probe_ids")
                    if clean_output_reference(str(manifest.get("artifact", ""))) != clean_output_reference(artifact_raw):
                        add(diagnostics, "error", "E_G05_MANIFEST_ARTIFACT", note, region_line, f"question {question} probe {probe_id!r} manifest artifact differs from result row")
            evidence_rows.append((note, question, row, region_line))

        for probe_id, probe_status in probe_statuses.items():
            if probe_status == "executed" and probe_id not in results_by_probe:
                add(diagnostics, "error", "E_G05_RESULT_MISSING", note, region_line, f"question {question} executed probe {probe_id!r} has no diagnostic result")

        if route == "information_limited":
            audit_rows = table_records(sections["6"], "编号")
            audit = {row.get("编号", "").strip().split(" ", 1)[0]: row for row in audit_rows}
            failed = [key for key in ("E1", "E2", "E3", "E4") if audit.get(key, {}).get("结论", "").strip() != "否"]
            if failed:
                add(diagnostics, "error", "E_G05_INFORMATION_AUDIT", note, region_line, f"question {question} information_limited requires E1-E4 all equal 否; invalid: {', '.join(failed)}")

        if g1_status == "passed":
            unlocked_by = gate_value(g1, "unlocked_by") if g1 else None
            if unlocked_by != version:
                add(diagnostics, "error", "E_G05_UNLOCK_VERSION", note, g1.field_lines.get("unlocked_by", g1.line) if g1 else line, f"question {question} G1 unlocked_by must match G0.5 diagnosis_version")
        elif g1 and not null_value(gate_value(g1, "unlocked_by")):
            add(diagnostics, "error", "E_G05_UNLOCK_STATE", note, g1.field_lines.get("unlocked_by", g1.line), "G1 unlocked_by must be null unless G1 passed")

    duplicate_groups: dict[tuple[str, ...], list[tuple[Note, str, dict[str, str], int]]] = {}
    for item in evidence_rows:
        _, _, row, _ = item
        evidence_id = row.get("evidence_id", "").strip()
        if evidence_id:
            duplicate_groups.setdefault(("id", evidence_id), []).append(item)
        artifact_signature = (
            "artifact",
            clean_output_reference(row.get("权威产物", "")),
            row.get("主指标", "").strip(),
            row.get("关键辅助指标", "").strip(),
            row.get("相对基线差异", "").strip(),
        )
        duplicate_groups.setdefault(artifact_signature, []).append(item)

    reported: set[tuple[str, str, str]] = set()
    for key, items in duplicate_groups.items():
        questions = {item[1] for item in items}
        if len(questions) < 2:
            continue
        for note, question, row, line in items:
            marker = (question, key[0], "|".join(key[1:]))
            if marker in reported:
                continue
            reported.add(marker)
            missing = [field for field in ("共享生成机制", "本问适用理由", "反例风险") if unfilled(row.get(field))]
            if missing:
                add(diagnostics, "error", "E_G05_EVIDENCE_REUSE", note, line, f"question {question} reuses cross-question evidence without: {', '.join(missing)}")

    for route, items in routes.items():
        if route == "information_limited" or len(items) < 2:
            continue
        for note, question, line in items:
            add(diagnostics, "warning", "W_G05_ROUTE_REUSE", note, line, f"question {question} shares route {route!r} with another question; review independent support, do not reject by model name")


def validate_g0_audits(notes: list[Note], mode: str, diagnostics: list[Diagnostic]) -> None:
    gate_notes = {note.relative: parse_gate_records(note) for note in notes}
    for note, question, text, offset in question_content_blocks(notes, mode):
        records = gate_notes.get(note.relative, {}).get(question, {})
        g0 = records.get("G0")
        if not g0 or gate_value(g0, "status") != "passed":
            continue
        region = marked_region(text, G0_AUDIT_START, G0_AUDIT_END)
        if region is None:
            line = note.text[:offset].count("\n") + 1
            add(
                diagnostics,
                "warning",
                "W_LEGACY_G0_AUDIT",
                note,
                line,
                f"question {question} has G0=passed but no structured G0 audit; review before migration",
            )
            continue
        body, relative_start = region
        fields = two_column_fields(body)
        missing = [
            field
            for field in G0_AUDIT_FIELDS
            if unfilled(fields.get(field)) or fields.get(field, "").strip() == "待检查"
        ]
        if missing:
            absolute = offset + relative_start
            line = note.text[:absolute].count("\n") + 1
            add(
                diagnostics,
                "error",
                "E_G0_AUDIT",
                note,
                line,
                f"question {question} has G0=passed but incomplete audit fields: {', '.join(missing)}",
            )


def deliverable_registry(mode: str, note_map: dict[str, "Note"]) -> tuple[set[str], bool]:
    """Collect registered deliverable ids; the flag is False for legacy registries."""
    if mode == "full":
        note = note_map.get("交付物清单.md")
    else:
        note = note_map.get("02_问题分析卡.md")
        if note is not None and not re.search(r"^## 交付物清单\s*$", note.text, re.MULTILINE):
            note = None
    if note is None:
        return set(), False
    ids: set[str] = set()
    for _, title, fields in parse_item_entries(note):
        if "<" in title:
            continue
        value = fields.get("id", ("", 1, False))[0].strip()
        if value and not value.startswith("<"):
            ids.add(value)
    return ids, True


def table_rows(body: str, first_header: str) -> list[dict[str, str]]:
    rows = []
    for record in table_records(body, first_header):
        subject = record.get(first_header, "").strip()
        if subject and not subject.startswith("<"):
            rows.append(record)
    return rows


def validate_delivery_skeletons(
    notes: list[Note], mode: str, note_map: dict[str, Note], diagnostics: list[Diagnostic]
) -> None:
    gate_notes = {note.relative: parse_gate_records(note) for note in notes}
    ids, structured = deliverable_registry(mode, note_map)
    for note, question, text, offset in question_content_blocks(notes, mode):
        records = gate_notes.get(note.relative, {}).get(question, {})
        g0 = records.get("G0")
        g3 = records.get("G3")
        g0_passed = bool(g0) and gate_value(g0, "status") == "passed"
        g3_passed = bool(g3) and gate_value(g3, "status") == "passed"
        if not g0_passed and not g3_passed:
            continue

        region = marked_region(text, DELIVERY_SKELETON_START, DELIVERY_SKELETON_END)
        if region is None:
            add(
                diagnostics,
                "warning",
                "W_LEGACY_DELIVERY_SKELETON",
                note,
                note.text[:offset].count("\n") + 1,
                f"question {question} passed a gate but has no structured delivery skeleton; review before migration",
            )
        else:
            body, relative_start = region
            issues: list[str] = []
            rows = table_rows(body, "交付对象")
            if not rows:
                issues.append("no delivery object is defined before model selection")
            for row in rows:
                subject = row["交付对象"].strip()
                missing = [key for key in SKELETON_FIELDS if unfilled(row.get(key))]
                if missing:
                    issues.append(f"{subject}: missing {', '.join(missing)}")
                    continue
                if row.get("形态", "").strip() in SKELETON_FORMS_WITHOUT_ID:
                    continue
                item_id = row.get("对应交付物 ID", "").strip()
                if unfilled(item_id):
                    issues.append(f"{subject}: no deliverable id")
                elif structured and item_id not in ids:
                    issues.append(f"{subject}: deliverable id {item_id!r} is not registered")
            if issues:
                add(
                    diagnostics,
                    "error",
                    "E_DELIVERY_SKELETON",
                    note,
                    note.text[: offset + relative_start].count("\n") + 1,
                    f"question {question} passed a gate but " + "; ".join(issues),
                )

        if not g3_passed:
            continue
        trace = marked_region(text, REQUIREMENT_TRACE_START, REQUIREMENT_TRACE_END)
        if trace is None:
            add(
                diagnostics,
                "warning",
                "W_LEGACY_REQUIREMENT_TRACE",
                note,
                note.text[:offset].count("\n") + 1,
                f"question {question} has G3=passed but no structured requirement trace",
            )
            continue
        body, relative_start = trace
        issues = []
        rows = table_rows(body, "题面要求或动词")
        if not rows:
            issues.append("no requirement or verb is traced")
        for row in rows:
            subject = row["题面要求或动词"].strip()
            missing = [key for key in TRACE_FIELDS if unfilled(row.get(key))]
            if missing:
                issues.append(f"{subject}: missing {', '.join(missing)}")
            elif leading_status(row.get("状态"), ITEM_STATUSES) == TRACE_OPEN_STATUS:
                issues.append(f"{subject}: still planned")
        if issues:
            add(
                diagnostics,
                "error",
                "E_REQUIREMENT_TRACE",
                note,
                note.text[: offset + relative_start].count("\n") + 1,
                f"question {question} has G3=passed but " + "; ".join(issues),
            )


def validate_parameter_checks(notes: list[Note], mode: str, diagnostics: list[Diagnostic]) -> None:
    gate_notes = {note.relative: parse_gate_records(note) for note in notes}
    sensitive_values = {"是", "高", "敏感", "yes", "true"}
    for note, question, text, offset in question_content_blocks(notes, mode):
        records = gate_notes.get(note.relative, {}).get(question, {})
        g3 = records.get("G3")
        if not g3 or gate_value(g3, "status") != "passed":
            continue
        region = marked_region(text, PARAMETER_CHECK_START, PARAMETER_CHECK_END)
        if region is None:
            line = note.text[:offset].count("\n") + 1
            add(
                diagnostics,
                "warning",
                "W_LEGACY_PARAMETER_CHECK",
                note,
                line,
                f"question {question} has G3=passed but no structured parameter and corner check",
            )
            continue
        body, relative_start = region
        checks = bullet_fields(body)
        missing_checks = [
            key
            for key in ("参数敏感性自检", "角点与断点自检")
            if leading_status(checks.get(key), SELF_CHECK_STATUSES) not in SELF_CHECK_STATUSES
        ]
        high_risk: list[str] = []
        for record in table_records(body, "参数"):
            parameter = record.get("参数", "").strip()
            sensitive = record.get("最终答案是否敏感", "").strip().lower()
            if not parameter or parameter.startswith("<") or sensitive not in sensitive_values:
                continue
            if unfilled(record.get("已扰动范围")) or unfilled(record.get("证据")):
                high_risk.append(parameter)
        if missing_checks or high_risk:
            absolute = offset + relative_start
            line = note.text[:absolute].count("\n") + 1
            details: list[str] = []
            if missing_checks:
                details.append("unfinished checks: " + ", ".join(missing_checks))
            if high_risk:
                details.append("sensitive parameters without perturbation evidence: " + ", ".join(high_risk))
            add(
                diagnostics,
                "error",
                "E_PARAMETER_CHECK",
                note,
                line,
                f"question {question} has G3=passed but " + "; ".join(details),
            )


def validate_negative_closures(notes: list[Note], mode: str, diagnostics: list[Diagnostic]) -> None:
    gate_notes = {note.relative: parse_gate_records(note) for note in notes}
    for note, question, text, offset in question_content_blocks(notes, mode):
        records = gate_notes.get(note.relative, {}).get(question, {})
        g3 = records.get("G3")
        if not g3 or gate_value(g3, "status") != "passed":
            continue
        region = marked_region(text, NEGATIVE_CLOSURE_START, NEGATIVE_CLOSURE_END)
        if region is None:
            line = note.text[:offset].count("\n") + 1
            add(
                diagnostics,
                "warning",
                "W_LEGACY_NEGATIVE_CLOSURE",
                note,
                line,
                f"question {question} has G3=passed but no structured negative-result closure",
            )
            continue
        body, relative_start = region
        checks = bullet_fields(body)
        issues: list[str] = []
        if leading_status(checks.get("负结果闭环自检"), SELF_CHECK_STATUSES) not in SELF_CHECK_STATUSES:
            issues.append("negative-result self-check is unfinished")
        for record in table_records(body, "对象"):
            subject = record.get("对象", "").strip()
            if not subject or subject.startswith("<"):
                continue
            disposition = leading_status(record.get("闭环处置"), NEGATIVE_DISPOSITIONS)
            if disposition not in NEGATIVE_DISPOSITIONS:
                issues.append(f"{subject}: invalid disposition {disposition!r}")
                continue
            if disposition == "未解决":
                issues.append(f"{subject}: unresolved negative result blocks G3")
                continue
            missing = [
                key
                for key in ("负结果或淘汰证据", "最终回答/替代/适用范围", "证据")
                if unfilled(record.get(key))
            ]
            if missing:
                issues.append(f"{subject}: missing {', '.join(missing)}")
        if issues:
            absolute = offset + relative_start
            line = note.text[:absolute].count("\n") + 1
            add(
                diagnostics,
                "error",
                "E_NEGATIVE_CLOSURE",
                note,
                line,
                f"question {question} has G3=passed but " + "; ".join(issues),
            )


def budget_records(text: str) -> tuple[list[dict[str, str]], int] | None:
    region = marked_region(text, BUDGET_PLAN_START, BUDGET_PLAN_END)
    if region is None:
        return None
    body, relative_start = region
    records = [record for record in table_records(body, "工作 ID") if record.get("工作 ID", "").strip()]
    return records, relative_start


def no_exception(value: str | None) -> bool:
    return unfilled(value) or (value or "").strip() in {"—", "无", "不适用", "[]"}


def validate_budget_plans(notes: list[Note], mode: str, diagnostics: list[Diagnostic]) -> None:
    parsed: dict[str, list[dict[str, str]]] = {}
    locations: dict[str, tuple[Note, int]] = {}
    seen_ids: dict[str, tuple[Note, int]] = {}

    for note, question, text, offset in question_content_blocks(notes, mode):
        stage = scalar(note, "stage")
        result = budget_records(text)
        if result is None:
            if stage in STAGE_ORDER and STAGE_ORDER[stage] >= STAGE_ORDER["analysis"]:
                line = note.text[:offset].count("\n") + 1
                add(
                    diagnostics,
                    "warning",
                    "W_LEGACY_BUDGET_PLAN",
                    note,
                    line,
                    f"question {question} has no structured M1/M2/M3 plan",
                )
            continue
        records, relative_start = result
        absolute = offset + relative_start
        line = note.text[:absolute].count("\n") + 1
        parsed[question] = records
        locations[question] = (note, line)

        valid_m1 = 0
        for record in records:
            work_id = record.get("工作 ID", "").strip()
            work_item = record.get("工作项", "").strip()
            level = leading_status(record.get("级别"), BUDGET_LEVELS)
            status = leading_status(record.get("状态"), BUDGET_STATUSES)
            target = record.get("对应交付物/证据", "").strip()
            issues: list[str] = []
            if unfilled(work_item):
                issues.append("工作项")
            if level not in BUDGET_LEVELS:
                issues.append("级别")
            if status not in BUDGET_STATUSES:
                issues.append("状态")
            if unfilled(target):
                issues.append("对应交付物/证据")
            if issues:
                add(
                    diagnostics,
                    "error",
                    "E_BUDGET_FIELD",
                    note,
                    line,
                    f"question {question} work {work_id!r} has invalid or empty fields: {', '.join(issues)}",
                )
            if work_id in seen_ids:
                first_note, first_line = seen_ids[work_id]
                add(
                    diagnostics,
                    "error",
                    "E_BUDGET_ID_DUPLICATE",
                    note,
                    line,
                    f"duplicate work ID {work_id!r}; first declared at {first_note.relative}:{first_line}",
                )
            else:
                seen_ids[work_id] = (note, line)
            if level == "M1":
                valid_m1 += 1

        if stage in STAGE_ORDER and STAGE_ORDER[stage] >= STAGE_ORDER["analysis"] and valid_m1 == 0:
            add(
                diagnostics,
                "error",
                "E_M1_PLAN",
                note,
                line,
                f"question {question} reached {stage!r} without an M1 work plan",
            )

    all_questions = [question for _, question, _, _ in question_content_blocks(notes, mode)]
    m1_incomplete = False
    for question in all_questions:
        m1 = [
            record
            for record in parsed.get(question, [])
            if leading_status(record.get("级别"), BUDGET_LEVELS) == "M1"
        ]
        if not m1 or any(leading_status(record.get("状态"), BUDGET_STATUSES) != "done" for record in m1):
            m1_incomplete = True
            break
    if not m1_incomplete:
        return

    for question, records in parsed.items():
        note, line = locations[question]
        for record in records:
            level = leading_status(record.get("级别"), BUDGET_LEVELS)
            status = leading_status(record.get("状态"), BUDGET_STATUSES)
            if level not in {"M2", "M3"} or status not in {"in-progress", "done"}:
                continue
            if no_exception(record.get("例外决策")):
                add(
                    diagnostics,
                    "error",
                    "E_BUDGET_PRIORITY",
                    note,
                    line,
                    f"question {question} work {record.get('工作 ID', '').strip()!r} advances {level} while project M1 is incomplete and has no exception decision",
                )


def validate_stage_gates(
    note: Note,
    records: dict[str, GateRecord],
    stage: str | None,
    diagnostics: list[Diagnostic],
) -> None:
    if stage not in STAGE_ORDER:
        return
    requirements: list[str] = []
    if STAGE_ORDER[stage] >= STAGE_ORDER["analysis"]:
        requirements.append("G0")
    if STAGE_ORDER[stage] >= STAGE_ORDER["implementation"]:
        if "G0.5" in records:
            requirements.append("G0.5")
        requirements.append("G1")
    if stage == "writing":
        requirements.append("G3")
    for gate in requirements:
        record = records.get(gate)
        if record and gate_value(record, "status") != "passed":
            add(
                diagnostics,
                "error",
                "E_GATE_STAGE",
                note,
                record.field_lines.get("status", record.line),
                f"stage {stage!r} requires {gate}=passed",
            )


def validate_gates(notes: list[Note], mode: str, require_gates: bool, diagnostics: list[Diagnostic]) -> None:
    note_map = {note.relative: note for note in notes}
    overview = note_map.get("00_赛题总览.md")
    if overview:
        records = parse_gate_records(overview).get("global", {})
        if "gates" not in overview.frontmatter:
            missing_gate(overview, require_gates, diagnostics, "legacy context has no project gate GP")
        else:
            for gate in PROJECT_GATES:
                if gate not in records:
                    add(diagnostics, "error", "E_GATE_MISSING", overview, overview.field_lines.get("gates", 1), f"missing project gate: {gate}")
                else:
                    validate_gate_record(overview, records[gate], diagnostics)
            gp = records.get("GP")
            if gp and gate_value(gp, "status") != "passed":
                add(diagnostics, "error", "E_GP_REQUIRED", overview, gp.field_lines.get("status", gp.line), "initialized context requires GP=passed")

    if mode == "full":
        for note in notes:
            if not QUESTION_FILE_RE.match(note.path.name) or scalar(note, "status") == "superseded":
                continue
            question = scalar(note, "question") or ""
            records = parse_gate_records(note).get(question, {})
            if "gates" not in note.frontmatter:
                missing_gate(note, require_gates, diagnostics, "legacy question card has no G0-G3 records")
                continue
            for gate in QUESTION_GATES:
                if gate not in records:
                    if gate == "G0.5" and G05_DIAGNOSTIC_START not in note.text:
                        missing_gate(note, require_gates, diagnostics, "legacy question card has no G0.5 record")
                    else:
                        add(diagnostics, "error", "E_GATE_MISSING", note, note.field_lines.get("gates", 1), f"missing question gate: {gate}")
                else:
                    validate_gate_record(note, records[gate], diagnostics)
            validate_stage_gates(note, records, scalar(note, "stage"), diagnostics)
    else:
        note = note_map.get("02_问题分析卡.md")
        if not note:
            return
        nested = parse_gate_records(note)
        expected = question_sections(note)
        if "gates" not in note.frontmatter:
            missing_gate(note, require_gates, diagnostics, "legacy minimal question card has no per-question G0-G3 records")
            return
        for question in expected:
            records = nested.get(question, {})
            block = next((text for _, value, text, _ in question_content_blocks(notes, mode) if value == question), "")
            for gate in QUESTION_GATES:
                if gate not in records:
                    if gate == "G0.5" and G05_DIAGNOSTIC_START not in block:
                        missing_gate(note, require_gates, diagnostics, f"legacy question {question} has no G0.5 record")
                    else:
                        add(diagnostics, "error", "E_GATE_MISSING", note, note.field_lines.get("gates", 1), f"question {question} is missing gate: {gate}")
                else:
                    validate_gate_record(note, records[gate], diagnostics)
            validate_stage_gates(note, records, scalar(note, "stage"), diagnostics)
        extras = sorted(set(nested) - set(expected) - {"global"})
        for question in extras:
            add(diagnostics, "error", "E_GATE_QUESTION", note, note.field_lines.get("gates", 1), f"gate block has no matching question section: {question}")


def gate_summary_text(notes: list[Note], mode: str) -> str | None:
    if mode != "full":
        return None
    note_map = {note.relative: note for note in notes}
    overview = note_map.get("00_赛题总览.md")
    if not overview:
        return None
    gp = parse_gate_records(overview).get("global", {}).get("GP")
    if not gp:
        return None
    question_notes = sorted(
        (note for note in notes if QUESTION_FILE_RE.match(note.path.name) and scalar(note, "status") != "superseded"),
        key=lambda note: int(scalar(note, "question") or "0"),
    )
    if not question_notes:
        return None
    use_g05 = all(
        "G0.5" in parse_gate_records(note).get(scalar(note, "question") or "", {})
        for note in question_notes
    )
    if use_g05:
        rows = [
            "| 问题 | stage | GP | G0 | G0.5 | 路线 | 重构 | G1 | G2 | G3 | 当前阻塞 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    else:
        rows = [
            "| 问题 | stage | GP | G0 | G1 | G2 | G3 | 当前阻塞 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    for note in question_notes:
        question = scalar(note, "question") or ""
        records = parse_gate_records(note).get(question, {})
        expected_gates = QUESTION_GATES if use_g05 else tuple(gate for gate in QUESTION_GATES if gate != "G0.5")
        if any(gate not in records for gate in expected_gates):
            return None
        blockers = [
            f"{gate}: {gate_value(records[gate], 'blocker')}"
            for gate in expected_gates
            if gate_value(records[gate], "status") == "blocked" and not null_value(gate_value(records[gate], "blocker"))
        ]
        blocker = "；".join(blockers) if blockers else "—"
        blocker = blocker.replace("|", "\\|").replace("\n", " ")
        if use_g05:
            g05 = records["G0.5"]
            route = gate_value(g05, "route")
            reformulation = gate_value(g05, "reformulation")
            statuses = [
                gate_value(records["G0"], "status") or "?",
                gate_value(g05, "status") or "?",
                "—" if null_value(route) else route or "—",
                "—" if null_value(reformulation) else reformulation or "—",
                gate_value(records["G1"], "status") or "?",
                gate_value(records["G2"], "status") or "?",
                gate_value(records["G3"], "status") or "?",
            ]
        else:
            statuses = [gate_value(records[gate], "status") or "?" for gate in expected_gates]
        rows.append(f"| {question} | {scalar(note, 'stage') or '?'} | {gate_value(gp, 'status') or '?'} | " + " | ".join(statuses) + f" | {blocker} |")
    return "\n".join(rows)


def budget_summary_text(notes: list[Note], mode: str) -> str | None:
    if mode != "full":
        return None
    blocks = sorted(question_content_blocks(notes, mode), key=lambda item: int(item[1]))
    if not blocks:
        return None
    rows = [
        "| 问题 | M1 完成 | M2 已推进 | M3 已推进 | 当前预算阻塞 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for _, question, text, _ in blocks:
        result = budget_records(text)
        records = result[0] if result else []
        m1 = [record for record in records if leading_status(record.get("级别"), BUDGET_LEVELS) == "M1"]
        m1_done = sum(leading_status(record.get("状态"), BUDGET_STATUSES) == "done" for record in m1)
        progressed = {
            level: sum(
                leading_status(record.get("级别"), BUDGET_LEVELS) == level
                and leading_status(record.get("状态"), BUDGET_STATUSES) in {"in-progress", "done"}
                for record in records
            )
            for level in ("M2", "M3")
        }
        if not m1:
            m1_text = "未登记"
            blocker = "M1 未登记"
        else:
            m1_text = f"{m1_done}/{len(m1)}"
            blocker = "—" if m1_done == len(m1) else f"M1 {len(m1) - m1_done} 项未完成"
        rows.append(f"| {question} | {m1_text} | {progressed['M2']} | {progressed['M3']} | {blocker} |")
    return "\n".join(rows)


def summary_region(
    note: Note,
    start_marker: str = GATE_SUMMARY_START,
    end_marker: str = GATE_SUMMARY_END,
) -> tuple[int, int] | None:
    try:
        start = note.lines.index(start_marker)
        end = note.lines.index(end_marker)
    except ValueError:
        return None
    return (start, end) if start < end else None


def validate_gate_summary(notes: list[Note], mode: str, diagnostics: list[Diagnostic]) -> None:
    if mode != "full":
        return
    note = next((item for item in notes if item.relative == "项目设计总览.md"), None)
    if not note:
        return
    region = summary_region(note)
    if not region:
        add(diagnostics, "warning", "W_GATE_SUMMARY_MISSING", note, 1, "legacy project overview has no derived gate-summary markers")
        return
    expected = gate_summary_text(notes, mode)
    if expected is None:
        return
    start, end = region
    actual = "\n".join(note.lines[start + 1 : end]).strip()
    if actual != expected:
        add(diagnostics, "error", "E_GATE_SUMMARY_STALE", note, start + 1, "derived gate table is stale; run with --write-summary")


def validate_budget_summary(notes: list[Note], mode: str, diagnostics: list[Diagnostic]) -> None:
    if mode != "full":
        return
    note = next((item for item in notes if item.relative == "项目设计总览.md"), None)
    if not note:
        return
    region = summary_region(note, BUDGET_SUMMARY_START, BUDGET_SUMMARY_END)
    if not region:
        add(diagnostics, "warning", "W_BUDGET_SUMMARY_MISSING", note, 1, "legacy project overview has no derived budget-summary markers")
        return
    expected = budget_summary_text(notes, mode)
    if expected is None:
        return
    start, end = region
    actual = "\n".join(note.lines[start + 1 : end]).strip()
    if actual != expected:
        add(diagnostics, "error", "E_BUDGET_SUMMARY_STALE", note, start + 1, "derived budget table is stale; run with --write-summary")


def write_gate_summary(root: Path, mode: str | None, notes: list[Note]) -> tuple[bool, list[Diagnostic]]:
    diagnostics: list[Diagnostic] = []
    if mode != "full":
        diagnostics.append(Diagnostic("error", "E_GATE_SUMMARY_MODE", ".", 1, "--write-summary is available only for full mode"))
        return False, diagnostics
    note = next((item for item in notes if item.relative == "项目设计总览.md"), None)
    if not note:
        diagnostics.append(Diagnostic("error", "E_GATE_SUMMARY_FILE", "项目设计总览.md", 1, "project overview is missing"))
        return False, diagnostics
    gate_region = summary_region(note)
    if not gate_region:
        add(diagnostics, "error", "E_GATE_SUMMARY_MARKER", note, 1, "derived gate-summary markers are missing")
        return False, diagnostics
    gate_summary = gate_summary_text(notes, mode)
    if gate_summary is None:
        add(diagnostics, "error", "E_GATE_SUMMARY_DATA", note, 1, "cannot derive summary until GP and all question gates exist")
        return False, diagnostics
    replacements = [(gate_region, gate_summary)]
    budget_region = summary_region(note, BUDGET_SUMMARY_START, BUDGET_SUMMARY_END)
    budget_summary = budget_summary_text(notes, mode)
    if budget_region and budget_summary is not None:
        replacements.append((budget_region, budget_summary))
    new_lines = list(note.lines)
    for (start, end), summary in sorted(replacements, key=lambda item: item[0][0], reverse=True):
        new_lines = new_lines[: start + 1] + summary.splitlines() + new_lines[end:]
    new_text = "\n".join(new_lines).rstrip() + "\n"
    if new_text == note.text.replace("\r\n", "\n"):
        return False, diagnostics
    (root / note.relative).write_text(new_text, encoding="utf-8")
    return True, diagnostics


def note_aliases(notes: Iterable[Note]) -> set[str]:
    aliases: set[str] = set()
    for note in notes:
        relative = Path(note.relative)
        without_suffix = relative.with_suffix("").as_posix()
        aliases.add(without_suffix)
        aliases.add(relative.stem)
    return aliases


def normalize_link(raw: str) -> str:
    target = raw.split("|", 1)[0].split("#", 1)[0].strip().replace("\\", "/")
    return target[:-3] if target.lower().endswith(".md") else target


def validate_dependencies_and_links(notes: list[Note], diagnostics: list[Diagnostic]) -> None:
    aliases = note_aliases(notes)
    for note in notes:
        dependencies = note.frontmatter.get("depends_on", [])
        if isinstance(dependencies, list):
            for dependency in dependencies:
                normalized = normalize_link(dependency)
                if normalized and normalized not in aliases:
                    add(diagnostics, "error", "E_DEPENDENCY", note, note.field_lines.get("depends_on", 1), f"depends_on target does not exist: {dependency}")

        for line_number, line in enumerate(note.lines, 1):
            for raw in WIKILINK_RE.findall(line):
                normalized = normalize_link(raw)
                if not normalized or normalized in aliases:
                    continue
                if "N_" in normalized or normalized.startswith("文献库/"):
                    severity = "warning"
                    code = "W_PLANNED_LINK"
                else:
                    severity = "warning"
                    code = "W_LINK_MISSING"
                add(diagnostics, severity, code, note, line_number, f"wikilink target was not found in context: {raw}")


def validate_global_stage(notes: list[Note], mode: str, diagnostics: list[Diagnostic]) -> None:
    if mode != "full":
        return
    questions = [note for note in notes if QUESTION_FILE_RE.match(note.path.name) and scalar(note, "status") != "superseded"]
    stages = [scalar(note, "stage") for note in questions]
    if not stages or any(stage not in STAGE_ORDER for stage in stages):
        return
    expected = min(stages, key=lambda value: STAGE_ORDER[value])  # type: ignore[index]
    for note in notes:
        if scalar(note, "question") == "global" and scalar(note, "status") != "superseded":
            actual = scalar(note, "stage")
            if actual in STAGE_ORDER and actual != expected:
                add(
                    diagnostics,
                    "error",
                    "E_GLOBAL_STAGE",
                    note,
                    note.field_lines.get("stage", 1),
                    f"global stage must equal the lowest question stage {expected!r}, found {actual!r}",
                )


def unfilled(value: str | None) -> bool:
    if value is None or not value.strip():
        return True
    stripped = value.strip()
    return (stripped.startswith("<") and stripped.endswith(">")) or stripped in {"TBD", "待填"}


def parse_item_entries(note: Note) -> list[tuple[int, str, dict[str, tuple[str, int, bool]]]]:
    entries: list[tuple[int, str, dict[str, tuple[str, int, bool]]]] = []
    index = 0
    while index < len(note.lines):
        header = re.match(r"^###\s+(.+?)\s*$", note.lines[index])
        if not header:
            index += 1
            continue
        title = header.group(1)
        start = index
        index += 1
        fields: dict[str, tuple[str, int, bool]] = {}
        current_key: str | None = None
        while index < len(note.lines) and not re.match(r"^#{2,3}\s+", note.lines[index]):
            line = note.lines[index]
            field = re.match(r"^-\s+([^:]+):\s*(.*)$", line)
            if field:
                current_key = field.group(1).strip().strip("`")
                fields[current_key] = (field.group(2).strip(), index + 1, False)
            elif current_key and re.match(r"^\s{2,}-\s+\S", line):
                value, field_line, _ = fields[current_key]
                fields[current_key] = (value, field_line, True)
            index += 1
        if "status" in fields:
            entries.append((start + 1, title, fields))
    return entries


def validate_legacy_full_figures(note: Note, diagnostics: list[Diagnostic]) -> None:
    for header_line, title, fields in parse_item_entries(note):
        status_info = fields.get("status")
        if not status_info:
            continue
        status, status_line, _ = status_info
        if status not in ITEM_STATUSES:
            add(diagnostics, "error", "E_ITEM_STATUS", note, status_line, f"invalid figure item status: {status!r}")
            continue
        example = "<" in title or any("<" in value and ">" in value for value, _, _ in fields.values())
        if example:
            add(diagnostics, "warning", "W_EXAMPLE_ENTRY", note, header_line, "example figure entry remains; delete it when real entries are created")
            continue
        if status == "superseded":
            continue
        required = ["question", "claim"]
        if status in {"drafted", "active"}:
            required += ["label", "claim_source", "caption", "panels", "supersedes", "出图与引用"]
        if status == "active":
            required += ["口径核验", "产物回看"]
        for key in required:
            value, line, has_nested = fields.get(key, ("", header_line, False))
            filled = has_nested or (key == "supersedes" and value == "[]") or not unfilled(value)
            if not filled:
                add(diagnostics, "error", "E_ITEM_FIELD", note, line, f"{status} figure item is missing field: {key}")


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def validate_legacy_minimal_figures(note: Note, diagnostics: list[Diagnostic]) -> None:
    for line_number, line in enumerate(note.lines, 1):
        if not line.lstrip().startswith("|"):
            continue
        cells = split_table_row(line)
        if len(cells) < 10 or cells[0] in {"条目", "---", ""}:
            continue
        status = cells[1]
        if status not in ITEM_STATUSES:
            add(diagnostics, "error", "E_ITEM_STATUS", note, line_number, f"invalid figure item status: {status!r}")
            continue
        if status == "superseded":
            continue
        indexes = [3, 4]
        if status in {"drafted", "active"}:
            indexes += [2, 5, 6, 7]
        if status == "active":
            indexes += [8, 9]
        for index in indexes:
            if index >= len(cells) or unfilled(cells[index]):
                add(diagnostics, "error", "E_ITEM_FIELD", note, line_number, f"{status} figure table row has an empty required column")
                break


def field_filled(
    fields: dict[str, tuple[str, int, bool]],
    key: str,
    allow_empty_list: bool = False,
    default_line: int = 1,
) -> tuple[bool, int]:
    value, line, has_nested = fields.get(key, ("", default_line, False))
    if has_nested:
        return True, line
    if allow_empty_list and value == "[]":
        return True, line
    return not unfilled(value) and value != "[]", line


def validate_deliverable_entries(note: Note, diagnostics: list[Diagnostic]) -> None:
    seen_ids: dict[str, int] = {}
    kind_drafted = {
        "figure": ("panels", "caption"),
        "table": ("columns", "units", "precision", "missing"),
        "rule": ("inputs", "output", "boundaries", "exceptions"),
        "threshold": ("inputs", "output", "boundaries", "exceptions"),
        "schedule": ("feasible_region", "time_unit", "conflicts"),
        "plan": ("feasible_region", "time_unit", "conflicts"),
    }
    kind_active = {
        "figure": ("口径核验", "产物回看"),
        "table": ("render_review",),
        "rule": ("executable_check",),
        "threshold": ("executable_check",),
        "schedule": ("execution_precision",),
        "plan": ("execution_precision",),
    }
    for header_line, title, fields in parse_item_entries(note):
        example = "<" in title or any("<" in value and ">" in value for value, _, _ in fields.values())
        if example:
            add(
                diagnostics,
                "warning",
                "W_EXAMPLE_ENTRY",
                note,
                header_line,
                "example deliverable entry remains; delete it when real entries are created",
            )
            continue

        raw_status, status_line, _ = fields.get("status", ("", header_line, False))
        status = leading_status(raw_status, ITEM_STATUSES)
        if status not in ITEM_STATUSES:
            add(diagnostics, "error", "E_ITEM_STATUS", note, status_line, f"invalid deliverable status: {raw_status!r}")
            continue
        if status == "superseded":
            continue

        common = ["id", "kind", "question", "claim"]
        if status in {"drafted", "active"}:
            common += ["label", "claim_source", "source", "artifact", "acceptance", "supersedes"]
        for key in common:
            filled, line = field_filled(
                fields, key, allow_empty_list=key == "supersedes", default_line=header_line
            )
            if not filled:
                add(
                    diagnostics,
                    "error",
                    "E_ITEM_FIELD",
                    note,
                    line or header_line,
                    f"{status} deliverable is missing field: {key}",
                )

        item_id, id_line, _ = fields.get("id", ("", header_line, False))
        if item_id:
            if item_id in seen_ids:
                add(
                    diagnostics,
                    "error",
                    "E_ITEM_ID_DUPLICATE",
                    note,
                    id_line,
                    f"duplicate deliverable id {item_id!r}; first declared at line {seen_ids[item_id]}",
                )
            else:
                seen_ids[item_id] = id_line

        raw_kind, kind_line, _ = fields.get("kind", ("", header_line, False))
        kind = leading_status(raw_kind, DELIVERABLE_KINDS)
        if kind not in DELIVERABLE_KINDS:
            add(diagnostics, "error", "E_ITEM_KIND", note, kind_line, f"invalid deliverable kind: {raw_kind!r}")
            continue
        question, question_line, _ = fields.get("question", ("", header_line, False))
        if question != "global" and not question.isdigit():
            add(
                diagnostics,
                "error",
                "E_ITEM_QUESTION",
                note,
                question_line,
                f"invalid deliverable question: {question!r}; use a number or 'global'",
            )
        if status in {"drafted", "active"}:
            for key in kind_drafted[kind]:
                filled, line = field_filled(fields, key, default_line=header_line)
                if not filled:
                    add(
                        diagnostics,
                        "error",
                        "E_ITEM_KIND_FIELD",
                        note,
                        line or header_line,
                        f"{status} {kind} deliverable is missing field: {key}",
                    )
        if status == "active":
            for key in kind_active[kind]:
                filled, line = field_filled(fields, key, default_line=header_line)
                if not filled:
                    add(
                        diagnostics,
                        "error",
                        "E_ITEM_KIND_FIELD",
                        note,
                        line or header_line,
                        f"active {kind} deliverable is missing field: {key}",
                    )


def validate_deliverables(root: Path, mode: str, note_map: dict[str, Note], diagnostics: list[Diagnostic]) -> None:
    if mode == "full":
        current = note_map.get("交付物清单.md")
        legacy = note_map.get("图表清单.md")
        if current:
            validate_deliverable_entries(current, diagnostics)
        elif legacy:
            add(
                diagnostics,
                "warning",
                "W_LEGACY_DELIVERABLES",
                legacy,
                1,
                "legacy 图表清单.md is supported; run preview_modeling_upgrade.py --deliverables before migration",
            )
            validate_legacy_full_figures(legacy, diagnostics)
        return

    note = note_map.get("02_问题分析卡.md")
    if not note:
        return
    if re.search(r"^## 交付物清单\s*$", note.text, re.MULTILINE):
        validate_deliverable_entries(note, diagnostics)
    elif re.search(r"^## 图表清单\s*$", note.text, re.MULTILINE):
        add(
            diagnostics,
            "warning",
            "W_LEGACY_DELIVERABLES",
            note,
            1,
            "legacy minimal figure table is supported; preview deliverable migration before upgrading",
        )
        validate_legacy_minimal_figures(note, diagnostics)
    else:
        add(diagnostics, "error", "E_DELIVERABLE_REGISTRY", note, 1, "minimal context has no deliverable registry")


def run(root: Path, requested_mode: str, require_gates: bool = False) -> tuple[str | None, list[Diagnostic], list[Note]]:
    diagnostics: list[Diagnostic] = []
    if not root.is_dir():
        return None, [Diagnostic("error", "E_CONTEXT_DIR", ".", 1, f"context directory does not exist: {root}")], []

    mode = detect_mode(root, requested_mode, diagnostics)
    if mode:
        validate_required_files(root, mode, diagnostics)

    notes: list[Note] = []
    for path in sorted(root.glob("*.md")):
        note, note_diagnostics = parse_frontmatter(path, root)
        diagnostics.extend(note_diagnostics)
        if note:
            notes.append(note)
            validate_note(note, diagnostics)

    validate_dependencies_and_links(notes, diagnostics)
    if mode:
        validate_global_stage(notes, mode, diagnostics)
        validate_deliverables(root, mode, {note.relative: note for note in notes}, diagnostics)
        validate_gates(notes, mode, require_gates, diagnostics)
        validate_g0_audits(notes, mode, diagnostics)
        validate_g0_5(root, notes, mode, diagnostics)
        validate_delivery_skeletons(notes, mode, {note.relative: note for note in notes}, diagnostics)
        validate_parameter_checks(notes, mode, diagnostics)
        validate_negative_closures(notes, mode, diagnostics)
        validate_budget_plans(notes, mode, diagnostics)
        validate_gate_summary(notes, mode, diagnostics)
        validate_budget_summary(notes, mode, diagnostics)
    return mode, diagnostics, notes


def main() -> int:
    args = parse_args()
    root = args.context.resolve()
    mode, diagnostics, notes = run(root, args.mode, args.require_gates)
    summary_updated = False
    if args.write_summary:
        summary_updated, write_diagnostics = write_gate_summary(root, mode, notes)
        if not any(item.severity == "error" for item in write_diagnostics):
            mode, diagnostics, notes = run(root, args.mode, args.require_gates)
        diagnostics.extend(write_diagnostics)
    diagnostics.sort(key=lambda item: (item.path, item.line, item.severity, item.code))
    errors = sum(item.severity == "error" for item in diagnostics)
    warnings = sum(item.severity == "warning" for item in diagnostics)

    if args.json:
        print(
            json.dumps(
                {
                    "context": str(root),
                    "mode": mode,
                    "notes": len(notes),
                    "errors": errors,
                    "warnings": warnings,
                    "summary_updated": summary_updated,
                    "diagnostics": [asdict(item) for item in diagnostics],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for item in diagnostics:
            print(f"{item.severity.upper()} {item.code} {item.path}:{item.line} {item.message}")
        result = "PASS" if errors == 0 else "FAIL"
        print(f"{result}: mode={mode or 'unknown'} notes={len(notes)} errors={errors} warnings={warnings}")
        if args.write_summary:
            print("Project summaries: " + ("updated" if summary_updated else "unchanged"))

    if errors or (args.strict_warnings and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
