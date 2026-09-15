# Markdown、Notion、飞书文档转换 Skill

中文 | [English](README.md)

用于在 Markdown、Notion 和飞书文档之间转换内容，同时尽量保留结构、链接、来源和验证信息。

## 仓库内容

- `SKILL.md`：Agent 工作流程与安全边界
- `SKILL.zh-CN.md`：中文 Skill 说明
- `scripts/notion_to_markdown.py`：递归导出 Notion Block、表格和嵌套列表
- `scripts/markdown_to_notion.py`：Markdown 转 Notion Block，支持预览、分批写入和回读
- `scripts/feishu_markdown.py`：通过当前 `lark-cli` 导入或导出飞书 Markdown
- `scripts/verify_markdown.py`：对比标题、链接、代码块、表格和列表数量
- `tests/`：Markdown 解析和格式损失测试
- `references/format-mapping.md`：格式映射与无法无损转换的结构
- `examples/`：示例 Markdown、调用提示和转换验收记录
- `agents/openai.yaml`：界面元数据

## 使用

通过兼容 Agent Skills 的客户端安装本仓库，或将仓库复制到 Agent 的 Skills 目录。需要在 Markdown、Notion、飞书三者之间迁移或转换文档时调用。

完整示例见 [`examples/README.md`](examples/README.md)，其中给出了六种转换方向的实际命令。Notion 和飞书写入命令默认只显示计划，复核后必须显式传入 `--confirm-write`。

运行离线测试：

```bash
python3 -m unittest discover -s tests -v
```

## 作者

根据 Hermes Agent 工作流的实践经验整理。第三方服务和客户端仍遵循各自的条款与许可证。

## 许可证

[MIT](LICENSE)
