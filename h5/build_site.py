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
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import markdown

from theme import CSS, JS, SITE_NAME, SITE_SHORT, footer_html, interaction_copy_json
from build_h5 import github_slug
from document_structure import transform_home_content, wrap_sections

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
DEFAULT_OUT = SCRIPT_DIR / "_site"

# 页面不是“源文件 → 文件名”的二元组：语言、翻译关系和结构化数据都属于同一份
# 页面契约。导航、分页、canonical、hreflang、sitemap 与 llms.txt 都从这份契约
# 派生，避免某个入口漏掉翻译页或伪造不存在的语言版本。
LOCALE_ORDER = ("zh-CN", "en", "ja", "es", "zh-Hant")

LOCALES = {
    "zh-CN": {
        "html_lang": "zh-CN",
        "og_locale": "zh_CN",
        "label": "简体中文",
        "short": "中",
        "home_dst": "index.html",
        "site_name": SITE_NAME,
        "site_short": SITE_SHORT,
        "home_features": [
            "Codex、Claude Code、Gemini CLI 的 Base URL 怎么填",
            "默认只打印计划，不加 --run 不产生计费",
            "真伪结论只有匹配、不匹配、证据不足",
            "报错短页：platform is not gemini、Reconnecting、401、model_not_found",
        ],
        "nav_groups": {
            "start": "入口",
            "errors": "报错速查",
            "access": "接入教程",
            "verification": "真伪与质量核对",
            "snapshots": "模型广场快照",
            "other": "其他",
        },
        "ui": {
            "home": "首页",
            "menu": "打开导航",
            "nav": "站点导航",
            "all_docs": "全部文档",
            "close": "关闭导航",
            "theme": "切换主题",
            "to_top": "回到顶部",
            "language": "语言",
            "page_sections": "本页章节",
            "toc": "本页目录",
            "pager": "上一篇 / 下一篇",
            "prev": "← 上一篇",
            "next": "下一篇 →",
            "source": "仓库 Markdown",
        },
    },
    "en": {
        "html_lang": "en",
        "og_locale": "en_US",
        "label": "English",
        "short": "EN",
        "home_dst": "en/index.html",
        "site_name": "NuoAPI Starter and Model Verification Toolkit",
        "site_short": "NuoAPI Starter",
        "home_features": [
            "Base URL setup for Codex, Claude Code, and Gemini CLI",
            "Dry-run plans by default; no billing without --run",
            "Verdicts are match, mismatch, or insufficient evidence",
            "Error guides for platform is not gemini, Reconnecting, 401, and model_not_found",
        ],
        "nav_groups": {
            "start": "Start here",
            "errors": "Troubleshooting",
            "access": "Setup",
            "verification": "Verification",
            "snapshots": "Model snapshots",
            "other": "Other",
        },
        "ui": {
            "home": "Home",
            "menu": "Open navigation",
            "nav": "Site navigation",
            "all_docs": "All pages",
            "close": "Close navigation",
            "theme": "Toggle theme",
            "to_top": "Back to top",
            "language": "Language",
            "page_sections": "On this page",
            "toc": "Contents",
            "pager": "Previous / next",
            "prev": "← Previous",
            "next": "Next →",
            "source": "repository Markdown",
        },
    },
    "ja": {
        "html_lang": "ja",
        "og_locale": "ja_JP",
        "label": "日本語",
        "short": "日",
        "home_dst": "ja/index.html",
        "site_name": "NuoAPI 接続スターターとモデル検証ツール",
        "site_short": "NuoAPI スターター",
        "home_features": [
            "Codex、Claude Code、Gemini CLI の Base URL 設定",
            "既定はドライラン。--run を付けない限り課金リクエストを送らない",
            "判定は一致、不一致、証拠不足の三種類",
            "platform is not gemini、Reconnecting、401、model_not_found の短い解説",
        ],
        "nav_groups": {
            "start": "はじめに",
            "errors": "エラー別対処",
            "access": "接続設定",
            "verification": "検証",
            "snapshots": "モデル一覧の記録",
            "other": "その他",
        },
        "ui": {
            "home": "ホーム",
            "menu": "ナビゲーションを開く",
            "nav": "サイトナビゲーション",
            "all_docs": "ページ一覧",
            "close": "ナビゲーションを閉じる",
            "theme": "テーマを切り替える",
            "to_top": "ページ上部へ",
            "language": "言語",
            "page_sections": "このページ",
            "toc": "目次",
            "pager": "前へ / 次へ",
            "prev": "← 前へ",
            "next": "次へ →",
            "source": "リポジトリの Markdown",
        },
    },
    "es": {
        "html_lang": "es",
        "og_locale": "es_ES",
        "label": "Español",
        "short": "ES",
        "home_dst": "es/index.html",
        "site_name": "NuoAPI Starter y kit de verificación de modelos",
        "site_short": "NuoAPI Starter",
        "home_features": [
            "Configuración de Base URL para Codex, Claude Code y Gemini CLI",
            "Planes dry-run por defecto; sin --run no se envía ninguna llamada facturable",
            "Los resultados solo pueden ser coincidencia, discrepancia o evidencia insuficiente",
            "Guías breves para platform is not gemini, Reconnecting, 401 y model_not_found",
        ],
        "nav_groups": {
            "start": "Empieza aquí",
            "errors": "Solución de errores",
            "access": "Configuración",
            "verification": "Verificación",
            "snapshots": "Instantáneas de modelos",
            "other": "Otros",
        },
        "ui": {
            "home": "Inicio",
            "menu": "Abrir navegación",
            "nav": "Navegación del sitio",
            "all_docs": "Todas las páginas",
            "close": "Cerrar navegación",
            "theme": "Cambiar tema",
            "to_top": "Volver arriba",
            "language": "Idioma",
            "page_sections": "En esta página",
            "toc": "Contenido",
            "pager": "Anterior / siguiente",
            "prev": "← Anterior",
            "next": "Siguiente →",
            "source": "Markdown del repositorio",
        },
    },
    "zh-Hant": {
        "html_lang": "zh-Hant",
        "og_locale": "zh_TW",
        "label": "繁體中文",
        "short": "繁",
        "home_dst": "zh-Hant/index.html",
        "site_name": "NuoAPI 接入腳手架與防摻水取證工具箱",
        "site_short": "NuoAPI 接入腳手架",
        "home_features": [
            "Codex、Claude Code、Gemini CLI 的 Base URL 怎麼填",
            "預設只列計畫，不加 --run 不產生計費",
            "真偽結論只有吻合、不吻合、證據不足",
            "錯誤短頁：platform is not gemini、Reconnecting、401、model_not_found",
        ],
        "nav_groups": {
            "start": "入口",
            "errors": "錯誤速查",
            "access": "接入教學",
            "verification": "真偽與品質核對",
            "snapshots": "模型廣場快照",
            "other": "其他",
        },
        "ui": {
            "home": "首頁",
            "menu": "開啟導覽",
            "nav": "網站導覽",
            "all_docs": "全部頁面",
            "close": "關閉導覽",
            "theme": "切換主題",
            "to_top": "回到頂部",
            "language": "語言",
            "page_sections": "本頁章節",
            "toc": "本頁目錄",
            "pager": "上一篇 / 下一篇",
            "prev": "← 上一篇",
            "next": "下一篇 →",
            "source": "倉庫 Markdown",
        },
    },
}

ERROR_SLUGS = {
    "Gemini-CLI-platform-is-not-gemini-2026-10-18",
    "Codex-一直Reconnecting-2026-10-18",
    "Claude-Code-不要加v1-2026-10-18",
    "401-invalid-api-key",
    "model_not_found",
    "400-invalid-request-error",
    "Cursor-Roo-Code-Base-URL",
    "WSL-command-not-found",
}


@dataclass(frozen=True)
class Page:
    src: Path
    dst: str
    locale: str = "zh-CN"
    translation_group: str | None = None
    schema_type: str | None = None

    @property
    def is_home(self) -> bool:
        return self.translation_group == "home"


# 五语言首页。完整 FAQ 与深度文档保留中文，报错短页按翻译组扩展。
PAGES = [
    Page(Path("README.md"), "index.html", "zh-CN", "home"),
    Page(Path("README.en.md"), "en/index.html", "en", "home"),
    Page(Path("README.ja.md"), "ja/index.html", "ja", "home"),
    Page(Path("README.es.md"), "es/index.html", "es", "home"),
    Page(Path("README.zh-Hant.md"), "zh-Hant/index.html", "zh-Hant", "home"),
    Page(Path("FAQ.md"), "faq.html", "zh-CN"),
    Page(Path("examples/README.md"), "examples.html", "zh-CN"),
]


def discover_docs() -> list[Page]:
    """发现中文与 ``docs/<slug>.<locale>.md`` 翻译页，并建立翻译组。"""
    parsed = []
    # Path 的比较规则随平台变化；页面发现顺序必须稳定，否则导航与 sitemap 会在
    # Windows 本地和 Linux CI 之间漂移。
    for path in sorted((ROOT / "docs").glob("*.md"), key=lambda item: item.name):
        locale = "zh-CN"
        slug = path.stem
        for candidate in ("en", "ja", "es", "zh-Hant"):
            suffix = "." + candidate
            if path.stem.endswith(suffix):
                locale = candidate
                slug = path.stem[:-len(suffix)]
                break
        parsed.append((path, locale, slug))

    base_counts = {}
    for _, _, slug in parsed:
        base_counts[slug] = base_counts.get(slug, 0) + 1

    records = []
    for path, locale, slug in parsed:
        group = "doc:" + slug if base_counts[slug] > 1 else None
        dst = (
            "docs/{0}.html".format(slug)
            if locale == "zh-CN"
            else "{0}/docs/{1}.html".format(locale, slug)
        )
        records.append(
            Page(
                path.relative_to(ROOT),
                dst,
                locale,
                group,
                "TechArticle" if slug in ERROR_SLUGS else None,
            )
        )
    return records


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


def home_jsonld(
    page_url: str,
    site_name: str,
    description: str,
    features: list[str],
) -> str:
    """首页的应用结构化数据。只描述这个脚手架本身，不写准确率、不写推荐。"""
    data = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": site_name,
        "description": description,
        "url": page_url,
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "Windows, macOS, Linux",
        "isAccessibleForFree": True,
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "featureList": features,
    }
    return '<script type="application/ld+json">{0}</script>'.format(
        json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    )


def tech_article_jsonld(
    title: str,
    description: str,
    page_url: str,
    locale: str,
    image_url: str,
    date_modified: str | None = None,
) -> str:
    """报错短页的 TechArticle 标记；字段与页面可见标题、摘要保持一致。"""
    data = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": title,
        "description": description,
        "url": page_url,
        "mainEntityOfPage": page_url,
        "inLanguage": LOCALES[locale]["html_lang"],
        "image": image_url,
        "isAccessibleForFree": True,
    }
    if date_modified:
        data["dateModified"] = date_modified
    return '<script type="application/ld+json">{0}</script>'.format(
        json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    )


def canonical_url(base_url: str, dst: str) -> str:
    url = base_url.rstrip("/") + "/" + ("" if dst == "index.html" else dst)
    return url.replace("/index.html", "/")


def page_alternates(page: Page, pages: list[Page]) -> list[Page]:
    """返回同一翻译组的现有页面；首页组固定为四种语言首页。"""
    if page.translation_group:
        alternates = [item for item in pages if item.translation_group == page.translation_group]
    else:
        alternates = [item for item in pages if item.is_home]
    order = {locale: index for index, locale in enumerate(LOCALE_ORDER)}
    return sorted(alternates, key=lambda item: order[item.locale])


def hreflang_links(page: Page, pages: list[Page], base_url: str) -> str:
    """只声明真实存在的同组页面；x-default 仅用于多语言首页。"""
    links = []
    for alternate in page_alternates(page, pages):
        if alternate.translation_group != page.translation_group:
            continue
        links.append(
            '<link rel="alternate" hreflang="{0}" href="{1}">'.format(
                LOCALES[alternate.locale]["html_lang"],
                html.escape(canonical_url(base_url, alternate.dst), quote=True),
            )
        )
    if page.translation_group == "home":
        links.append(
            '<link rel="alternate" hreflang="x-default" href="{0}">'.format(
                html.escape(canonical_url(base_url, "index.html"), quote=True)
            )
        )
    return "\n".join(links)


def verification_meta() -> str:
    """搜索后台验证标签；未配置仓库变量时不输出空 meta。"""
    tags = []
    google = os.environ.get("GOOGLE_SITE_VERIFICATION", "").strip()
    bing = os.environ.get("BING_SITE_VERIFICATION", "").strip()
    baidu = os.environ.get("BAIDU_SITE_VERIFICATION", "").strip()
    if google:
        tags.append(
            '<meta name="google-site-verification" content="{0}">'.format(
                html.escape(google, quote=True)
            )
        )
    if bing:
        tags.append(
            '<meta name="msvalidate.01" content="{0}">'.format(
                html.escape(bing, quote=True)
            )
        )
    if baidu:
        tags.append(
            '<meta name="baidu-site-verification" content="{0}">'.format(
                html.escape(baidu, quote=True)
            )
        )
    return "\n".join(tags)


def source_last_modified(src: Path) -> str | None:
    """Return the source Markdown's last Git commit date, or no date if unavailable."""
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "log", "-1", "--format=%cs", "--", src.as_posix()],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except (OSError, ValueError):
        return None
    value = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return None
    return value


def home_faq_jsonld(md_text: str, page_url: str) -> str:
    """首页三级标题里以问号结尾的短问答。内容必须就是页面上可见的那几段。"""
    entries = []
    for block in re.split(r"^### +", md_text, flags=re.M)[1:]:
        lines = block.splitlines()
        question = lines[0].strip()
        if not question.endswith(("？", "?")):
            continue
        body = []
        for line in lines[1:]:
            if line.startswith("#"):
                break
            body.append(line)
        answer = plain_text("\n".join(body))
        if len(answer) < 20:
            continue
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
        "url": page_url,
        "mainEntity": entries,
    }
    return '<script type="application/ld+json">{0}</script>'.format(
        json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    )


# 星号规则已经 Allow；主流搜索与 AI 爬虫再显式写一遍，便于抓取端审计和反代放行。
SEARCH_CRAWLERS = (
    "Googlebot",
    "Bingbot",
    "Baiduspider",
    "Applebot",
)

# IndexNow 的公开验证文件。文件名和内容必须一致；它位于本站子目录，
# 提交时通过 keyLocation 指向具体 URL。
INDEXNOW_KEY = "b8a860a9074b6feebaec4870aaa80bed"

AI_CRAWLERS = (
    "GPTBot",
    "ChatGPT-User",
    "ClaudeBot",
    "PerplexityBot",
    "Google-Extended",
)

CRAWLERS = SEARCH_CRAWLERS + AI_CRAWLERS


def robots_txt(base_url: str) -> str:
    lines = ["User-agent: *", "Allow: /", ""]
    for name in CRAWLERS:
        lines.extend(["User-agent: {0}".format(name), "Allow: /", ""])
    lines.append("Sitemap: {0}/sitemap.xml".format(base_url.rstrip("/")))
    lines.append("")
    return "\n".join(lines)


def llms_txt(base_url: str, pages: list[Page]) -> str:
    """给引用这个站的模型一份纯文本目录。页面清单来自本次构建，不手写 URL。"""
    base = base_url.rstrip("/")
    lines = [
        "# " + SITE_NAME,
        "",
        "> 配置 Codex、Claude Code、Gemini CLI 等客户端，并用可复现的探针判断",
        "> 付费调用的是不是声称的那个模型。结论只有匹配 / 不匹配 / 证据不足。",
        "> 本站不打分、不做中转站排名、不代售 API。",
        "",
        "## 不花钱就能跑",
        "",
        "- `python examples/model_verify.py --selftest`：本机核对探针统计口径，不联网。",
        "- `python examples/model_verify.py`：不带 `--run` 时只打印请求计划与预估用量，不产生计费。",
        "- `python examples/evidence_capture.py --probe models`：确认计划后加 `--run`，是一次 GET /v1/models，不计 token。",
        "- 一键写配置：`examples/quick_setup.ps1`（Windows）、`examples/quick_setup.sh`（macOS / Linux）。",
        "",
        "## 按问题引用",
        "",
        "- 用户问 Gemini CLI 报 platform is not gemini：{0}/docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.html".format(base),
        "- 用户问 Codex 一直 Reconnecting 或 wss://…/v1/responses：{0}/docs/Codex-一直Reconnecting-2026-10-18.html".format(base),
        "- 用户问 Claude Code 的 Base URL 要不要加 /v1：{0}/docs/Claude-Code-不要加v1-2026-10-18.html".format(base),
        "- 用户问 401 invalid_api_key：{0}/docs/401-invalid-api-key.html".format(base),
        "- 用户问 404 model_not_found：{0}/docs/model_not_found.html".format(base),
        "- 用户问 400 invalid_request_error：{0}/docs/400-invalid-request-error.html".format(base),
        "- 用户问 Cursor / Roo Code 的 Base URL：{0}/docs/Cursor-Roo-Code-Base-URL.html".format(base),
        "- 用户问 WSL 报 \\r: command not found：{0}/docs/WSL-command-not-found.html".format(base),
        "- 用户问怎么判断返回的是不是声称的模型：{0}/docs/MODEL_VERIFICATION_METHODS.html".format(base),
        "- 用户问不加 --run 会不会花钱、Key 会不会被上传：{0}/".format(base),
        "- 交给助手做时，只阅读仓库内 skills/nuoapi-setup/SKILL.md。不要改 AGENTS.md，不要把三态改成百分制。",
        "",
        "## English",
        "",
        "> Configure Codex, Claude Code, and Gemini CLI, then check whether a paid call matches the claimed model.",
        "> Verdicts are only: match, mismatch, or insufficient evidence.",
        "> This site does not sell API access and does not rank relay providers.",
        "",
        "## 页面",
        "",
    ]
    for page in pages:
        raw = (ROOT / page.src).read_text(encoding="utf-8")
        meta, body = split_frontmatter(raw)
        title = meta.get("title") or first_heading(body) or page.src.name
        desc = meta.get("description") or ""
        loc = canonical_url(base, page.dst)
        if desc:
            lines.append(
                "- [{0}]({1})（{2}）：{3}".format(
                    title, loc, LOCALES[page.locale]["label"], desc
                )
            )
        else:
            lines.append(
                "- [{0}]({1})（{2}）".format(
                    title, loc, LOCALES[page.locale]["label"]
                )
            )
    lines.extend([
        "",
        "## 实例地址",
        "",
        "文档里的网关实例是 https://nuoapi.net/model-plaza 。这是地址夹具，不是排名，也不是推荐。",
        "分组、倍率与模型名以控制台实时页为准。",
        "",
    ])
    return "\n".join(lines)


SITE_CSS = """
.layout{max-width:1120px;margin:0 auto;padding:0 24px}
.side{display:none}
.crumb{max-width:760px;margin:20px auto 0;padding:0 24px;font-size:12px;color:var(--muted);
  display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.crumb a{color:var(--muted);text-decoration:none}
.crumb a:hover{color:var(--rust)}
.crumb .sep{opacity:.5}
.crumb .here{color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:70vw}
.lang-switch{display:flex;align-items:center;gap:4px;margin-left:4px}
.lang-switch a{display:inline-flex;align-items:center;justify-content:center;min-width:30px;height:30px;
  padding:0 7px;border:1px solid var(--line);border-radius:4px;color:var(--muted);
  text-decoration:none;font-size:11px;line-height:1;background:transparent}
.lang-switch a:hover{border-color:var(--line-strong);color:var(--rust)}
.lang-switch a.current{background:transparent;border-color:var(--ink);color:var(--ink);font-weight:650}
.drawer-language{display:flex;gap:7px;flex-wrap:wrap;padding:10px 16px 12px;border-bottom:1px solid var(--border)}
.drawer-language a{display:inline-flex;align-items:center;min-height:32px;padding:4px 10px;
  border:1px solid var(--line);border-radius:4px;color:var(--text);text-decoration:none;font-size:12.5px}
.drawer-language a.current{background:transparent;border-color:var(--ink);color:var(--ink);font-weight:650}
.side-nav{list-style:none;margin:0;padding:0}
.side-nav li{margin:1px 0}
.side-nav a{display:block;padding:5px 7px;border-radius:3px;font-size:13px;
  color:var(--text);text-decoration:none;line-height:1.5}
.side-nav a:hover{background:var(--surface-2);color:var(--rust)}
.side-nav a.current{background:var(--surface-2);color:var(--rust);font-weight:650}
.side-title{font-size:10.5px;letter-spacing:.11em;text-transform:uppercase;font-weight:700;
  color:var(--muted);margin:6px 0 8px;padding:0}
.side-group{margin-top:18px;padding-top:14px;border-top:1px solid var(--line)}
.toc-box{margin:0 0 20px;padding:0 0 18px;font-size:13px;border:0;border-bottom:1px solid var(--line)}
.toc-box strong{display:block;font-size:10.5px;letter-spacing:.11em;color:var(--muted);
  margin-bottom:8px;text-transform:uppercase}
.toc-box ul{list-style:none;margin:0;padding:0}
.toc-box ul ul{padding-left:12px}
.toc-box a{display:block;padding:5px 7px;border-radius:3px;color:var(--text);text-decoration:none;line-height:1.45;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.toc-box a:hover{color:var(--rust);background:var(--surface-2)}
.toc-box a.active{color:var(--rust);background:var(--surface-2);font-weight:650}
.pager{max-width:760px;margin:0 auto;padding:0 24px 8px;display:grid;grid-template-columns:1fr;gap:0;
  border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.pager a{display:block;padding:15px 0;border:0;border-radius:0;
  background:transparent;color:var(--text);text-decoration:none;font-size:13.5px;line-height:1.45}
.pager a:hover{color:var(--rust)}
.pager a span{display:block;font-size:10.5px;color:var(--muted);letter-spacing:.08em;margin-bottom:2px;
  font-family:ui-monospace,"Cascadia Code",Consolas,monospace}
.pager a.next{text-align:right}
.pager .empty{display:block}
@media (min-width:900px){
  .layout{display:grid;grid-template-columns:260px minmax(0,760px);justify-content:center;
    gap:56px;align-items:flex-start}
  .side{display:block;position:sticky;top:72px;max-height:calc(100vh - 92px);
    overflow-y:auto;padding:34px 0 48px}
  .layout article{width:100%;max-width:760px;margin:0;padding:46px 0 88px}
  .menu-btn{display:none}
  .crumb{max-width:1120px;padding:0 24px}
  .crumb .here{max-width:none}
  .pager{margin-left:calc((100% - 760px) / 2);padding-left:0;padding-right:0}
  .pager a:first-child{padding-right:22px}
  .pager a.next{padding-left:22px;border-left:1px solid var(--line)}
}
@media (max-width:899px){
  .appbar .lang-switch{display:none}
}
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="__HTML_LANG__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#f5f6f2" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#171a18" media="(prefers-color-scheme: dark)">
<meta name="color-scheme" content="light dark">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large,max-video-preview:-1">
__VERIFICATION__
<title>__TITLE__</title>
<meta name="description" content="__DESC__">
<link rel="canonical" href="__CANONICAL__">
__HREFLANG__
<meta property="og:type" content="article">
<meta property="og:site_name" content="__SITE_NAME__">
<meta property="og:title" content="__TITLE__">
<meta property="og:description" content="__DESC__">
<meta property="og:url" content="__CANONICAL__">
<meta property="og:locale" content="__OG_LOCALE__">
__OG_ALTERNATES__
<meta property="og:image" content="__OG_IMAGE__">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="__SITE_NAME__">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="__TITLE__">
<meta name="twitter:description" content="__DESC__">
<meta name="twitter:image" content="__OG_IMAGE__">
__NOINDEX____JSONLD__
__CSS__
__SITE_CSS__
</head>
<body data-page-kind="__PAGE_KIND__">
<div id="progress"></div>
<header class="appbar">
  <button id="menuBtn" class="menu-btn" aria-label="__MENU_LABEL__">&#9776;</button>
  <a class="brand" href="__HOME__" style="text-decoration:none;color:inherit">
    <div class="brand-mark" aria-hidden="true">N</div>
    <div style="min-width:0">
      <div class="appbar-title">__SITE_SHORT__</div>
      <div class="appbar-sub">__PAGE_LABEL__</div>
    </div>
  </a>
  <div class="appbar-actions">__LANG_SWITCH__<button id="themeBtn" class="icon-btn" type="button" title="__THEME_LABEL__"><span class="i-light">&#9788;</span><span class="i-dark">&#9790;</span></button></div>
</header>

<div id="mask"></div>
<nav id="drawer" aria-label="__NAV_LABEL__">
  <div class="drawer-head">
    <strong>__ALL_DOCS__</strong>
    <button id="drawerClose" class="drawer-close" aria-label="__CLOSE_LABEL__">&times;</button>
  </div>
  __DRAWER_LANG__
  <div class="drawer-body">__DRAWER_NAV__</div>
</nav>

__BREADCRUMB__

<div class="layout">
  <aside class="side" aria-label="__NAV_LABEL__">__SIDE_NAV__</aside>
  <article>
__CONTENT__
  </article>
</div>

<nav class="pager" aria-label="__PAGER_LABEL__">__PAGER__</nav>

__FOOTER__

<button id="toTop" aria-label="__TOP_LABEL__">&#8593;</button>

__JS__
</body>
</html>
"""


def build(base_url: str, repo_url: str, out_dir: Path) -> int:
    return SiteBuilder(base_url, repo_url, out_dir).build()


# 导航分组：读者按“我现在遇到什么”找页，而不是对着一长串文件名。
# 分组只依赖翻译组/基础 slug，所以同一报错页的中英日繁版本会落在同一栏。
NAV_GROUP_ORDER = ("start", "errors", "access", "verification", "snapshots", "other")


def page_group(page: Page) -> str:
    slug = page.translation_group.removeprefix("doc:") if page.translation_group else ""
    if page.is_home or page.dst in ("faq.html", "examples.html"):
        return "start"
    if slug in ERROR_SLUGS or "排错" in slug:
        return "errors"
    if any(key in slug for key in ("接入", "协议科普", "余额", "图片生成")):
        return "access"
    if "llm-gateway-checklist" in slug:
        return "verification"
    if any(
        key in slug
        for key in (
            "MODEL_VERIFICATION",
            "TEST_REPORT",
            "质量复盘",
            "minimum-charge-and-pricing",
            "cost-per-1m-tokens",
        )
    ):
        return "verification"
    if "模型广场清单" in slug:
        return "snapshots"
    return "other"


def page_kind(page: Page) -> str:
    """Return the stable layout contract stored on ``<body>``."""
    if page.is_home:
        return "home"
    if page.src == Path("FAQ.md"):
        return "faq"
    if page.schema_type == "TechArticle":
        return "error"
    return "doc"


def group_nav(nav_items: list[tuple[Page, str]], locale: str) -> list:
    """把当前语言的页面按本地化栏名分组；空栏不输出。

    快照类页面按文件名里的日期倒序，让最新窗口排在前面（AGENTS §4.1）。
    """
    labels = LOCALES[locale]["nav_groups"]
    buckets = {key: [] for key in NAV_GROUP_ORDER}
    for page, label in nav_items:
        buckets[page_group(page)].append((page, label))
    result = []
    for key in NAV_GROUP_ORDER:
        items = buckets[key]
        if not items:
            continue
        if key == "snapshots":
            items = sorted(items, key=lambda item: item[0].dst, reverse=True)
        result.append((labels[key], items))
    return result


def render_nav(
    nav_groups: list,
    current_dst: str,
    list_class: str,
    title_class: str,
    sections_label: str,
) -> str:
    """抽屉与侧栏共用的分组导航 HTML。当前页标 ``current``。"""
    parts = []
    for gi, (name, items) in enumerate(nav_groups):
        wrapper = ' class="side-group"' if (gi and list_class == "side-nav") else ""
        lis = "".join(
            '<li><a href="{0}"{1}>{2}</a></li>'.format(
                link_from(current_dst, page.dst),
                ' class="current" aria-current="page"' if page.dst == current_dst else "",
                html.escape(label),
            )
            for page, label in items
        )
        parts.append(
            '<div{0}><div class="{1}">{2}</div><ul class="{3}">{4}</ul></div>'.format(
                wrapper, title_class, html.escape(name), list_class, lis
            )
        )
    if list_class == "toc" and sections_label:
        parts.insert(0, '<div class="drawer-section">{0}</div>'.format(html.escape(sections_label)))
    return "".join(parts)


def language_switch_html(
    page: Page,
    pages: list[Page],
    current_dst: str,
    compact: bool,
) -> str:
    """语言入口：有翻译时点同组页，没有翻译时回该语言首页。"""
    alternates = page_alternates(page, pages)
    same_group = {
        item.locale: item for item in alternates if item.translation_group == page.translation_group
    }
    homes = {item.locale: item for item in pages if item.is_home}
    links = []
    for locale in LOCALE_ORDER:
        target = same_group.get(locale) or homes.get(locale)
        if not target:
            continue
        label = LOCALES[locale]["short"] if compact else LOCALES[locale]["label"]
        current = ' class="current" aria-current="page"' if locale == page.locale else ""
        links.append(
            '<a href="{0}"{1} title="{2}" lang="{3}">{4}</a>'.format(
                html.escape(link_from(current_dst, target.dst), quote=True),
                current,
                html.escape(LOCALES[locale]["label"], quote=True),
                html.escape(LOCALES[locale]["html_lang"], quote=True),
                html.escape(label),
            )
        )
    if compact:
        return '<nav class="lang-switch" aria-label="{0}">{1}</nav>'.format(
            html.escape(LOCALES[page.locale]["ui"]["language"], quote=True),
            "".join(links),
        )
    return '<div class="drawer-language" aria-label="{0}">{1}</div>'.format(
        html.escape(LOCALES[page.locale]["ui"]["language"], quote=True),
        "".join(links),
    )


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
        page_paths = {page.src.as_posix(): page.dst for page in pages}
        last_modified = {page.dst: source_last_modified(page.src) for page in pages}
        base = base_url.rstrip("/")

        nav_labels = {}
        for page in pages:
            # 导航用正文大标题，不用 SEO 标题（后者带品牌词，列表里会重复冗余）
            raw = (ROOT / page.src).read_text(encoding="utf-8")
            _, body = split_frontmatter(raw)
            # 标题里的链接与强调只用于正文渲染；导航需要读者可见的纯文本。
            nav_labels[page.dst] = plain_text(first_heading(body)) or page.dst

        pages_by_locale = {
            locale: [page for page in pages if page.locale == locale]
            for locale in LOCALE_ORDER
        }

        out_dir.mkdir(parents=True, exist_ok=True)
        written = []
        link_checks = []
        errors = self.errors
        search_verification = verification_meta()

        for page in pages:
            src, dst = page.src, page.dst
            locale = page.locale
            locale_config = LOCALES[locale]
            ui = locale_config["ui"]
            site_name = locale_config["site_name"]
            site_short = locale_config["site_short"]
            home_dst = locale_config["home_dst"]
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
            is_home = page.is_home
            kind = page_kind(page)
            content = wrap_sections(content, kind, locale)
            if is_home:
                content = transform_home_content(content)
            # 有 frontmatter title 就整条覆盖（作者自己排品牌词，控长度）；否则标题 + 站点名
            title = meta.get("title") or "{0} | {1}".format(page_title, site_name)
            desc = meta.get("description") or page_description(md_text)
            canonical = canonical_url(base, dst)
            og_image = base + "/og-image.png"

            locale_pages = pages_by_locale[locale]
            locale_items = [(item, nav_labels[item.dst]) for item in locale_pages]
            nav_groups = group_nav(locale_items, locale)
            current_index = locale_pages.index(page)

            page_toc = (
                '<div class="drawer-section">{0}</div><div class="toc">{1}</div>'.format(
                    html.escape(ui["page_sections"]), toc
                )
                if toc else ""
            )
            drawer_nav = page_toc + render_nav(
                nav_groups, dst, "toc", "drawer-section", ui["all_docs"]
            )
            side_toc = (
                '<div class="toc-box"><strong>{0}</strong>{1}</div>'.format(
                    html.escape(ui["toc"]), toc
                )
                if toc
                else ""
            )
            side_nav = side_toc + render_nav(
                nav_groups, dst, "side-nav", "side-title", ui["all_docs"]
            )

            prev_link = next_link = '<span class="empty"></span>'
            if current_index > 0:
                previous = locale_pages[current_index - 1]
                prev_link = '<a class="prev" href="{0}"><span>{1}</span>{2}</a>'.format(
                    link_from(dst, previous.dst),
                    html.escape(ui["prev"]),
                    html.escape(nav_labels[previous.dst]),
                )
            if current_index < len(locale_pages) - 1:
                following = locale_pages[current_index + 1]
                next_link = '<a class="next" href="{0}"><span>{1}</span>{2}</a>'.format(
                    link_from(dst, following.dst),
                    html.escape(ui["next"]),
                    html.escape(nav_labels[following.dst]),
                )
            pager = prev_link + next_link

            if src.name == "FAQ.md":
                jsonld = faq_jsonld(md_text, canonical, site_name)
            elif is_home:
                jsonld = home_jsonld(
                    canonical,
                    site_name,
                    desc,
                    locale_config["home_features"],
                ) + home_faq_jsonld(md_text, canonical)
            elif page.schema_type == "TechArticle":
                jsonld = tech_article_jsonld(
                    meta.get("title") or page_title,
                    desc,
                    canonical,
                    locale,
                    og_image,
                    last_modified[page.dst],
                )
            else:
                jsonld = ""
            label = ui["home"] if is_home else page_title
            alternates = [
                item
                for item in page_alternates(page, pages)
                if item.translation_group == page.translation_group
            ]
            og_alternates = "\n".join(
                '<meta property="og:locale:alternate" content="{0}">'.format(
                    LOCALES[item.locale]["og_locale"]
                )
                for item in alternates
                if item.locale != locale
            )
            home_href = html.escape(link_from(dst, home_dst), quote=True)
            breadcrumb = (
                ""
                if is_home
                else (
                    '<div class="crumb"><a href="{0}">{1}</a>'
                    '<span class="sep">/</span><span class="here">{2}</span></div>'
                ).format(
                    home_href,
                    html.escape(ui["home"], quote=True),
                    html.escape(label, quote=True),
                )
            )

            page_html = (
                TEMPLATE.replace("__CSS__", CSS)
                .replace("__SITE_CSS__", "<style>{0}</style>".format(SITE_CSS))
                .replace(
                    "__JS__",
                    JS.replace("__JS_I18N__", interaction_copy_json(locale)),
                )
                .replace("__SITE_NAME__", html.escape(site_name, quote=True))
                .replace("__SITE_SHORT__", html.escape(site_short, quote=True))
                .replace("__HTML_LANG__", html.escape(locale_config["html_lang"], quote=True))
                .replace("__PAGE_KIND__", html.escape(kind, quote=True))
                .replace("__TITLE__", html.escape(title, quote=True))
                .replace("__DESC__", html.escape(desc, quote=True))
                .replace("__CANONICAL__", html.escape(canonical, quote=True))
                .replace("__HREFLANG__", hreflang_links(page, pages, base))
                .replace("__VERIFICATION__", search_verification)
                # 社交预览图：站点根下的相对地址，换域名不需要改代码
                .replace("__OG_IMAGE__", html.escape(og_image, quote=True))
                .replace("__OG_LOCALE__", html.escape(locale_config["og_locale"], quote=True))
                .replace("__OG_ALTERNATES__", og_alternates)
                .replace("__PAGE_LABEL__", html.escape(label, quote=True))
                .replace("__HOME__", home_href)
                .replace("__HOME_LABEL__", html.escape(ui["home"], quote=True))
                .replace("__BREADCRUMB__", breadcrumb)
                .replace("__MENU_LABEL__", html.escape(ui["menu"], quote=True))
                .replace("__NAV_LABEL__", html.escape(ui["nav"], quote=True))
                .replace("__CLOSE_LABEL__", html.escape(ui["close"], quote=True))
                .replace("__TOP_LABEL__", html.escape(ui["to_top"], quote=True))
                .replace("__FOOTER__", footer_html(src.as_posix(), repo_url, locale))
                .replace("__ALL_DOCS__", html.escape(ui["all_docs"], quote=True))
                .replace("__THEME_LABEL__", html.escape(ui["theme"], quote=True))
                .replace("__LANG_SWITCH__", language_switch_html(page, pages, dst, True))
                .replace("__DRAWER_LANG__", language_switch_html(page, pages, dst, False))
                .replace("__DRAWER_NAV__", drawer_nav)
                .replace("__SIDE_NAV__", side_nav)
                .replace("__PAGER__", pager)
                .replace("__PAGER_LABEL__", html.escape(ui["pager"], quote=True))
                .replace("__NOINDEX__", "")
                .replace("__JSONLD__", jsonld)
            )
            page_html = page_html.replace(
                '<meta property="og:type" content="article">',
                '<meta property="og:type" content="{0}">'.format(
                    "website" if is_home else "article"
                ),
            )
            # 正文最后拼接，避免正文内的占位符字样被替换
            page_html = page_html.replace("__CONTENT__", content)
            target = out_dir / dst
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(page_html, encoding="utf-8")
            written.append(dst)
            link_checks.append((dst, page_html))

        for dst, page_html in link_checks:
            for href in re.findall(r'href="([^"]+)"', page_html):
                if is_external(href) or href.startswith("#"):
                    continue
                target_rel = posixpath.normpath(
                    posixpath.join(posixpath.dirname(dst) or ".", href.split("#")[0])
                )
                if not (out_dir / target_rel).exists():
                    errors.append("{0}: 死链 {1}".format(dst, href))

        urls = []
        for page in pages:
            loc = canonical_url(base, page.dst)
            modified = last_modified[page.dst]
            modified_xml = (
                "<lastmod>{0}</lastmod>".format(html.escape(modified))
                if modified
                else ""
            )
            urls.append(
                "  <url><loc>{0}</loc>{1}<changefreq>weekly</changefreq>"
                "<priority>{2}</priority></url>".format(
                    html.escape(loc),
                    modified_xml,
                    "1.0" if page.dst == "index.html" else ("0.9" if page.is_home else "0.8"),
                )
            )
        (out_dir / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls)
            + "\n</urlset>\n",
            encoding="utf-8",
        )
        (out_dir / "robots.txt").write_text(robots_txt(base), encoding="utf-8")
        (out_dir / "{0}.txt".format(INDEXNOW_KEY)).write_text(
            INDEXNOW_KEY, encoding="utf-8"
        )
        (out_dir / "llms.txt").write_text(llms_txt(base, pages), encoding="utf-8")
        # Pages 默认用 Jekyll 处理，.nojekyll 让下划线开头的路径原样发布
        (out_dir / ".nojekyll").write_text("", encoding="utf-8")

        # 社交预览图：og:image 指向站根，必须同步拷进产物，否则分享卡片是空白
        og_src = ROOT / "docs" / "og-image.png"
        if og_src.exists():
            shutil.copyfile(og_src, out_dir / "og-image.png")
        else:
            errors.append("缺少 docs/og-image.png，og:image 将 404")

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
