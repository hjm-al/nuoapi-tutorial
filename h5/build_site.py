# -*- coding: utf-8 -*-
"""把仓库内的 Markdown 文档构建成可部署到 GitHub Pages 的多页静态站。

与 ``h5/build_h5.py`` 的区别：

- ``build_h5.py`` → 单文件离线页 ``h5/index.html``（只有 README，供离线/移动端分享）；
- ``build_site.py`` → 多页站点，每篇 ``docs/*.md``、``FAQ.md``、``README.md``
  各成一个可被搜索引擎单独收录的页面，附带 sitemap / robots / canonical /
  Open Graph / 结构化数据，并由 GitHub Actions 部署到 Pages。

用法（本机构建，输出目录已被 .gitignore 排除）::

    python h5/build_site.py --base-url https://<user>.github.io/nuoapi-tutorial
    python h5/build_site.py --out h5/_site --repo-url https://github.com/<user>/nuoapi-tutorial

设计约束：

1. 与 ``build_h5.py`` 共用 ``h5/theme.py`` 的 CSS/JS，两套产物外观不漂移。
2. 站点内 Markdown 链接改写成 ``.html`` 站内路径；指向脚本/模板/xlsx 的链接
   改写成 GitHub 仓库地址（Pages 不托管这些文件）；外链统一 ``target=_blank``。
3. 构建后自检每一条站内链接都有对应产物，避免出现新的 404（CI 会跑）。
4. Markdown 可用 ``---`` 头的 ``title:`` / ``description:`` 覆盖页面标题与摘要（见
   ``split_frontmatter``）：搜索结果里显示的就是这两行，标题越短越不容易被截断。
   没有头就退回“标题 + 站点名”“首段正文”，行为与旧版一致。
"""

import argparse
import html
import json
import os
import posixpath
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

import markdown

from theme import CSS, JS
from build_h5 import github_slug

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DEFAULT_OUT = SCRIPT_DIR / "_site"

# 页面清单：源文件 → 站点内路径
PAGES = [
    (Path("README.md"), "index.html"),
    (Path("FAQ.md"), "faq.html"),
    (Path("examples/README.md"), "examples.html"),
]


def discover_docs() -> list:
    """docs/ 下所有 Markdown 都独立成页，按文件名排序保证输出稳定。"""
    docs = sorted((ROOT / "docs").glob("*.md"))
    return [(p.relative_to(ROOT), "docs/{0}.html".format(p.stem)) for p in docs]


MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
FENCE = re.compile(r"^\s*```")
# Markdown 头部的 SEO 键值块。用 HTML 注释包着，是为了它在两个渲染面（GitHub
# 文件页 / 本站构建）都不可见，不会变成正文里多出来的一段文字：
#   <!-- seo-meta
#     title: 搜索结果里的标题（含品牌词，建议 ≤30 汉字）
#     description: 搜索结果里的两行摘要（首 60 字内交代读者能得到什么）
#   -->
FRONTMATTER = re.compile(r"\A<!--\s*seo-meta\s*\n(.*?)\n\s*-->[ \t]*(?:\n|\Z)", re.S)

# 站点不托管的文件后缀：这类链接改为指向 GitHub 仓库（源码/模板/表格）
REPO_ONLY_SUFFIXES = {
    ".py", ".ps1", ".sh", ".cs", ".go", ".mjs", ".php", ".rs", ".java", ".js",
    ".json", ".toml", ".yaml", ".yml", ".example", ".service", ".env",
    ".xlsx", ".csv", ".txt", ".gitignore", "",
}


def split_frontmatter(md_text: str):
    """拆出 ``<!-- seo-meta -->`` 头里的 title / description，返回 (meta, 正文)。

    只认简单的 ``key: value`` 行，不引入 YAML 依赖；没有头就原样返回，
    所以旧文档不加头也能构建。
    """
    match = FRONTMATTER.match(md_text)
    if not match:
        return {}, md_text
    meta = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        key = key.strip().lower()
        if key in ("title", "description") and value.strip():
            meta[key] = value.strip()
    return meta, md_text[match.end():]


def first_heading(md_text: str) -> str:
    match = re.search(r"^#\s+(.+)$", md_text, flags=re.M)
    return match.group(1).strip() if match else ""


def plain_text(md_text: str) -> str:
    """抽出用于 <meta description> 的纯文本。"""
    text = re.sub(r"```.*?```", " ", md_text, flags=re.S)
    text = re.sub(r"^#+\s*", "", text, flags=re.M)
    text = MD_LINK.sub(r"\1", text)
    text = re.sub(r"[*_`>|]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def page_description(md_text: str, limit: int = 150) -> str:
    """取标题后第一段可读正文作为描述，控制长度（中文按字符算）。"""
    body = re.sub(r"\A\s*#\s+.+?$", "", md_text, count=1, flags=re.M)
    for block in re.split(r"\n\s*\n", body):
        block = block.strip()
        if not block or block.startswith((">", "|", "#", "-", "*", "```")) or set(block) <= set("-|: "):
            continue
        text = plain_text(block)
        if len(text) >= 40:
            return text[:limit].rstrip(" ,，。;；") + ("…" if len(text) > limit else "")
    return plain_text(body)[:limit]


def is_external(url: str) -> bool:
    return url.startswith(("http://", "https://", "mailto:", "tel:", "data:"))


def link_from(current_dst: str, target_dst: str) -> str:
    """生成从当前页指向目标页的相对路径（站点必须能放在 /repo/ 子路径下）。"""
    start = posixpath.dirname(current_dst) or "."
    return posixpath.relpath(target_dst, start)


def resolve_link(source: Path, target: str, page_paths: dict, repo_url: str,
                 current_dst: str) -> str:
    """把 Markdown 链接改成站点路径或 GitHub 地址。

    - ``.md`` → 对应站点页面（保留锚点，锚点 slug 与 GitHub 规则一致）
    - 目录 → GitHub 仓库对应目录
    - 其他文件（脚本/模板/xlsx）→ GitHub blob 地址
    """
    file_part, _, anchor = target.partition("#")
    if not file_part:
        return "#" + anchor
    if is_external(file_part):
        suffix = "#" + anchor if anchor else ""
        return file_part + suffix

    resolved = (ROOT / source).parent / file_part
    try:
        rel = resolved.resolve().relative_to(ROOT)
    except ValueError:
        return file_part + (("#" + anchor) if anchor else "")

    rel_posix = rel.as_posix().rstrip("/")
    frag = ("#" + anchor) if anchor else ""

    if rel.suffix == ".md" and rel_posix in page_paths:
        return link_from(current_dst, page_paths[rel_posix]) + frag
    if rel.suffix == ".md":
        # 未纳入站点的 Markdown（理论上不存在）退回仓库地址，避免站内 404
        return "{0}/blob/main/{1}{2}".format(repo_url, rel_posix, frag)
    if not rel.suffix and rel.is_dir():
        return "{0}/tree/main/{1}".format(repo_url, rel_posix)
    return "{0}/blob/main/{1}{2}".format(repo_url, rel_posix, frag)


def rewrite_links(html_text: str, source: Path, page_paths: dict, repo_url: str,
                  current_dst: str) -> str:
    """只改写正文 HTML 的 href（跳过代码块产生的内容不必要：代码块里没有 <a>）。"""

    def repl(match: re.Match) -> str:
        attr, url = match.group(1), match.group(2)
        if url.startswith("#") or url.startswith(("mailto:", "tel:", "data:")):
            return match.group(0)
        new_url = resolve_link(source, url, page_paths, repo_url, current_dst)
        return '{0}="{1}"'.format(attr, new_url)

    html_text = re.sub(r'\b(href|src)="([^"]+)"', repl, html_text)
    # 外链新窗口打开
    html_text = re.sub(
        r'<a href="(https?://[^"]+)"',
        r'<a target="_blank" rel="noopener noreferrer" href="\1"',
        html_text,
    )
    return html_text


def wrap_tables(html_text: str) -> str:
    return html_text.replace("<table>", '<div class="table-wrap"><table>').replace(
        "</table>", "</table></div>"
    )


def faq_jsonld(md_text: str, page_url: str, site_name: str) -> str:
    """从 FAQ.md 的二级标题 + 紧随正文生成 FAQPage 结构化数据。

    Google 要求标记内容与页面上可见内容一致，这里抽取的正是页面渲染的同一段文字。
    """
    entries = []
    blocks = re.split(r"^## +(?=\d+\.)", md_text, flags=re.M)[1:]
    for block in blocks:
        lines = block.splitlines()
        if not lines:
            continue
        question = lines[0].strip()
        answer = plain_text("\n".join(lines[1:]))
        if question and len(answer) >= 20:
            entries.append(
                {
                    "@type": "Question",
                    "name": question,
                    "acceptedAnswer": {"@type": "Answer", "text": answer[:1200]},
                }
            )
    if not entries:
        return ""
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "name": site_name,
        "url": page_url,
        "mainEntity": entries,
    }
    return '<script type="application/ld+json">{0}</script>'.format(
        json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    )


SITE_CSS = """
.layout{max-width:1120px;margin:0 auto;padding:0 16px}
.side{display:none}
.crumb{max-width:760px;margin:14px auto 0;padding:0 16px;font-size:12.5px;color:var(--muted)}
.crumb a{color:var(--muted);text-decoration:none}
.side-nav{list-style:none;margin:0;padding:0}
.side-nav li{margin:2px 0}
.side-nav a{display:block;padding:7px 10px;border-radius:8px;font-size:13.5px;
  color:#374151;text-decoration:none;line-height:1.5}
.side-nav a:hover{background:var(--primary-soft)}
.side-nav a.current{background:var(--primary-soft);color:var(--primary);font-weight:600}
.side-title{font-size:11px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--muted);margin:18px 0 6px;padding:0 10px}
.toc-box{background:#f8fafc;border:1px solid var(--border);border-radius:10px;
  padding:12px 14px;margin:16px 0 22px;font-size:13.5px}
.toc-box strong{display:block;font-size:12px;letter-spacing:.06em;color:var(--muted);
  margin-bottom:6px;text-transform:uppercase}
.toc-box ul{list-style:none;margin:0;padding:0}
.toc-box ul ul{padding-left:14px}
.toc-box a{display:block;padding:3px 0;color:#374151;text-decoration:none;border:none}
.toc-box a:hover{color:var(--primary)}
.pager{max-width:760px;margin:0 auto;padding:0 16px 8px;display:flex;
  justify-content:space-between;gap:12px;font-size:13.5px}
.pager a{color:var(--primary);text-decoration:none}
.site-footer a{color:var(--muted)}
@media (min-width:900px){
  .layout{display:flex;gap:32px;align-items:flex-start}
  .side{display:block;width:246px;flex:0 0 246px;position:sticky;top:64px;
    max-height:calc(100vh - 84px);overflow-y:auto;padding:18px 0 40px}
  .layout article{margin:0;flex:1;min-width:0;max-width:820px}
  .menu-btn{display:none}
  .crumb{max-width:none}
}
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#2563eb">
<title>__TITLE__</title>
<meta name="description" content="__DESC__">
<link rel="canonical" href="__CANONICAL__">
<meta property="og:type" content="article">
<meta property="og:site_name" content="__SITE_NAME__">
<meta property="og:title" content="__TITLE__">
<meta property="og:description" content="__DESC__">
<meta property="og:url" content="__CANONICAL__">
<meta property="og:locale" content="zh_CN">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="__TITLE__">
<meta name="twitter:description" content="__DESC__">
__NOINDEX____JSONLD__
__CSS__
__SITE_CSS__
</head>
<body>
<div id="progress"></div>
<header class="appbar">
  <button id="menuBtn" class="menu-btn" aria-label="打开导航">&#9776;</button>
  <div>
    <div class="appbar-title">__SITE_NAME__</div>
    <div class="appbar-sub">__PAGE_LABEL__</div>
  </div>
</header>

<div id="mask"></div>
<nav id="drawer" aria-label="站点导航">
  <div class="drawer-head">
    <strong>全部文档</strong>
    <button id="drawerClose" class="drawer-close" aria-label="关闭导航">&times;</button>
  </div>
  <div class="drawer-body">__DRAWER_NAV__</div>
</nav>

<div class="crumb"><a href="__HOME__">首页</a> / __PAGE_LABEL__</div>

<div class="layout">
  <aside class="side">__SIDE_NAV__</aside>
  <article>
__CONTENT__
  </article>
</div>

<div class="pager">__PAGER__</div>

<footer class="site-footer">
  本页由仓库 Markdown 自动构建 · 示例代码采用 MIT 许可证 · 内容带取证窗口日期，价格与可用性以
  <a href="https://nuoapi.net" target="_blank" rel="noopener noreferrer">nuoapi.net</a> 控制台实时显示为准<br>
  本工具箱不提供、不代售任何 API 服务，不构成投资或购买建议<br>
  <a href="__REPO_URL__" target="_blank" rel="noopener noreferrer">GitHub 仓库</a>
</footer>

<button id="toTop" aria-label="回到顶部">&#8593;</button>

__JS__
</body>
</html>
"""


def build(base_url: str, repo_url: str, out_dir: Path) -> int:
    return SiteBuilder(base_url, repo_url, out_dir).build()


class SiteBuilder:
    """可复用的站点构建器：测试直接调用 build()，无需起子进程。"""

    def __init__(self, base_url: str, repo_url: str, out_dir: Path):
        self.base_url = base_url.rstrip("/")
        self.repo_url = repo_url.rstrip("/")
        self.out_dir = Path(out_dir)
        self.errors = []

    def build(self) -> int:
        base_url, repo_url, out_dir = self.base_url, self.repo_url, self.out_dir
        pages = PAGES + discover_docs()
        page_paths = {src.as_posix(): dst for src, dst in pages}
        site_name = "第三方 AI 网关接入教程与防掺水取证工具箱"
        base = base_url.rstrip("/")

        nav_items = []
        for src, dst in pages:
            # 导航用正文大标题，不用 SEO 标题（后者带品牌词，列表里会重复冗余）
            raw = (ROOT / src).read_text(encoding="utf-8")
            meta, body = split_frontmatter(raw)
            nav_items.append((dst, first_heading(body) or dst))

        out_dir.mkdir(parents=True, exist_ok=True)
        written = []
        link_checks = []
        errors = self.errors

        for index, (src, dst) in enumerate(pages):
            md_text = (ROOT / src).read_text(encoding="utf-8")
            meta, md_text = split_frontmatter(md_text)

            md = markdown.Markdown(
                extensions=["fenced_code", "tables", "sane_lists", "toc"],
                extension_configs={"toc": {"slugify": github_slug, "toc_depth": "2-3"}},
            )
            content = wrap_tables(md.convert(md_text))
            content = rewrite_links(content, src, page_paths, repo_url, dst)
            toc = md.toc

            page_title = first_heading(md_text) or dst
            is_home = dst == "index.html"
            # 有 frontmatter title 就整条覆盖（作者自己排品牌词，控长度）；否则标题 + 站点名
            title = meta.get("title") or "{0} | {1}".format(page_title, site_name)
            desc = meta.get("description") or page_description(md_text)
            canonical = base + "/" + ("" if is_home else dst)
            canonical = canonical.replace("/index.html", "/")

            drawer_nav = "<ul class=\"toc\">{0}</ul>".format(
                "".join(
                    '<li><a href="{0}"{1}>{2}</a></li>'.format(
                        link_from(dst, href), ' class="current"' if href == dst else "", html.escape(label)
                    )
                    for href, label in nav_items
                )
            )
            side_nav = '<div class="side-title">全部文档</div><ul class="side-nav">{0}</ul>'.format(
                "".join(
                    '<li><a href="{0}"{1}>{2}</a></li>'.format(
                        link_from(dst, href), ' class="current"' if href == dst else "", html.escape(label)
                    )
                    for href, label in nav_items
                )
            )

            prev_link = next_link = ""
            if index > 0:
                prev_link = '<a href="{0}">← {1}</a>'.format(
                    link_from(dst, nav_items[index - 1][0]), html.escape(nav_items[index - 1][1]))
            if index < len(nav_items) - 1:
                next_link = '<a href="{0}">{1} →</a>'.format(
                    link_from(dst, nav_items[index + 1][0]), html.escape(nav_items[index + 1][1]))
            pager = '<span>{0}</span><span>{1}</span>'.format(prev_link, next_link)

            jsonld = faq_jsonld(md_text, canonical, site_name) if src.name == "FAQ.md" else ""
            label = "首页" if is_home else page_title

            page_html = (
                TEMPLATE.replace("__CSS__", CSS)
                .replace("__SITE_CSS__", "<style>{0}</style>".format(SITE_CSS))
                .replace("__JS__", JS)
                .replace("__SITE_NAME__", html.escape(site_name, quote=True))
                .replace("__TITLE__", html.escape(title, quote=True))
                .replace("__DESC__", html.escape(desc, quote=True))
                .replace("__CANONICAL__", html.escape(canonical, quote=True))
                .replace("__PAGE_LABEL__", html.escape(label, quote=True))
                .replace("__HOME__", html.escape(link_from(dst, "index.html"), quote=True))
                .replace("__REPO_URL__", html.escape(repo_url, quote=True))
                .replace("__DRAWER_NAV__", drawer_nav)
                .replace("__SIDE_NAV__", side_nav + ('<div class="toc-box"><strong>本页目录</strong>{0}</div>'.format(toc) if toc else ""))
                .replace("__PAGER__", pager)
                .replace("__NOINDEX__", "")
                .replace("__JSONLD__", jsonld)
            )
            # 正文最后拼接，避免正文内的占位符字样被替换
            page_html = page_html.replace("__CONTENT__", content)
            target = out_dir / dst
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(page_html, encoding="utf-8")
            written.append(dst)

        for dst, page_html in link_checks:
            for href in re.findall(r'href="([^"]+)"', page_html):
                if is_external(href) or href.startswith("#"):
                    continue
                target_rel = posixpath.normpath(
                    posixpath.join(posixpath.dirname(dst) or ".", href.split("#")[0])
                )
                if not (out_dir / target_rel).exists():
                    errors.append("{0}: 死链 {1}".format(dst, href))

        today = date.today().isoformat()
        urls = []
        for _, dst in pages:
            loc = base + "/" + ("" if dst == "index.html" else dst)
            loc = loc.replace("/index.html", "/")
            urls.append(
                "  <url><loc>{0}</loc><lastmod>{1}</lastmod><changefreq>weekly</changefreq>"
                "<priority>{2}</priority></url>".format(
                    html.escape(loc), today, "1.0" if dst == "index.html" else "0.8"
                )
            )
        (out_dir / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls)
            + "\n</urlset>\n",
            encoding="utf-8",
        )
        (out_dir / "robots.txt").write_text(
            "User-agent: *\nAllow: /\n\nSitemap: {0}/sitemap.xml\n".format(base), encoding="utf-8"
        )
        # Pages 默认用 Jekyll 处理，.nojekyll 让下划线开头的路径原样发布
        (out_dir / ".nojekyll").write_text("", encoding="utf-8")

        print("built {0} pages -> {1}".format(len(written), out_dir))
        if errors:
            print("LINK ERRORS:", file=sys.stderr)
            for e in errors:
                print("  " + e, file=sys.stderr)
            return 1
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="构建 GitHub Pages 多页教程站")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("SITE_URL", "https://YOUR_GITHUB_USER.github.io/nuoapi-tutorial"),
        help="站点根地址（含仓库子路径），用于 canonical / sitemap",
    )
    parser.add_argument(
        "--repo-url",
        default=os.environ.get("REPO_URL", "https://github.com/YOUR_GITHUB_USER/nuoapi-tutorial"),
        help="GitHub 仓库地址，用于源码/模板/表格链接",
    )
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="输出目录")
    args = parser.parse_args()
    return build(args.base_url, args.repo_url, Path(args.out))


if __name__ == "__main__":
    raise SystemExit(main())
