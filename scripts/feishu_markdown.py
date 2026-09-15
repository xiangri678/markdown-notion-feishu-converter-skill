#!/usr/bin/env python3
"""Import or export Feishu documents as Markdown through the installed lark-cli."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess


def run_json(command: list[str], cwd: Path | None = None) -> dict:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"command failed: {command[0]}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("lark-cli did not return JSON: " + result.stdout[:500]) from exc


def find_content(payload: dict) -> str:
    value = payload.get("data", {}).get("document", {}).get("content")
    if not isinstance(value, str):
        raise RuntimeError("lark-cli response has no data.document.content")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lark-cli", default=shutil.which("lark-cli") or "lark-cli")
    sub = parser.add_subparsers(dest="command", required=True)
    export = sub.add_parser("export")
    export.add_argument("--doc", required=True)
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--as", dest="identity", choices=["user", "bot"], default="user")
    create = sub.add_parser("import")
    create.add_argument("--input", type=Path, required=True)
    create.add_argument("--title")
    create.add_argument("--parent-token")
    create.add_argument("--as", dest="identity", choices=["user", "bot"], default="user")
    create.add_argument("--result", type=Path, default=Path("feishu-import-result.json"))
    create.add_argument("--confirm-write", action="store_true")
    args = parser.parse_args()

    if args.command == "export":
        payload = run_json([
            args.lark_cli, "docs", "+fetch", "--doc", args.doc,
            "--doc-format", "markdown", "--as", args.identity, "--format", "json",
        ])
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(find_content(payload).rstrip() + "\n", encoding="utf-8")
        print(output)
        return 0

    source = args.input.expanduser().resolve()
    command = [
        args.lark_cli, "docs", "+create", "--doc-format", "markdown",
        "--title", args.title or source.stem, "--content", "@" + source.name,
        "--as", args.identity, "--format", "json",
    ]
    if args.parent_token:
        command.extend(["--parent-token", args.parent_token])
    if not args.confirm_write:
        print(json.dumps({"cwd": str(source.parent), "command": command}, ensure_ascii=False, indent=2))
        print("No document was created. Pass --confirm-write after reviewing this plan.")
        return 0
    payload = run_json(command, cwd=source.parent)
    document = payload.get("data", {}).get("document", {})
    result = {
        "ok": bool(payload.get("ok") and document.get("document_id")),
        "document_id": document.get("document_id", ""),
        "url": document.get("url", ""),
        "source": str(source),
    }
    output = args.result.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
