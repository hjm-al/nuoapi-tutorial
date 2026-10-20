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
- 抽屉目录在 README 锚点之后附上 ``docs/*.md`` 的标题链接（指向多页站 ``docs/*.html``），
  新增文档不用手改导航；``<link rel=canonical>`` 指向多页站首页，避免两套首页互抢搜索查询

需要 ``markdown`` 包：``python -m pip install -r h5/requirements.txt``。
"""

import html
import os
import re
import unicodedata
from datetime import datetime
from pathlib import Path

import markdown

from theme import CSS, JS, SITE_SHORT, footer_html, interaction_copy_json

SCRIPT_DIR = Path(__file__).resolve().parent
README = SCRIPT_DIR.parent / "README.md"
OUTPUT = SCRIPT_DIR / "index.html"
DOCS_DIR = SCRIPT_DIR.parent / "docs"
# 多页站（GitHub Pages）的根地址。单文件页与多页站首页内容相同，canonical 指向多页站，
# 避免两个首页在搜索结果里互相抢同一个查询；抽屉里的专题文档也链到多页站的 .html，
# 而不是浏览器会当成裸文本打开的 ../docs/*.md。可用环境变量 SITE_URL 覆盖（与 pages.yml 同名）。
SITE_URL = os.environ.get("SITE_URL", "https://hjm-al.github.io/nuoapi-tutorial").rstrip("/")

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
    """模拟 GitHub 给标题生成锚点的规则：保留中文，小写，每个空格变连字符。"""
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"[^\w\s-]", "", value.lower(), flags=re.UNICODE)
    return re.sub(r"\s", separator, value).strip(separator)


def docs_drawer_html() -> str:
    """抽屉里的专题文档列表：每篇 ``docs/*.md`` 一条，链到多页站对应的 ``.html``。

    标签用正文一级标题（不用 SEO 标题，避免品牌词在导航里重复）。
    单文件页是中文入口，只列中文文档；``docs/<slug>.<locale>.md`` 属于多页站
    的语言版本，不能在这里重复成一套近似目录。
    """
    items = []
    # Path 在 Windows 上按大小写不敏感规则比较，Linux 上则按码点比较。
    # 固定用文件名字符串作键，保证单文件抽屉在本地与 CI 生成相同顺序。
    for path in sorted(DOCS_DIR.glob("*.md"), key=lambda item: item.name):
        if any(path.stem.endswith("." + locale) for locale in ("en", "ja", "zh-Hant")):
            continue
        _meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
        match = re.search(r"^#\s+(.+)$", body, flags=re.M)
        label = match.group(1).strip() if match else path.stem
        href = "{0}/docs/{1}.html".format(SITE_URL, path.stem)
        items.append(
            "<li><a href=\"{0}\" target=\"_blank\" rel=\"noopener noreferrer\">{1}</a></li>".format(
                html.escape(href, quote=True), html.escape(label)
            )
        )
    if not items:
        return ""
    return (
        '<div class="toc docs-toc">'
        '<div class="drawer-section">专题文档</div>'
        "<ul>{0}</ul></div>".format("".join(items))
    )


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
<link rel="canonical" href="__CANONICAL__">
<title>__TITLE__</title>
__CSS__
</head>
<body>
<div id="progress"></div>
<header class="appbar">
  <button id="menuBtn" class="menu-btn" aria-label="打开目录">&#9776;</button>
  <div class="brand">
    <div class="brand-mark" aria-hidden="true">N</div>
    <div>
      <div class="appbar-title">__SITE_SHORT__</div>
      <div class="appbar-sub">离线单页版 · 构建于 __GEN_DATE__</div>
    </div>
  </div>
  <div class="appbar-actions"><button id="themeBtn" class="icon-btn" type="button" title="切换主题"><span class="i-light">&#9788;</span><span class="i-dark">&#9790;</span></button></div>
</header>

<div id="mask"></div>
<nav id="drawer" aria-label="教程目录">
  <div class="drawer-head">
    <strong>教程目录</strong>
    <button id="drawerClose" class="drawer-close" aria-label="关闭目录">&times;</button>
  </div>
  <div class="drawer-body">__TOC__</div>
</nav>

<div class="page">
<article>
__CONTENT__
</article>
<aside class="page-side"><div class="side-title">本页目录</div>__SIDE_TOC__</aside>
</div>

__FOOTER__

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
    page_toc = fix_relative_links(md.toc)
    toc = '<div class="drawer-section">本页章节</div>' + page_toc + docs_drawer_html()

    title_match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "教程"
    # 搜索结果里显示的标题/摘要优先取 Markdown 头部的显式声明
    display_title = meta.get("title") or title
    description = meta.get("description") or (
        "把 Codex、Claude Code、Gemini CLI 等客户端接入第三方 AI 网关，并用可复现的探针核对模型真伪；结论只有匹配 / 不匹配 / 证据不足"
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
        "__CANONICAL__": html.escape(SITE_URL + "/", quote=True),
        "__TOC__": toc,
        "__SIDE_TOC__": page_toc,
        "__GEN_DATE__": gen_date,
        "__SITE_SHORT__": html.escape(SITE_SHORT, quote=True),
        "__FOOTER__": footer_html("README.md"),
        "__CSS__": CSS,
        "__JS__": JS.replace("__JS_I18N__", interaction_copy_json("zh-CN")),
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
