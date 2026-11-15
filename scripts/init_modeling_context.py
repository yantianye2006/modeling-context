#!/usr/bin/env python3
"""Initialize a traceable Obsidian context for a mathematical-modeling project."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path


GROUP_RE = re.compile(r"^<!-- modeling-start:group (\{.*\}) -->$")
SECTION_RE = re.compile(r"^<!-- modeling-start:section (\{.*\}) -->$")
SECTION_END = "<!-- modeling-start:endsection -->"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create full or minimal Obsidian modeling notes without overwriting by default."
    )
    parser.add_argument("--output", required=True, type=Path, help="Destination modeling directory")
    parser.add_argument(
        "--questions", required=True, type=int, help="Number of explicitly numbered top-level questions"
    )
    parser.add_argument(
        "--input-evidence",
        required=True,
        action="append",
        help="Evidence that the input-understanding gate passed; repeat for multiple files, pages, sheets, or records",
    )
    parser.add_argument("--minimal", action="store_true", help="Create the four-file minimal structure")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing generated filenames; use only with explicit user approval",
    )
    parser.add_argument("--dry-run", action="store_true", help="List intended actions without writing")
    return parser.parse_args()


def render(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def question_rows(count: int) -> str:
    return "\n".join(f"| 问题 {i} |  |  |  |  |" for i in range(1, count + 1))


def question_graph(count: int) -> str:
    # Create nodes only. Dependencies must come from the problem statement, not guesses.
    return "\n".join(f'    Q{i}["问题{i}"]' for i in range(1, count + 1))


def question_model_rows(count: int) -> str:
    return "\n".join(f"| 问题 {i} |  |  |  |  | 待验证 |" for i in range(1, count + 1))


def gate_fields(
    indent: int,
    status: str = "not-checked",
    checked_at: str = "null",
    evidence: list[str] | None = None,
    extra_fields: dict[str, str] | None = None,
) -> str:
    prefix = " " * indent
    evidence = evidence or []
    lines = [
        f"{prefix}status: {status}",
        f"{prefix}checked_at: {checked_at}",
        f"{prefix}blocker: null",
        f"{prefix}waiver_reason: null",
    ]
    if evidence:
        lines.append(f"{prefix}evidence:")
        lines.extend(f"{prefix}  - {json.dumps(item, ensure_ascii=False)}" for item in evidence)
    else:
        lines.append(f"{prefix}evidence: []")
    for key, value in (extra_fields or {}).items():
        lines.append(f"{prefix}{key}: {value}")
    return "\n".join(lines)


def project_gate_block(today: str, input_evidence: list[str]) -> str:
    return "\n".join(("  GP:", gate_fields(4, "passed", today, input_evidence)))


def question_gate_block(indent: int = 2) -> str:
    blocks: list[str] = []
    gates = (
        ("G0", None),
        (
            "G0.5",
            {
                "route": "null",
                "reformulation": "null",
                "diagnosis_version": "null",
            },
        ),
        ("G1", {"unlocked_by": "null"}),
        ("G2", None),
        ("G3", None),
    )
    for gate, extra_fields in gates:
        blocks.append(
            f"{' ' * indent}{gate}:\n"
            + gate_fields(indent + 2, extra_fields=extra_fields)
        )
    return "\n".join(blocks)


def minimal_question_gate_blocks(count: int) -> str:
    return "\n".join(
        f'  "{number}":\n{question_gate_block(4)}' for number in range(1, count + 1)
    )


def gate_summary(count: int) -> str:
    header = (
        "| 问题 | stage | GP | G0 | G0.5 | 路线 | 重构 | G1 | G2 | G3 | 当前阻塞 |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    )
    rows = "\n".join(
        f"| {number} | problem-framing | passed | not-checked | not-checked | — | — | not-checked | not-checked | not-checked | — |"
        for number in range(1, count + 1)
    )
    return f"{header}\n{rows}"


def budget_summary(count: int) -> str:
    header = (
        "| 问题 | M1 完成 | M2 已推进 | M3 已推进 | 当前预算阻塞 |\n"
        "| --- | --- | --- | --- | --- |"
    )
    rows = "\n".join(
        f"| {number} | 未登记 | 0 | 0 | M1 未登记 |" for number in range(1, count + 1)
    )
    return f"{header}\n{rows}"


def load_shared_sections(path: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    groups: list[dict[str, str]] = []
    sections: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    body: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        group = GROUP_RE.match(line)
        section = SECTION_RE.match(line)
        if group:
            if current is not None:
                raise ValueError(f"{path}:{line_number}: group marker inside section")
            groups.append(json.loads(group.group(1)))
        elif section:
            if current is not None:
                raise ValueError(f"{path}:{line_number}: nested section marker")
            current = json.loads(section.group(1))
            body = []
        elif line == SECTION_END:
            if current is None:
                raise ValueError(f"{path}:{line_number}: unmatched section end")
            current["body"] = "\n".join(body).strip()
            sections.append(current)
            current = None
            body = []
        elif current is not None:
            body.append(line)
    if current is not None:
        raise ValueError(f"{path}: unclosed section {current.get('id', '<unknown>')}")

    group_ids = [group["id"] for group in groups]
    section_ids = [section["id"] for section in sections]
    if len(group_ids) != len(set(group_ids)) or len(section_ids) != len(set(section_ids)):
        raise ValueError(f"{path}: duplicate group or section id")
    unknown_groups = sorted({section["minimal_group"] for section in sections} - set(group_ids))
    if unknown_groups:
        raise ValueError(f"{path}: unknown minimal groups: {', '.join(unknown_groups)}")
    return groups, sections


def shift_headings(text: str, levels: int) -> str:
    def replace(match: re.Match[str]) -> str:
        return "#" * min(6, len(match.group(1)) + levels) + match.group(2)

    return re.sub(r"^(#{1,6})(\s+.*)$", replace, text, flags=re.MULTILINE)


def section_marker(section_id: str, boundary: str) -> str:
    return f"<!-- modeling-start:section:{section_id}:{boundary} -->"


def render_full_sections(sections: list[dict[str, str]]) -> str:
    blocks: list[str] = []
    for section in sections:
        block = [
            section_marker(section["id"], "start"),
            f'## {section["full_title"]}',
        ]
        if section["body"]:
            block.extend(("", section["body"]))
        block.extend(("", section_marker(section["id"], "end")))
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)


def render_minimal_sections(groups: list[dict[str, str]], sections: list[dict[str, str]]) -> str:
    blocks: list[str] = []
    for group in groups:
        group_sections = [section for section in sections if section["minimal_group"] == group["id"]]
        group_block = [f'### {group["title"]}']
        for section in group_sections:
            section_block = [section_marker(section["id"], "start")]
            if section["minimal"] == "include":
                section_block.extend((f'#### {section["minimal_title"]}', ""))
                if section["body"]:
                    section_block.append(shift_headings(section["body"], 2))
            elif section["minimal"] == "anchor":
                section_block.append("<!-- 本节在 minimal 模式省略正文；升级时按稳定 ID 映射。 -->")
            else:
                raise ValueError(f"invalid minimal mode for section {section['id']}: {section['minimal']}")
            section_block.append(section_marker(section["id"], "end"))
            group_block.extend(("", "\n".join(section_block)))
        blocks.append("\n".join(group_block))
    return "\n\n".join(blocks)


def repeated_template(count: int, template: str, extra_values: dict[str, str] | None = None) -> str:
    extra_values = extra_values or {}
    return "\n\n".join(
        render(template, {**extra_values, "question": str(number)}).rstrip()
        for number in range(1, count + 1)
    )


def write_file(path: Path, content: str, overwrite: bool, dry_run: bool) -> str:
    if path.exists() and not overwrite:
        return f"SKIP  {path} (exists)"
    action = "WRITE" if path.exists() else "CREATE"
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return f"{action:<6} {path}"


def main() -> int:
    args = parse_args()
    if args.questions < 1:
        raise SystemExit("--questions must be at least 1")

    skill_dir = Path(__file__).resolve().parents[1]
    template_mode = "minimal" if args.minimal else "full"
    template_dir = skill_dir / "assets" / "templates" / template_mode
    shared_dir = skill_dir / "assets" / "templates" / "shared"
    if not template_dir.is_dir():
        raise SystemExit(f"Template directory is missing: {template_dir}")

    groups, sections = load_shared_sections(shared_dir / "question-sections.md")
    full_question_sections = render_full_sections(sections)
    minimal_sections = render_minimal_sections(groups, sections)
    minimal_wrapper = (shared_dir / "minimal-question-wrapper.md").read_text(encoding="utf-8")
    deep_learning_wrapper = (shared_dir / "deep-learning-question-wrapper.md").read_text(encoding="utf-8")

    today = date.today().isoformat()
    values = {
        "updated": today,
        "question_rows": question_rows(args.questions),
        "question_graph": question_graph(args.questions),
        "question_model_rows": question_model_rows(args.questions),
        "project_gate_block": project_gate_block(today, args.input_evidence),
        "question_gate_block": question_gate_block(),
        "question_gate_blocks": minimal_question_gate_blocks(args.questions),
        "gate_summary": gate_summary(args.questions),
        "budget_summary": budget_summary(args.questions),
        "full_question_sections": full_question_sections,
        "question_sections": repeated_template(
            args.questions, minimal_wrapper, {"minimal_sections": minimal_sections}
        ),
        "deep_learning_question_sections": repeated_template(args.questions, deep_learning_wrapper),
    }

    actions: list[str] = []
    for template in sorted(template_dir.glob("*.md")):
        if not args.minimal and template.name == "问题N_分析卡.md":
            continue
        content = render(template.read_text(encoding="utf-8"), values)
        actions.append(write_file(args.output / template.name, content, args.overwrite, args.dry_run))

    if not args.minimal:
        question_template = (template_dir / "问题N_分析卡.md").read_text(encoding="utf-8")
        for number in range(1, args.questions + 1):
            content = render(question_template, {**values, "question": str(number)})
            filename = f"问题{number}_分析卡.md"
            actions.append(write_file(args.output / filename, content, args.overwrite, args.dry_run))

    print(f"Mode: {template_mode}; questions: {args.questions}; output: {args.output}")
    for action in actions:
        print(action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
