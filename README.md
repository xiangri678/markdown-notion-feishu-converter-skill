# Markdown, Notion, and Feishu Converter Skill

[中文](README.zh-CN.md) | English

An Agent Skill for transferring documents among Markdown, Notion, and Feishu while preserving structure, links, source traceability, and verification.

## Contents

- `SKILL.md`: agent workflow and safety boundaries
- `scripts/notion_to_markdown.py`: recursive Notion block, table, and nested-list exporter
- `scripts/markdown_to_notion.py`: Markdown parser plus previewed, batched, read-back-verified Notion writer
- `scripts/feishu_markdown.py`: current `lark-cli` wrapper for Feishu Markdown import and export
- `scripts/verify_markdown.py`: compare headings, links, code blocks, tables, and lists
- `tests/`: Markdown parsing and loss-detection tests
- `references/format-mapping.md`: cross-format mapping and known lossy structures
- `examples/`: sample Markdown, invocation prompts, and verification record
- `agents/openai.yaml`: UI metadata

## Use

Install this repository with an Agent Skills-compatible client, or copy the repository into your agent's skills directory. Invoke it when moving or converting a document among the supported formats.

See [`examples/README.md`](examples/README.md) for executable commands covering all six directions. Notion and Feishu writers print a plan unless `--confirm-write` is passed after review.

## Authorship

Based on practical experience with Hermes Agent workflows. Third-party services and clients retain their own terms and licenses.

## License

[MIT](LICENSE)
