#!/usr/bin/env python3
"""Preview modeling-start context upgrades without writing any file."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from init_modeling_context import load_shared_sections


QUESTION_RE = re.compile(r"^## 问题\s+(\d+)\s*$", re.MULTILINE)
QUESTION_MARKER_RE = re.compile(r"<!-- modeling-start:question:(\d+):start -->")
SECTION_MARKER_RE = re.compile(r"<!-- modeling-start:section:([a-z0-9-]+):start -->")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview minimal-to-full and legacy-deliverable migrations; never writes files."
    )
    parser.add_argument("--context", required=True, type=Path, help="Existing modeling context directory")
    parser.add_argument("--to-full", action="store_true", help="Preview minimal-to-full expansion")
    parser.add_argument(
        "--deliverables",
        action="store_true",
        help="Preview 图表清单.md to 交付物清单.md migration and link updates",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser.parse_args()


def detect_mode(root: Path) -> str:
    has_full = (root / "01_数据理解.md").is_file() or any(root.glob("问题*_分析卡.md"))
    has_minimal = (root / "01_数据与口径.md").is_file()
    if has_full and has_minimal:
        return "ambiguous"
    if has_full:
        return "full"
    if has_minimal:
        return "minimal"
    return "unknown"


def deliverable_preview(root: Path, mode: str) -> tuple[list[dict[str, object]], list[str]]:
    actions: list[dict[str, object]] = []
    warnings: list[str] = []
    legacy = root / "图表清单.md"
    current = root / "交付物清单.md"
    if legacy.is_file() and current.is_file():
        warnings.append("图表清单.md 与 交付物清单.md 同时存在；必须人工消解，不能自动合并。")
    elif legacy.is_file():
        linked_files: list[str] = []
        for path in sorted(root.glob("*.md")):
            if path == legacy:
                continue
            text = path.read_text(encoding="utf-8-sig")
            if "图表清单" in text:
                linked_files.append(path.name)
        actions.append(
            {
                "action": "rename-with-schema-migration",
                "source": legacy.name,
                "target": current.name,
                "link_updates": linked_files,
                "note": "先把旧 figure 条目映射为 kind: figure，再更新链接；预览不写文件。",
            }
        )
    elif current.is_file():
        actions.append({"action": "none", "target": current.name, "note": "已使用通用交付物清单。"})
    elif mode == "minimal":
        card = root / "02_问题分析卡.md"
        text = card.read_text(encoding="utf-8-sig") if card.is_file() else ""
        heading = "交付物清单" if "## 交付物清单" in text else "图表清单" if "## 图表清单" in text else None
        actions.append(
            {
                "action": "extract-on-full-upgrade",
                "source": f"02_问题分析卡.md#{heading}" if heading else "02_问题分析卡.md",
                "target": "交付物清单.md",
                "note": "minimal 原文件保留；升级目标在独立目录生成，不能覆盖源文件。",
            }
        )
        if heading == "图表清单":
            warnings.append("minimal 使用旧图表表格；升级时需为每行补 kind: figure 和稳定 id。")
    else:
        warnings.append("未找到图表清单.md、交付物清单.md 或 minimal 问题分析卡。")
    return actions, warnings


def full_preview(root: Path, skill_dir: Path, mode: str) -> tuple[list[dict[str, object]], list[str]]:
    actions: list[dict[str, object]] = []
    warnings: list[str] = []
    if mode != "minimal":
        warnings.append(f"--to-full 需要 minimal 上下文，当前检测为 {mode}。")
        return actions, warnings

    card = root / "02_问题分析卡.md"
    if not card.is_file():
        warnings.append("缺少 02_问题分析卡.md，无法建立逐问题映射。")
        return actions, warnings
    text = card.read_text(encoding="utf-8-sig")
    questions = QUESTION_MARKER_RE.findall(text)
    if not questions:
        questions = QUESTION_RE.findall(text)
        if questions:
            warnings.append("旧 minimal 缺少稳定 question marker；问题边界由标题回退识别，必须人工确认。")
    _, sections = load_shared_sections(skill_dir / "assets" / "templates" / "shared" / "question-sections.md")
    expected_ids = [section["id"] for section in sections]
    present_ids = set(SECTION_MARKER_RE.findall(text))

    full_template_names = sorted(
        path.name for path in (skill_dir / "assets" / "templates" / "full").glob("*.md")
        if path.name != "问题N_分析卡.md"
    )
    actions.append(
        {
            "action": "create-in-separate-target",
            "files": full_template_names,
            "note": "00_赛题总览.md 等同名源文件只读取和映射，不在原目录覆盖。",
        }
    )
    for question in questions:
        actions.append(
            {
                "action": "split-question-card",
                "source": f"02_问题分析卡.md#问题 {question}",
                "target": f"问题{question}_分析卡.md",
                "section_mapping": [
                    {
                        "id": section_id,
                        "status": "mapped" if section_id in present_ids else "manual-required",
                    }
                    for section_id in expected_ids
                ],
            }
        )
    if not questions:
        warnings.append("没有找到“## 问题 N”章节。")
    missing = [section_id for section_id in expected_ids if section_id not in present_ids]
    if missing:
        warnings.append("缺少稳定 section ID，以下章节必须人工映射：" + ", ".join(missing))
    actions.append(
        {
            "action": "preserve-source",
            "files": sorted(path.name for path in root.glob("*.md")),
            "note": "预览与后续升级均不得覆盖 minimal 源文件。",
        }
    )
    return actions, warnings


def main() -> int:
    args = parse_args()
    if not args.to_full and not args.deliverables:
        raise SystemExit("select at least one preview: --to-full or --deliverables")
    root = args.context.resolve()
    if not root.is_dir():
        raise SystemExit(f"context directory does not exist: {root}")
    skill_dir = Path(__file__).resolve().parents[1]
    mode = detect_mode(root)
    actions: list[dict[str, object]] = []
    warnings: list[str] = []
    if args.deliverables:
        result, result_warnings = deliverable_preview(root, mode)
        actions.extend(result)
        warnings.extend(result_warnings)
    if args.to_full:
        result, result_warnings = full_preview(root, skill_dir, mode)
        actions.extend(result)
        warnings.extend(result_warnings)

    payload = {
        "preview_only": True,
        "context": str(root),
        "mode": mode,
        "actions": actions,
        "warnings": warnings,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"PREVIEW ONLY: mode={mode}; context={root}")
        for item in actions:
            print(f"- {item['action']}: {json.dumps(item, ensure_ascii=False)}")
        for warning in warnings:
            print(f"WARNING: {warning}")
        print("No files were written.")
    return 1 if mode in {"ambiguous", "unknown"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
