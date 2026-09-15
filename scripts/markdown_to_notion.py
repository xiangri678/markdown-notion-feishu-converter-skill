#!/usr/bin/env python3
"""Convert Markdown to Notion blocks and optionally create a verified Notion page."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request


KNOWN_CODE_LANGUAGES = {
    "abap", "arduino", "bash", "basic", "c", "c++", "c#", "clojure", "coffeescript",
    "css", "dart", "diff", "docker", "elixir", "elm", "erlang", "flow", "fortran", "f#",
    "gherkin", "glsl", "go", "graphql", "groovy", "haskell", "html", "java", "javascript",
    "json", "julia", "kotlin", "latex", "less", "lisp", "livescript", "lua", "makefile",
    "markdown", "markup", "matlab", "mermaid", "nix", "objective-c", "ocaml", "pascal",
    "perl", "php", "plain text", "powershell", "prolog", "protobuf", "python", "r", "reason",
    "ruby", "rust", "sass", "scala", "scheme", "scss", "shell", "sql", "swift", "typescript",
    "vb.net", "verilog", "wasm", "wolfram", "xml", "yaml", "zig",
}


def text_object(content: str, annotation: str | None = None, url: str | None = None) -> dict:
    item: dict = {"type": "text", "text": {"content": content}}
    if url:
        item["text"]["link"] = {"url": url}
    if annotation:
        item["annotations"] = {annotation: True}
    return item


def split_text_object(item: dict, limit: int = 1900) -> list[dict]:
    content = item.get("text", {}).get("content", "")
    if len(content) <= limit:
        return [item]
    result: list[dict] = []
    for start in range(0, len(content), limit):
        clone = json.loads(json.dumps(item))
        clone["text"]["content"] = content[start:start + limit]
        result.append(clone)
    return result


INLINE = re.compile(r"(\[[^\]]+\]\(https?://[^)]+\)|\*\*[^*]+\*\*|~~[^~]+~~|`[^`]+`|\*[^*]+\*)")


def rich_text(value: str) -> list[dict]:
    result: list[dict] = []
    for part in INLINE.split(value):
        if not part:
            continue
        link = re.fullmatch(r"\[([^\]]+)\]\((https?://[^)]+)\)", part)
        if link:
            result.append(text_object(link.group(1), url=link.group(2)))
        elif part.startswith("**") and part.endswith("**"):
            result.append(text_object(part[2:-2], "bold"))
        elif part.startswith("~~") and part.endswith("~~"):
            result.append(text_object(part[2:-2], "strikethrough"))
        elif part.startswith("`") and part.endswith("`"):
            result.append(text_object(part[1:-1], "code"))
        elif part.startswith("*") and part.endswith("*"):
            result.append(text_object(part[1:-1], "italic"))
        else:
            result.append(text_object(part))
    split: list[dict] = []
    for item in result or [text_object("")]:
        split.extend(split_text_object(item))
    if len(split) > 100:
        raise ValueError("one Markdown block expands beyond 100 Notion rich-text objects")
    return split


def text_block(kind: str, value: str, **extra) -> dict:
    body = {"rich_text": rich_text(value), **extra}
    return {"object": "block", "type": kind, kind: body}


def split_table_row(value: str) -> list[str]:
    return [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", value.strip().strip("|"))]


def table_block(rows: list[list[str]]) -> dict:
    width = max(len(row) for row in rows)
    children = []
    for row in rows:
        cells = row + [""] * (width - len(row))
        children.append({
            "object": "block",
            "type": "table_row",
            "table_row": {"cells": [rich_text(cell) for cell in cells]},
        })
    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": width,
            "has_column_header": True,
            "has_row_header": False,
            "children": children,
        },
    }


def markdown_to_blocks(markdown: str, strip_first_title: bool = True) -> tuple[str | None, list[dict]]:
    lines = markdown.splitlines()
    title = None
    if strip_first_title:
        for index, line in enumerate(lines):
            if not line.strip():
                continue
            match = re.fullmatch(r"#\s+(.+)", line.strip())
            if match:
                title = match.group(1).strip()
                del lines[index]
            break

    blocks: list[dict] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("```"):
            language = stripped[3:].strip().lower()
            language = "shell" if language == "sh" else language
            language = language if language in KNOWN_CODE_LANGUAGES else "plain text"
            body: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            blocks.append(text_block("code", "\n".join(body), language=language or "plain text"))
            i += 1
            continue
        if stripped.startswith("|") and i + 1 < len(lines) and re.fullmatch(r"\|?[\s:|-]+\|?", lines[i + 1].strip()):
            rows = [split_table_row(stripped)]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_table_row(lines[i]))
                i += 1
            blocks.append(table_block(rows))
            continue
        heading = re.fullmatch(r"(#{1,6})\s+(.+)", stripped)
        if heading:
            blocks.append(text_block(f"heading_{min(len(heading.group(1)), 3)}", heading.group(2)))
        elif stripped in {"---", "***", "___"}:
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        elif stripped.startswith(">"):
            blocks.append(text_block("quote", stripped[1:].strip()))
        elif re.match(r"^- \[[ xX]\] ", stripped):
            blocks.append(text_block("to_do", stripped[6:], checked=stripped[3].lower() == "x"))
        elif re.match(r"^[-+*] ", stripped):
            blocks.append(text_block("bulleted_list_item", stripped[2:]))
        elif re.match(r"^\d+[.)] ", stripped):
            blocks.append(text_block("numbered_list_item", re.sub(r"^\d+[.)] ", "", stripped)))
        else:
            blocks.append(text_block("paragraph", stripped))
        i += 1
    return title, blocks


def block_weight(block: dict) -> int:
    body = block.get(block.get("type", ""), {})
    return 1 + len(body.get("children", []))


def batches(blocks: list[dict], limit: int = 90) -> list[list[dict]]:
    result: list[list[dict]] = []
    current: list[dict] = []
    weight = 0
    for block in blocks:
        item_weight = block_weight(block)
        if item_weight > limit:
            raise ValueError(f"single {block.get('type')} block exceeds Notion request limit")
        if current and weight + item_weight > limit:
            result.append(current)
            current, weight = [], 0
        current.append(block)
        weight += item_weight
    if current:
        result.append(current)
    return result


class NotionClient:
    def __init__(self, token: str, base_url: str, version: str):
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.version = version

    def request(self, method: str, path: str, payload: dict | None = None) -> dict:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            method=method,
            headers={
                "Authorization": "Bearer " + self.token,
                "Notion-Version": self.version,
                "Content-Type": "application/json; charset=utf-8",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1200]
            raise RuntimeError(f"Notion API returned HTTP {exc.code}: {detail}") from exc

    def children(self, block_id: str) -> list[dict]:
        result: list[dict] = []
        cursor = None
        while True:
            query = {"page_size": "100"}
            if cursor:
                query["start_cursor"] = cursor
            payload = self.request("GET", f"/blocks/{block_id}/children?" + urllib.parse.urlencode(query))
            result.extend(payload.get("results", []))
            if not payload.get("has_more"):
                return result
            cursor = payload.get("next_cursor")
            if not cursor:
                raise RuntimeError("Notion children response has_more without next_cursor")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parent = parser.add_mutually_exclusive_group(required=True)
    parent.add_argument("--parent-page-id")
    parent.add_argument("--database-id")
    parser.add_argument("--title")
    parser.add_argument("--title-property", default="Name")
    parser.add_argument("--token-env", default="NOTION_API_TOKEN")
    parser.add_argument("--base-url", default="https://api.notion.com/v1")
    parser.add_argument("--notion-version", default="2022-06-28")
    parser.add_argument("--result", type=Path, default=Path("notion-import-result.json"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm-write", action="store_true")
    args = parser.parse_args()

    source = args.input.expanduser().resolve()
    inferred_title, blocks = markdown_to_blocks(source.read_text(encoding="utf-8"))
    title = args.title or inferred_title or source.stem
    properties = {
        (args.title_property if args.database_id else "title"): {
            "title": [{"type": "text", "text": {"content": title}}]
        }
    }
    parent_payload = {"database_id": args.database_id} if args.database_id else {"page_id": args.parent_page_id}
    grouped = batches(blocks)
    create_payload = {"parent": parent_payload, "properties": properties, "children": grouped[0] if grouped else []}
    plan = {"title": title, "blocks": len(blocks), "batches": len(grouped), "create_payload": create_payload}
    if args.dry_run or not args.confirm_write:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        if not args.confirm_write:
            print("No page was created. Pass --confirm-write after reviewing this plan.")
        return 0

    token = os.environ.get(args.token_env, "")
    if not token:
        parser.error(f"set {args.token_env}")
    client = NotionClient(token, args.base_url, args.notion_version)
    page = client.request("POST", "/pages", create_payload)
    page_id = page.get("id")
    if not page_id:
        raise RuntimeError("Notion create response did not contain a page id")
    for group in grouped[1:]:
        client.request("PATCH", f"/blocks/{page_id}/children", {"children": group})
    verified_page = client.request("GET", f"/pages/{page_id}")
    verified_children = client.children(page_id)
    result = {
        "ok": verified_page.get("id") == page_id and len(verified_children) == len(blocks),
        "page_id": page_id,
        "url": page.get("url", ""),
        "source": str(source),
        "expected_top_level_blocks": len(blocks),
        "readback_top_level_blocks": len(verified_children),
    }
    output = args.result.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
