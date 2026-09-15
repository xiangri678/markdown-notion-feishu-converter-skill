#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
notion_to_markdown.py — Notion 页面 → 飞书兼容 Markdown 转换器

用法:
  python3 notion_to_markdown.py <Notion_URL_or_page_id> [--output-dir DIR] [--title 标题]

行为:
  1. Notion API 分页递归拉取页面所有 blocks（含嵌套 children）
  2. 转换为飞书 Markdown（lark-doc-md 转义规则）
  3. 输出:
     - <out>/<title>.md       完整合并版（人类可读）
     - <out>/<title>.part-0.md 分段文件（part-0 含文档标题，供 docs +create 建骨架）
     - <out>/<title>.part-N.md 后续分段（供 docs +update --command append）
     - <out>/summary.json     block 统计 + 未转换块警告

转换降级说明（飞书 Markdown 能力边界）:
  - heading_1/2/3 → ## / ### / ####（整体降一级，# 预留给飞书文档标题）
  - callout → "> **emoji 文本**"（children 平铺）
  - toggle → "📁 标题" 行 + children 平铺
  - underline → <u>（飞书 markdown 模式会解析 XML 标签）
  - 无表头表格 → 首行作表头（GFM 语法必需）
  - unsupported 块 → <!-- 未转换块: type --> 占位 + summary.json 警告
"""
import argparse
import json
import os
import re
import ssl
import sys
import urllib.parse
import uuid

PAGE_SIZE = 100
SEGMENT_CHARS = 25000  # 单次 create/append 的字符上限（稳妥值）


def get_auth(name='NOTION_API_TOKEN'):
    tok = os.environ.get(name) or (os.environ.get('NOTION_API_KEY') if name == 'NOTION_API_TOKEN' else None)
    if tok:
        return tok.strip()
    sys.exit(f'{name} 未找到；请通过环境变量提供，不要写入仓库')


AUTH = ''
CTX = ssl.create_default_context()


def notion_get(path):
    conn = http_conn()
    conn.request('GET', path, headers={
        'Authorization': 'Bearer ' + AUTH,
        'Notion-Version': '2022-06-28',
    })
    resp = conn.getresponse()
    data = json.loads(resp.read().decode('utf-8'))
    conn.close()
    if resp.status != 200:
        sys.exit(f'Notion API {resp.status}: {data.get("message", "")} path={path}')
    return data


def http_conn():
    return __import__('http.client').client.HTTPSConnection(
        'api.notion.com', 443, context=CTX, timeout=30)


def get_all_blocks(block_id):
    results = []
    url = f'/v1/blocks/{block_id}/children?page_size={PAGE_SIZE}'
    while url:
        data = notion_get(url)
        results.extend(data.get('results', []))
        url = (f'/v1/blocks/{block_id}/children?page_size={PAGE_SIZE}'
               f'&start_cursor={data["next_cursor"]}') if data.get('has_more') else None
    return results


def get_children(b):
    if not b.get('has_children'):
        return []
    return get_all_blocks(b['id'])


def escape_text(s, in_cell=False):
    """按飞书 markdown 转义规则处理字面文本（lark-doc-md 无条件转义集）。"""
    out = (s.replace('\\', '\\\\').replace('`', '\\`').replace('*', '\\*')
            .replace('_', '\\_').replace('[', '\\[').replace(']', '\\]')
            .replace('$', '\\$').replace('~', '\\~').replace('<', '\\<'))
    if in_cell:
        out = out.replace('|', '\\|')
    return out


def inline(rich_texts):
    """rich_text 数组 → 行内 markdown（含 annotations）。"""
    parts = []
    for rt in rich_texts:
        t = rt.get('type', 'text')
        if t == 'equation':
            parts.append('$' + rt['equation']['expression'] + '$')
        elif t == 'mention':
            m = rt.get('mention', {})
            mt = m.get('type')
            plain = rt.get('plain_text', '')
            if mt in ('page', 'database'):
                pid = m[mt].get('id', '')
                url = 'https://www.notion.so/' + pid.replace('-', '')
                parts.append('[' + plain + '](' + url + ')')
            else:
                parts.append(plain)
        else:
            content = rt.get('text', {}).get('content', '')
            ann = rt.get('annotations', {})
            if ann.get('code'):
                # 行内代码内所有符号均为字面量，不转义
                parts.append('`' + content + '`')
                continue
            content = escape_text(content)
            if ann.get('bold'):
                content = '**' + content + '**'
            if ann.get('italic'):
                content = '*' + content + '*'
            if ann.get('strikethrough'):
                content = '~~' + content + '~~'
            if ann.get('underline'):
                content = '<u>' + content + '</u>'
            text_obj = rt.get('text') or {}
            href = rt.get('href') or (text_obj.get('link') or {}).get('url')
            if href:
                content = '[' + content + '](' + href + ')'
            parts.append(content)
    return ''.join(parts)


def md_table(rows, has_header):
    if not rows:
        return ''
    if not has_header:
        header, body = rows[0], rows[1:]
    else:
        header, body = rows[0], rows[1:]
    cols = len(header)

    def fmt(r):
        cells = [escape_text((c or '').replace('\n', ' ').strip(), in_cell=True) for c in r[:cols]]
        cells += [''] * (cols - len(cells))
        return '| ' + ' | '.join(cells) + ' |'

    out = [fmt(header), '|' + '---|' * cols]
    out += [fmt(r) for r in body]
    return '\n'.join(out)


def blocks_to_groups(blocks, level, warnings):
    """返回段落字符串列表（每个元素是一个"块组"，顶层以空行连接）。"""
    groups = []
    i, n = 0, len(blocks)
    indent = '  ' * level
    while i < n:
        b = blocks[i]
        t = b['type']
        if t == 'bulleted_list_item':
            lines = []
            while i < n and blocks[i]['type'] == 'bulleted_list_item':
                b2 = blocks[i]
                lines.append(indent + '- ' + inline(b2[t]['rich_text']))
                for g in blocks_to_groups(get_children(b2), level + 1, warnings):
                    lines.extend(g.split('\n'))
                i += 1
            groups.append('\n'.join(lines))
            continue
        if t == 'numbered_list_item':
            lines = []
            num = 1
            while i < n and blocks[i]['type'] == 'numbered_list_item':
                b2 = blocks[i]
                lines.append(indent + str(num) + '. ' + inline(b2[t]['rich_text']))
                for g in blocks_to_groups(get_children(b2), level + 1, warnings):
                    lines.extend(g.split('\n'))
                num += 1
                i += 1
            groups.append('\n'.join(lines))
            continue
        if t == 'paragraph':
            groups.append(indent + inline(b['paragraph']['rich_text']))
        elif t.startswith('heading_'):
            h = int(t[-1]) + 1  # 降一级，# 预留给文档标题
            groups.append(indent + '#' * h + ' ' + inline(b[t]['rich_text']))
        elif t == 'to_do':
            td = b['to_do']
            mark = 'x' if td.get('checked') else ' '
            groups.append(indent + '- [' + mark + '] ' + inline(td['rich_text']))
        elif t == 'toggle':
            groups.append(indent + '📁 ' + inline(b['toggle']['rich_text']))
            groups.extend(blocks_to_groups(get_children(b), level, warnings))
        elif t == 'quote':
            lines = [indent + '> ' + inline(b['quote']['rich_text'])]
            for g in blocks_to_groups(get_children(b), level, warnings):
                lines.append('> ' + g.replace('\n', '\n> '))
            groups.append('\n'.join(lines))
        elif t == 'callout':
            icon = b['callout'].get('icon', {})
            emoji = icon.get('emoji', '💡') if icon.get('type') == 'emoji' else '💡'
            groups.append(indent + '> **' + emoji + ' ' + inline(b['callout']['rich_text']) + '**')
            groups.extend(blocks_to_groups(get_children(b), level, warnings))
        elif t == 'code':
            lang = b['code'].get('language') or ''
            text = ''.join(rt.get('text', {}).get('content', '') for rt in b['code']['rich_text'])
            groups.append('```' + lang + '\n' + text + '\n```')
        elif t == 'table':
            rows = []
            for row in get_children(b):
                rows.append([''.join(rt.get('plain_text', '') for rt in cell)
                             for cell in row['table_row']['cells']])
            md = md_table(rows, b['table'].get('has_column_header', False))
            if md:
                groups.append(md)
        elif t == 'divider':
            groups.append('---')
        elif t == 'image':
            img = b['image']
            url = (img.get('external') or {}).get('url') or (img.get('file') or {}).get('url')
            if url:
                cap = ''.join(rt.get('plain_text', '') for rt in img.get('caption', []))
                groups.append('![' + cap + '](' + url + ')')
            else:
                warnings.append('image block without url: ' + b['id'])
        elif t == 'equation':
            groups.append('$$' + b['equation']['expression'] + '$$')
        elif t in ('bookmark', 'link_preview'):
            data = b[t]
            url = data.get('url')
            cap = ''.join(rt.get('plain_text', '') for rt in data.get('caption', []))
            if url:
                groups.append('[' + (cap or url) + '](' + url + ')')
        elif t in ('file', 'pdf'):
            f = b[t]
            name = f.get('name') or ('附件 ' + b['id'][:8])
            url = (f.get('external') or {}).get('url') or (f.get('file') or {}).get('url')
            if url:
                groups.append('[' + name + '](' + url + ')')
            else:
                warnings.append(t + ' block without url: ' + b['id'])
        elif t in ('child_page', 'child_database'):
            title = b.get(t, {}).get('title') or '(未命名子页面)'
            url = 'https://www.notion.so/' + b['id'].replace('-', '')
            groups.append('[' + title + '](' + url + ')')
        else:
            warnings.append('unsupported block type: ' + t)
            groups.append('<!-- 未转换块: ' + t + ' -->')
        i += 1
    return groups


def parse_page_ref(ref):
    """URL 或 32-hex id → (page_id, 原始字符串)。"""
    m = re.search(r'([0-9a-fA-F]{32}|[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12})', ref)
    if not m:
        sys.exit('无法从输入解析 Notion page id: ' + ref)
    raw = m.group(1).replace('-', '')
    return str(uuid.UUID(raw)), raw


def main():
    global AUTH, SEGMENT_CHARS
    ap = argparse.ArgumentParser()
    ap.add_argument('ref', help='Notion URL 或 page id')
    ap.add_argument('--output-dir', '--out', dest='output_dir', default='notion-export', help='输出目录')
    ap.add_argument('--title', default=None, help='覆盖页面标题')
    ap.add_argument('--token-env', default='NOTION_API_TOKEN', help='Notion token 环境变量名')
    ap.add_argument('--segment-chars', type=int, default=SEGMENT_CHARS, help='飞书分段字符数')
    args = ap.parse_args()
    if args.segment_chars < 1000:
        ap.error('--segment-chars must be at least 1000')
    AUTH = get_auth(args.token_env)
    SEGMENT_CHARS = args.segment_chars

    page_id, _ = parse_page_ref(args.ref)
    page = notion_get('/v1/pages/' + page_id)
    props = page.get('properties', {})
    title = args.title
    if not title:
        for p in props.values():
            t = p.get('title') or []
            if t:
                title = ''.join(x.get('plain_text', '') for x in t)
                break
    if not title:
        title = page_id[:8]

    blocks = get_all_blocks(page_id)
    warnings = []
    # 标题去重：页面首个 block 若是 heading_1 且文本与页面标题重复（或标题是它的日期后缀变体
    # 如 title="会议纪要：X — 2026-08-13"、首块 heading_1="会议纪要：X"），剔除首块，
    # 避免转出后"文档标题 + 正文第一行同标题"重复。
    if blocks:
        b0 = blocks[0]
        if b0.get('type') == 'heading_1':
            h_text = ''.join(rt.get('plain_text', '') for rt in b0['heading_1'].get('rich_text', [])).strip()
            if h_text and (h_text == title.strip() or title.strip().startswith(h_text)):
                blocks = blocks[1:]
                warnings.append('removed first heading_1 identical to page title: ' + h_text)
    groups = blocks_to_groups(blocks, 0, warnings)

    md_full = '# ' + title + '\n\n' + '\n\n'.join(groups) if groups else '# ' + title

    safe = re.sub(r'[/\\:*?"<>|]', '_', title).strip()
    out_dir = os.path.abspath(os.path.expanduser(args.output_dir))
    os.makedirs(out_dir, exist_ok=True)

    # 完整版
    full_path = os.path.join(out_dir, 'page.md')
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(md_full)

    # 分段：part-0 = 标题 + 第一段内容（create 骨架），后续 append
    segs = []
    cur = '# ' + title
    for g in groups:
        candidate = cur + '\n\n' + g if cur != '# ' + title else cur + '\n\n' + g
        if len(candidate) > SEGMENT_CHARS and cur != '# ' + title:
            segs.append(cur)
            cur = g
        else:
            cur = candidate
    segs.append(cur)
    # 如果 part-0 只有标题（空页面），单独处理
    if len(segs) == 1 and segs[0].strip() == '# ' + title:
        segs = ['# ' + title]

    part_paths = []
    for idx, seg in enumerate(segs):
        p = os.path.join(out_dir, f'page.part-{idx}.md')
        with open(p, 'w', encoding='utf-8') as f:
            f.write(seg)
        part_paths.append(p)

    summary = {
        'page_id': page_id,
        'title': title,
        'block_count': len(blocks),
        'segments': len(segs),
        'part_files': part_paths,
        'full_file': full_path,
        'char_count': len(md_full),
        'warnings': warnings,
    }
    with open(os.path.join(out_dir, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print('Use scripts/feishu_markdown.py import to create a Feishu document from page.md.')


if __name__ == '__main__':
    main()
