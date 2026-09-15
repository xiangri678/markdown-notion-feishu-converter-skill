from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


to_notion = load("markdown_to_notion.py")
from_notion = load("notion_to_markdown.py")
verify = load("verify_markdown.py")


class ConverterTests(unittest.TestCase):
    def test_markdown_parser_preserves_common_structures(self):
        markdown = """# Title

## Section

- [x] done

| A | B |
|---|---|
| 1 | 2 |

```python
print('ok')
```
"""
        title, blocks = to_notion.markdown_to_blocks(markdown)
        self.assertEqual(title, "Title")
        self.assertEqual(
            [item["type"] for item in blocks],
            ["heading_2", "to_do", "table", "code"],
        )

    def test_validation_reports_structural_loss(self):
        source = verify.inventory("# A\n\n[link](https://example.com)\n")
        target = verify.inventory("# A\n")
        self.assertGreater(source["links"], target["links"])

    def test_notion_export_recurses_nested_list_items(self):
        parent = {
            "id": "parent",
            "type": "bulleted_list_item",
            "has_children": True,
            "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": "parent"}}]},
        }
        child = {
            "id": "child",
            "type": "bulleted_list_item",
            "has_children": False,
            "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": "child"}}]},
        }
        original = from_notion.get_all_blocks
        from_notion.get_all_blocks = lambda block_id: [child] if block_id == "parent" else []
        try:
            groups = from_notion.blocks_to_groups([parent], 0, [])
        finally:
            from_notion.get_all_blocks = original
        self.assertIn("  - child", groups[0])


if __name__ == "__main__":
    unittest.main()
