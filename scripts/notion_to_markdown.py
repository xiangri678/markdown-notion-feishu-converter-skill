#!/usr/bin/env python3
"""Export common Notion page blocks to Markdown without third-party packages."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import urllib.error
import urllib.parse
import urllib.request

NOTION_VERSION = "2022-06-28"


def request_json(url: str, token: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
        },
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Notion API returned HTTP {exc.code}: {detail}") from exc


def rich_text(items: list[dict]) -> str:
    parts: list[str] = []
    for item in items:
        text = item.get("plain_text", "")
        href = item.get("href")
        parts.append(f"[{text}]({href})" if href else text)
    return "".join(parts)


def block_to_markdown(block: dict) -> str:
    kind = block.get("type", "")
    value = block.get(kind, {})
    text = rich_text(value.get("rich_text", []))
    if kind == "paragraph":
        return text
    if kind.startswith("heading_"):
        level = kind.rsplit("_", 1)[-1]
        return f"{'#' * int(level)} {text}"
    if kind == "bulleted_list_item":
        return f"- {text}"
    if kind == "numbered_list_item":
        return f"1. {text}"
    if kind == "to_do":
        checked = "x" if value.get("checked") else " "
        return f"- [{checked}] {text}"
    if kind == "quote":
        return f"> {text}"
    if kind == "code":
        language = value.get("language", "")
        return f"```{language}\n{text}\n```"
    if kind == "divider":
        return "---"
    if kind == "bookmark":
        return value.get("url", "")
    if kind in {"image", "file", "pdf", "video", "audio"}:
        source = value.get(value.get("type", ""), {})
        url = source.get("url", "")
        caption = rich_text(value.get("caption", [])) or kind
        return f"[{caption}]({url})" if url else f"<!-- unsupported {kind} block -->"
    return f"<!-- unsupported Notion block: {kind} -->"


def children(block_id: str, token: str) -> list[dict]:
    results: list[dict] = []
    cursor = None
    while True:
        query = {"page_size": "100"}
        if cursor:
            query["start_cursor"] = cursor
        url = (
            f"https://api.notion.com/v1/blocks/{block_id}/children?"
            + urllib.parse.urlencode(query)
        )
        payload = request_json(url, token)
        results.extend(payload.get("results", []))
        if not payload.get("has_more"):
            return results
        cursor = payload.get("next_cursor")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("page_id", help="Notion page ID")
    parser.add_argument("--output-dir", default="notion-export")
    args = parser.parse_args()

    token = os.environ.get("NOTION_API_TOKEN")
    if not token:
        raise SystemExit("Set NOTION_API_TOKEN before exporting.")

    output_dir = pathlib.Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    blocks = children(args.page_id, token)
    lines = [block_to_markdown(block) for block in blocks]
    (output_dir / "page.md").write_text("\n\n".join(lines).rstrip() + "\n", encoding="utf-8")
    summary = {
        "source_page_id": args.page_id,
        "block_count": len(blocks),
        "unsupported_types": sorted(
            {
                block.get("type", "unknown")
                for block, line in zip(blocks, lines)
                if line.startswith("<!-- unsupported")
            }
        ),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
