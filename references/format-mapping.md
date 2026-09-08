# Format mapping

[中文](format-mapping.zh-CN.md) | English

Prefer structures that all three formats can represent reliably.

| Content | Markdown | Notion | Feishu |
| --- | --- | --- | --- |
| Heading | `#` through `###` | heading blocks | heading blocks |
| Bulleted list | `- item` | bulleted list item | bullet block |
| Numbered list | `1. item` | numbered list item | ordered block |
| Quote | `> text` | quote block | quote block |
| Code | fenced block with language | code block | code block |
| Table | pipe table | simple table | table block |
| Link | inline Markdown link | rich-text link | text link |
| Image/file | relative path or URL | file/image block | media/file block |

Notion databases, synced blocks, Feishu Sheets, interactive widgets, comments, permissions, page history, and mentions do not have lossless Markdown equivalents. Preserve their source links and describe the loss instead of silently inventing a substitute.

When Markdown contains local files, resolve paths relative to the Markdown file and upload through the destination's authorized API. Never expose private signed URLs in the exported Markdown.
