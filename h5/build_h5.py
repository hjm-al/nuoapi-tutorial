# -*- coding: utf-8 -*-
"""把上级目录的 README.md（主教程）构建成手机端 H5 单文件网页 index.html。

用法::

    python h5/build_h5.py

特点：
- 移动优先：viewport、抽屉式目录、阅读进度条、回到顶部、代码一键复制
- 单文件产物（样式与脚本内联），可离线分发；样式/脚本来自 ``h5/theme.py``，
  与多页站点构建器 ``h5/build_site.py`` 共用，避免两套外观漂移
- 页面内的相对链接（docs/、examples/、FAQ.md 等）自动加 ../ 前缀，
  便于把产物单独放到任意子路径下引用仓库文件

需要 ``markdown`` 包：``python -m pip install -r h5/requirements.txt``。
"""

import html
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import markdown

from theme import CSS, JS

SCRIPT_DIR = Path(__file__).resolve().parent
README = SCRIPT_DIR.parent / "README.md"
OUTPUT = SCRIPT_DIR / "index.html"

# Markdown 头部的 SEO 键值块（与 build_site.py 同一约定，用 HTML 注释包着所以
# 在 GitHub 与本站两个渲染面都不可见）：
#   <!-- seo-meta
#     title: ...
#     description: ...
#   -->
# 单文件页不能依赖 build_site 的模块，所以这里保留一份最小实现；两者拆法不一致
# 会被 tests/test_site_build.py 的产物一致性测试当场抓出来。
FRONTMATTER = re.compile(r"\A<!--\s*seo-meta\s*\n(.*?)\n\s*-->[ \t]*(?:\n|\Z)", re.S)


def split_frontmatter(text: str):
    """拆出 ``<!-- seo-meta -->`` 头里的 title / description，返回 (meta, 正文)；没头就原样返回。"""
    match = FRONTMATTER.match(text)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        key = key.strip().lower()
        if key in ("title", "description") and value.strip():
            meta[key] = value.strip()
    return meta, text[match.end():]


def github_slug(value: str, separator: str = "-", **kwargs) -> str:
    """模拟 GitHub 给标题生成锚点的规则：保留中文，小写，空格变连字符。"""
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"[^\w\s-]", "", value.lower(), flags=re.UNICODE)
    return re.sub(r"\s+", separator, value).strip(separator)


def fix_relative_links(html: str) -> str:
    """相对链接加 ../ 前缀；外链加 target=_blank。"""

    def repl(match: re.Match) -> str:
        attr, url = match.group(1), match.group(2)
        # 已经是 ../（或外链/锚点）开头的相对链接保持原样，避免二次构建叠加成 ../../
        if url.startswith(("#", "http://", "https://", "mailto:", "tel:", "data:", "../")):
            return match.group(0)
        return '{0}="../{1}"'.format(attr, url)

    html = re.sub(r'\b(href|src)="([^"]+)"', repl, html)
    html = re.sub(
        r'<a href="(https?://[^"]+)"',
        r'<a target="_blank" rel="noopener noreferrer" href="\1"',
        html,
    )
    return html


def wrap_tables(html: str) -> str:
    """给表格包一层可横向滚动的容器。"""
    html = html.replace("<table>", '<div class="table-wrap"><table>')
    html = html.replace("</table>", "</table></div>")
    return html


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#2563eb">
<meta name="description" content="__DESC__">
<title>__TITLE__</title>
__CSS__
</head>
<body>
<div id="progress"></div>
<header class="appbar">
  <button id="menuBtn" class="menu-btn" aria-label="打开目录">&#9776;</button>
  <div>
    <div class="appbar-title">NuoAPI 接入脚手架</div>
    <div class="appbar-sub">H5 版主教程 · 构建于 __GEN_DATE__</div>
  </div>
</header>

<div id="mask"></div>
<nav id="drawer" aria-label="教程目录">
  <div class="drawer-head">
    <strong>教程目录</strong>
    <button id="drawerClose" class="drawer-close" aria-label="关闭目录">&times;</button>
  </div>
  <div class="drawer-body">__TOC__</div>
</nav>

<article>
__CONTENT__
</article>

<footer class="site-footer">
  本页面由 README.md 自动构建 · 示例代码采用 MIT 许可证<br>
  本工具箱不提供、不代售任何 API 服务，不构成投资或购买建议
</footer>

<button id="toTop" aria-label="回到顶部">&#8593;</button>

__JS__
</body>
</html>
"""


def build(readme: Path = README, output: Path = OUTPUT) -> Path:
    """按给定输入/输出路径构建单文件页，返回产物路径（便于测试与 CI 复用）。"""
    raw = readme.read_text(encoding="utf-8")
    meta, text = split_frontmatter(raw)

    md = markdown.Markdown(
        extensions=["fenced_code", "tables", "sane_lists", "toc"],
        extension_configs={
            "toc": {
                "slugify": github_slug,
                "toc_depth": "2-6",
            }
        },
    )
    content = md.convert(text)
    content = wrap_tables(content)
    content = fix_relative_links(content)
    toc = fix_relative_links(md.toc)

    title_match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "教程"
    # 搜索结果里显示的标题/摘要优先取 Markdown 头部的显式声明
    display_title = meta.get("title") or title
    description = meta.get("description") or (
        "第三方 AI 中转站买方接入脚手架与防掺水取证工具箱：四协议接入、真伪探针、成本审计"
    )
    # 标题要插入 <title> 与 HTML 属性/文本节点，先做实体转义防注入
    safe_title = html.escape(display_title, quote=True)
    gen_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 以 __CONTENT__ 为界把模板切成头、尾两段：占位符替换只在模板段上进行，
    # 随后直接拼接正文，保证 README 正文永远不会被占位符二次替换
    # （例如正文里出现字面量 __TITLE__ / __TOC__ 也会原样保留）。
    head, tail = TEMPLATE.split("__CONTENT__", 1)
    replacements = {
        "__TITLE__": safe_title,
        "__DESC__": html.escape(description, quote=True),
        "__TOC__": toc,
        "__GEN_DATE__": gen_date,
        "__CSS__": CSS,
        "__JS__": JS,
    }
    for placeholder, value in replacements.items():
        head = head.replace(placeholder, value)
        tail = tail.replace(placeholder, value)
    page = head + content + tail

    output.write_text(page, encoding="utf-8")
    print("OK -> {0} ({1} bytes)".format(output, output.stat().st_size))
    return output


def main() -> None:
    build()


if __name__ == "__main__":
    main()
