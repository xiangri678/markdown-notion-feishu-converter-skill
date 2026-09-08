# Markdown, Notion, and Feishu Converter Skill

[中文](README.zh-CN.md) | English

An Agent Skill for transferring documents among Markdown, Notion, and Feishu while preserving structure, links, source traceability, and verification.

## Contents

- `SKILL.md`: agent workflow and safety boundaries
- `scripts/notion_to_markdown.py`: dependency-free Notion block exporter
- `references/format-mapping.md`: cross-format mapping and known lossy structures
- `examples/`: sample Markdown, invocation prompts, and verification record
- `agents/openai.yaml`: UI metadata

## Use

Install this repository with an Agent Skills-compatible client, or copy the repository into your agent's skills directory. Invoke it when moving or converting a document among the supported formats.

See [`examples/README.md`](examples/README.md) for Markdown-to-Notion, Markdown-to-Feishu, and Notion-to-Markdown examples.

## Authorship

Created by Xiangri from a self-built Hermes Agent workflow. Third-party services and clients retain their own terms and licenses.

## License

[MIT](LICENSE)
