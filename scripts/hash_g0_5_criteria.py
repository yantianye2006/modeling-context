#!/usr/bin/env python3
"""Compute the canonical G0.5 preregistration hash for one question."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_modeling_context import (
    QUESTION_BLOCK_RE,
    criteria_hash_from_g05,
    g05_criteria_material,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hash the applicable G0.5 probes and preregistered criteria without modifying notes."
    )
    parser.add_argument("--context", required=True, type=Path, help="Generated modeling directory")
    parser.add_argument("--question", required=True, type=int, help="Top-level question number")
    parser.add_argument("--json", action="store_true", help="Emit hash and normalized material as JSON")
    return parser.parse_args()


def question_text(root: Path, question: int) -> tuple[str, str]:
    full = root / f"问题{question}_分析卡.md"
    if full.is_file():
        return full.read_text(encoding="utf-8-sig"), full.name

    minimal = root / "02_问题分析卡.md"
    if not minimal.is_file():
        raise SystemExit(f"cannot find question card for question {question}")
    text = minimal.read_text(encoding="utf-8-sig")
    for match in QUESTION_BLOCK_RE.finditer(text):
        if int(match.group(1)) == question:
            return match.group(2), minimal.name
    raise SystemExit(f"cannot find question {question} in {minimal.name}")


def main() -> int:
    args = parse_args()
    root = args.context.resolve()
    text, source = question_text(root, args.question)
    try:
        criteria_hash = criteria_hash_from_g05(text)
    except ValueError as exc:
        raise SystemExit(f"cannot hash incomplete G0.5 declaration: {exc}") from exc
    material, _ = g05_criteria_material(text)
    if args.json:
        print(
            json.dumps(
                {
                    "question": args.question,
                    "source": source,
                    "criteria_hash": criteria_hash,
                    "normalized": material,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(criteria_hash)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
