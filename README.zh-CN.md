# Markdown、Notion、飞书文档转换 Skill

中文 | [English](README.md)

用于在 Markdown、Notion 和飞书文档之间转换内容，同时尽量保留结构、链接、来源和验证信息。

## 仓库内容

- `SKILL.md`：Agent 工作流程与安全边界
- `SKILL.zh-CN.md`：中文 Skill 说明
- `scripts/notion_to_markdown.py`：无第三方 Python 依赖的 Notion Block 导出脚本
- `references/format-mapping.md`：格式映射与无法无损转换的结构
- `agents/openai.yaml`：界面元数据

## 使用

通过兼容 Agent Skills 的客户端安装本仓库，或将仓库复制到 Agent 的 Skills 目录。需要在 Markdown、Notion、飞书三者之间迁移或转换文档时调用。

## 作者

由 Xiangri 根据自己构建的 Hermes Agent 工作流整理。第三方服务和客户端仍遵循各自的条款与许可证。

## 许可证

[MIT](LICENSE)
