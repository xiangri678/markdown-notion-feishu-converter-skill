#!/usr/bin/env python3
"""Compare structural Markdown counts before accepting a document conversion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


def inventory(text: str) -> dict[str, int]:
    return {
        "headings": len(re.findall(r"^#{1,6}\s+", text, flags=re.M)),
        "links": len(re.findall(r"\[[^\]]+\]\([^)]+\)", text)),
        "code_fences": len(re.findall(r"^```", text, flags=re.M)) // 2,
        "table_rows": len(re.findall(r"^\|.*\|\s*$", text, flags=re.M)),
        "tasks": len(re.findall(r"^- \[[ xX]\] ", text, flags=re.M)),
        "list_items": len(re.findall(r"^(?:[-+*]|\d+[.)])\s+", text, flags=re.M)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("converted", type=Path)
    parser.add_argument("--report", type=Path, default=Path("conversion-validation.json"))
    args = parser.parse_args()
    source = inventory(args.source.read_text(encoding="utf-8"))
    converted = inventory(args.converted.read_text(encoding="utf-8"))
    losses = {key: source[key] - converted[key] for key in source if converted[key] < source[key]}
    result = {"valid": not losses, "source": source, "converted": converted, "losses": losses}
    output = args.report.expanduser().resolve()
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("VALID" if result["valid"] else "INVALID")
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
