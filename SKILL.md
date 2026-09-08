---
name: note-transfer
description: Transfer documents among Markdown files, Notion pages, and Feishu documents while preserving structure, links, and source traceability. Use when copying or converting content between any two of these formats.
license: MIT
metadata:
  author: Xiangri
  version: "1.0.0"
  compatibility: Requires Python 3, an authorized Notion client for Notion operations, and lark-cli or another authorized Feishu client for Feishu operations.
  tags: [markdown, notion, feishu, document-conversion]
---

# Note Transfer

Use Markdown as the intermediate representation. Copy by default; delete or replace a source only when the user explicitly asks.

## Choose the route

| Source | Destination | Route |
| --- | --- | --- |
| Notion | Markdown | Export blocks with `scripts/notion_to_markdown.py` or an authorized Notion client |
| Markdown | Notion | Parse headings, lists, quotes, code, tables, links, and images into Notion blocks |
| Feishu | Markdown | Read the document with `lark-cli doc read` or an equivalent authorized client |
| Markdown | Feishu | Create a document, import the Markdown, then read it back |
| Notion | Feishu | Export to Markdown, normalize, then import |
| Feishu | Notion | Export to Markdown, normalize, then create Notion blocks |

Read [references/format-mapping.md](references/format-mapping.md) before converting tables, callouts, databases, attachments, or nested content.

## Export a Notion page

```bash
export NOTION_API_TOKEN='...'
python3 scripts/notion_to_markdown.py PAGE_ID --output-dir ./exported-page
```

The exporter writes `page.md` and `summary.json`. Supply credentials through the environment or the user's authorized connector. Never put tokens in source files, output documents, or logs.

## Transfer safely

1. Confirm the source, destination, and whether the user wants a copy or a move.
2. Read the complete source, including paginated or nested blocks.
3. Convert to Markdown and preserve the source URL or identifier in metadata.
4. Report unsupported structures before flattening them.
5. Create the destination through an authorized client.
6. Read the destination back and compare headings, paragraph count, links, tables, code blocks, and attachments.
7. Return the destination URL or path and list any intentional losses.

Do not claim success from a create response alone. For a move, delete the source only after read-back verification and explicit authorization.
