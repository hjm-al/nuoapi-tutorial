# -*- coding: utf-8 -*-
"""站点构建契约测试（GitHub Pages 多页站）。

目的：
1. 用固定参数构建到临时目录，断言页面数、sitemap/robots/.nojekyll 齐备；
2. 断言站内链接与页内锚点都有对应产物（构建器自身已自检，这里做第二道闸）；
3. 断言每页都有自指 canonical 与正确语言，翻译组互链对称，报错页带 TechArticle，
   FAQ 页带 FAQPage 结构化数据（能被富结果解析）；
4. 断言已提交的 h5/index.html 与当前 README/theme.py 构建结果一致，
   防止"README 改了、移动端页面静默过期"；
5. 断言 Pages workflow 仍以 GitHub Actions 方式部署（不是 branch 部署）。
"""

import re
import os
import struct
import sys
import tempfile
import unicodedata
import unittest
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qsl, urlsplit

ROOT = Path(__file__).resolve().parents[1]
H5 = ROOT / "h5"
sys.path.insert(0, str(H5))

import build_h5  # noqa: E402
import build_site  # noqa: E402
import document_structure  # noqa: E402
BASE_URL = "https://example.github.io/nuoapi-tutorial"
REPO_URL = "https://github.com/example/nuoapi-tutorial"
EXPECTED_PAGE_COUNT = 41
PRIORITY_PAGES = {
    Path("docs/MODEL_VERIFICATION_METHODS.md"): {
        "h1": "模型真伪与防掺水：中转站换模型怎么判断",
        "phrases": ("模型真伪", "防掺水", "AI 中转站 防掺水", "中转站换模型怎么判断"),
    },
    Path("docs/Codex-一直Reconnecting-2026-10-18.md"): {
        "h1": "Codex 一直 Reconnecting：关闭 supports_websockets",
        "phrases": ("Codex 一直 Reconnecting", "supports_websockets"),
    },
    Path("docs/Claude-Code-不要加v1-2026-10-18.md"): {
        "h1": "Claude Code 报 404：ANTHROPIC_BASE_URL 不要加 /v1",
        "phrases": ("Claude Code 报 404", "ANTHROPIC_BASE_URL", "/v1"),
    },
    Path("docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.md"): {
        "h1": "Gemini CLI：platform is not gemini",
        "phrases": ("Gemini CLI", "platform is not gemini", "/v1beta"),
    },
    Path("docs/model_not_found.md"): {
        "h1": "404 model_not_found：先核对当前分组的模型 ID",
        "phrases": ("404 model_not_found", "当前分组", "模型 ID"),
    },
    Path("docs/401-invalid-api-key.md"): {
        "h1": "401 invalid_api_key：先确认客户端读到哪把 Key",
        "phrases": ("401 invalid_api_key", "Key", "变量名"),
    },
}
ERROR_SECTION_HEADINGS = ("## 30 秒判断", "## 最短修复", "## 成功判据")
MULTILINGUAL_ENTRY_PAGES = {
    Path("docs/llm-gateway-checklist.en.md"): {
        "h1": "LLM Gateway Checklist: Model Consistency, Data Residency and Failover",
        "action": "**Primary action**",
        "phrases": ("data residency", "audit", "failover", "BYOK", "cost"),
    },
    Path("docs/minimum-charge-and-pricing.ja.md"): {
        "h1": "AI API の最低チャージと料金を確認する方法",
        "action": "**主な操作**",
        "phrases": ("最低チャージ", "クレジット換算", "SLA", "状態ページ"),
    },
    Path("docs/cost-per-1m-tokens.es.md"): {
        "h1": "Cómo comparar el precio por 1M de tokens de una API de IA",
        "action": "**Acción principal**",
        "phrases": ("precio por 1M de tokens", "entrada", "salida", "caché", "recarga mínima"),
    },
    Path("docs/cost-per-1m-tokens.md"): {
        "h1": "AI API 每百万 Token 成本怎么算：输入、输出与缓存",
        "action": "**主操作**",
        "phrases": ("每百万 Token", "输入", "输出", "缓存", "最低充值"),
    },
    Path("docs/cost-per-1m-tokens.en.md"): {
        "h1": "AI API Cost per 1M Tokens: Input, Output and Cache",
        "action": "**Primary action**",
        "phrases": ("cost per 1M tokens", "input", "output", "cache", "minimum top-up"),
    },
    Path("docs/cost-per-1m-tokens.ja.md"): {
        "h1": "AI API の 1M Token あたりの実費：入力・出力・キャッシュ",
        "action": "**主な操作**",
        "phrases": ("1M Token", "入力", "出力", "キャッシュ", "最低入金"),
    },
    Path("docs/cost-per-1m-tokens.zh-Hant.md"): {
        "h1": "AI API 每百萬 Token 成本怎麼算：輸入、輸出與快取",
        "action": "**主要操作**",
        "phrases": ("每百萬 Token", "輸入", "輸出", "快取", "最低儲值"),
    },
}
COST_CALCULATOR_PAGES = {
    Path("docs/cost-per-1m-tokens.md"): "zh-CN",
    Path("docs/cost-per-1m-tokens.en.md"): "en-US",
    Path("docs/cost-per-1m-tokens.ja.md"): "ja-JP",
    Path("docs/cost-per-1m-tokens.es.md"): "es-ES",
    Path("docs/cost-per-1m-tokens.zh-Hant.md"): "zh-TW",
}
MAJOR_SEO_PAGES = {
    Path("README.md"): ("AI 中转站", "模型真伪", "防掺水", "Codex"),
    Path("README.en.md"): ("AI API gateway", "model authenticity", "Codex"),
    Path("README.ja.md"): ("AI ゲートウェイ", "モデル真偽", "Codex"),
    Path("README.es.md"): ("modelo", "evidencia", "Codex"),
    Path("README.zh-Hant.md"): ("AI 中轉站", "模型真偽", "防摻水", "Codex"),
    Path("FAQ.md"): ("AI 中转站", "platform is not gemini", "model_not_found"),
    Path("docs/MODEL_VERIFICATION_METHODS.md"): ("AI 中转站", "模型真伪", "防掺水"),
    Path("docs/Codex-一直Reconnecting-2026-10-18.md"): ("Codex", "Reconnecting", "supports_websockets"),
    Path("docs/Claude-Code-不要加v1-2026-10-18.md"): ("Claude Code", "ANTHROPIC_BASE_URL", "/v1"),
    Path("docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.md"): ("Gemini CLI", "platform is not gemini", "/v1beta"),
    Path("docs/model_not_found.md"): ("404", "model_not_found", "模型 ID"),
    Path("docs/401-invalid-api-key.md"): ("401", "invalid_api_key", "Key"),
    Path("docs/AI模型API协议科普-2026-10-12.md"): ("AI 中转站", "Responses", "Gemini"),
}


def all_page_records():
    return build_site.PAGES + build_site.discover_docs()


def run_build(out_dir: Path) -> int:
    """直接调用构建器（不起子进程）：部分 Windows 环境禁止 spawn 解释器。"""
    code = build_site.build(BASE_URL, REPO_URL, out_dir)
    if code != 0:
        raise AssertionError("站点构建失败：存在站内死链，见构建输出")
    return code


class TestSiteBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.site = Path(cls._tmp.name) / "site"
        with mock.patch.dict(
            os.environ,
            {
                "GOOGLE_SITE_VERIFICATION": "",
                "BING_SITE_VERIFICATION": "",
                "BAIDU_SITE_VERIFICATION": "",
            },
            clear=False,
        ):
            run_build(cls.site)
        cls.pages = sorted(
            path
            for path in cls.site.rglob("*.html")
            if path.name != build_site.GOOGLE_SITE_VERIFICATION_FILE
        )
        cls.records = all_page_records()
        cls.records_by_dst = {page.dst: page for page in cls.records}

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_pages_and_required_files(self):
        """五语言首页、固定页和全部 docs 应生成恰好 41 个产物。"""
        for required in (
            "sitemap.xml",
            "robots.txt",
            "llms.txt",
            ".nojekyll",
            build_site.INDEXNOW_KEY + ".txt",
            build_site.GOOGLE_SITE_VERIFICATION_FILE,
        ):
            self.assertTrue((self.site / required).exists(), "缺少 " + required)
        names = {p.relative_to(self.site).as_posix() for p in self.pages}
        self.assertEqual(names, {page.dst for page in self.records})
        self.assertEqual(len(self.pages), EXPECTED_PAGE_COUNT)
        self.assertIn("en/index.html", names)
        self.assertIn("ja/index.html", names)
        self.assertIn("es/index.html", names)
        self.assertIn("zh-Hant/index.html", names)

    def test_sitemap_matches_page_count(self):
        """sitemap 必须与页面一一对应，不能重复、遗漏或指向别处。"""
        sitemap = (self.site / "sitemap.xml").read_text(encoding="utf-8")
        locs = re.findall(r"<loc>(.*?)</loc>", sitemap)
        expected = {
            build_site.canonical_url(BASE_URL, page.dst) for page in self.records
        }
        self.assertEqual(len(locs), EXPECTED_PAGE_COUNT)
        self.assertEqual(len(locs), len(set(locs)), "sitemap 存在重复 URL")
        self.assertEqual(set(locs), expected)
        self.assertIn(BASE_URL + "/", locs)

    def test_multilingual_cost_calculator_contract(self):
        """五语言费用页各有一个同构本地计算器，字段、结果和隐私边界固定。"""
        required_fields = (
            "input_tokens",
            "output_tokens",
            "cache_read_tokens",
            "cache_write_tokens",
            "input_price",
            "output_price",
            "cache_read_price",
            "cache_write_price",
        )
        records_by_src = {page.src: page for page in self.records}
        for path, locale in COST_CALCULATOR_PAGES.items():
            record = records_by_src[path]
            text = (self.site / record.dst).read_text(encoding="utf-8")
            self.assertEqual(
                len(re.findall(r"<section\b[^>]*\bdata-cost-calculator\b", text)),
                1,
                record.dst,
            )
            self.assertEqual(text.count('<form class="cost-form" data-cost-form'), 1)
            self.assertNotIn("<form action=", text)
            self.assertIn('data-cost-locale="{0}"'.format(locale), text)
            self.assertIn('aria-live="polite"', text)

            for message in ("ready", "missing", "invalid", "overflow"):
                match = re.search(
                    r'data-msg-' + message + r'="([^"]*)"',
                    text,
                )
                self.assertIsNotNone(match, "{0}: data-msg-{1}".format(record.dst, message))
                self.assertTrue(match.group(1).strip(), record.dst)

            for name in required_fields:
                tag = re.search(
                    r'<input\b(?=[^>]*\bname="' + re.escape(name) + r'")[^>]*>',
                    text,
                )
                self.assertIsNotNone(tag, "{0}: {1}".format(record.dst, name))
                self.assertRegex(tag.group(0), r"\brequired\b", name)
                self.assertNotIn("value=", tag.group(0), name)

            for name in (
                "currency",
                "minimum_charge",
                "credit_amount",
                "monthly_requests",
            ):
                self.assertIn('name="{0}"'.format(name), text)

            for name in (
                "request-cost",
                "monthly-cost",
                "effective-per-million",
                "credit-rate",
                "topup-count",
            ):
                self.assertIn('data-cost-result="{0}"'.format(name), text)

            for guard in (
                "Number.isFinite(n)",
                "n < 0",
                "Math.floor(n) !== n",
                "Number.isFinite(requestCost)",
                "Number.isFinite(monthlyCost)",
                "costForm.elements.currency.value",
            ):
                self.assertIn(guard, text)
            for network_call in ("fetch(", "XMLHttpRequest", "sendBeacon"):
                self.assertNotIn(network_call, text)
            self.assertNotRegex(text, r"<script\b[^>]*\bsrc=")
            self.assertNotIn("utm_", text)

        self.assertEqual(len(self.pages), EXPECTED_PAGE_COUNT)
        sitemap = (self.site / "sitemap.xml").read_text(encoding="utf-8")
        self.assertEqual(sitemap.count("<loc>"), EXPECTED_PAGE_COUNT)

    def test_sitemap_lastmod_uses_source_git_date(self):
        """sitemap 的 lastmod 来自源 Markdown 最后一次提交，不用构建当天填充。"""
        sitemap = (self.site / "sitemap.xml").read_text(encoding="utf-8")
        expected = {}
        for page in self.records:
            modified = build_site.source_last_modified(page.src)
            if modified is not None:
                self.assertRegex(modified, r"^\d{4}-\d{2}-\d{2}$", page.src.as_posix())
            expected[build_site.canonical_url(BASE_URL, page.dst)] = modified
        actual = {}
        for block in re.findall(r"<url>(.*?)</url>", sitemap, re.S):
            loc = re.search(r"<loc>(.*?)</loc>", block, re.S)
            lastmod = re.search(r"<lastmod>(.*?)</lastmod>", block, re.S)
            self.assertIsNotNone(loc, block)
            actual[loc.group(1)] = lastmod.group(1) if lastmod else None
        self.assertEqual(actual, expected)

    def test_sitemap_omits_lastmod_when_git_date_is_unavailable(self):
        """没有可信 Git 日期时整批省略 lastmod，不能退回构建日期。"""
        with tempfile.TemporaryDirectory() as tmp:
            undated = Path(tmp) / "site"
            with mock.patch.object(build_site, "source_last_modified", return_value=None):
                run_build(undated)
            sitemap = (undated / "sitemap.xml").read_text(encoding="utf-8")
            self.assertNotIn("<lastmod>", sitemap)
            for record in self.records:
                if record.schema_type != "TechArticle":
                    continue
                data = parse_jsonld((undated / record.dst).read_text(encoding="utf-8"))
                articles = [item for item in data if item.get("@type") == "TechArticle"]
                self.assertEqual(len(articles), 1, record.dst)
                self.assertNotIn("dateModified", articles[0], record.dst)

    def test_robots_allows_crawlers_and_llms_lists_dry_run(self):
        """搜索与 AI 爬虫显式放行；llms.txt 只引导到不花钱的探针和三态结论。"""
        robots = (self.site / "robots.txt").read_text(encoding="utf-8")
        for name in build_site.CRAWLERS:
            self.assertIn("User-agent: {0}".format(name), robots)
        self.assertIn("Sitemap: {0}/sitemap.xml".format(BASE_URL), robots)
        llms = (self.site / "llms.txt").read_text(encoding="utf-8")
        self.assertIn("python examples/model_verify.py --selftest", llms)
        self.assertIn("evidence_capture.py --probe models", llms)
        self.assertIn("platform is not gemini", llms)
        self.assertIn("insufficient evidence", llms)
        self.assertIn("匹配 / 不匹配 / 证据不足", llms)
        self.assertIn(BASE_URL + "/", llms)
        self.assertIn("## 核心页面", llms)
        for path in COST_CALCULATOR_PAGES:
            page = next(record for record in self.records if record.src == path)
            self.assertIn(build_site.canonical_url(BASE_URL, page.dst), llms)
        self.assertNotIn("utm_", llms)
        home = (self.site / "index.html").read_text(encoding="utf-8")
        self.assertIn(
            'name="robots" content="index,follow,max-snippet:-1,'
            'max-image-preview:large,max-video-preview:-1"',
            home,
        )
        self.assertIn('"@type":"WebApplication"', home)
        self.assertIn('"featureList":', home)
        self.assertIn('"@type":"FAQPage"', home)
        self.assertIn("会不会把 API Key 传走", home)
        self.assertNotIn("98%", home)

    def test_robots_sitemap_target_exists_and_parses(self):
        """robots 指向的 sitemap 必须真实生成、可解析并包含全部公开页面。"""
        robots = (self.site / "robots.txt").read_text(encoding="utf-8")
        match = re.search(r"(?m)^Sitemap: (https?://\S+)$", robots)
        self.assertIsNotNone(match)
        sitemap_url = match.group(1)
        self.assertTrue(sitemap_url.startswith(BASE_URL + "/"))
        target = self.site / sitemap_url[len(BASE_URL) + 1:]
        self.assertTrue(target.is_file(), sitemap_url)
        root = ET.parse(target).getroot()
        self.assertTrue(root.tag.endswith("urlset"))
        locs = [item.text for item in root.iter() if item.tag.endswith("loc")]
        self.assertEqual(len(locs), EXPECTED_PAGE_COUNT)
        self.assertEqual(len(locs), len(set(locs)))

    def test_indexnow_key_file_matches_its_name(self):
        """IndexNow 子目录验证文件必须存在，且内容与文件名完全一致。"""
        key = build_site.INDEXNOW_KEY
        self.assertRegex(key, r"^[A-Za-z0-9-]{8,128}$")
        self.assertEqual(
            (self.site / (key + ".txt")).read_text(encoding="utf-8"),
            key,
        )

    def test_internal_links_resolve(self):
        """站内链接必须指向真实产物，HTML 页内锚点也必须在目标中可见。"""
        missing = []
        anchor_cache = {}
        for page in self.pages:
            rel_page = page.relative_to(self.site).as_posix()
            for href in re.findall(r'href="([^"]+)"', page.read_text(encoding="utf-8")):
                if href.startswith(("http://", "https://", "mailto:", "tel:", "data:", "#")):
                    continue
                file_part, _, anchor = href.partition("#")
                target = (page.parent / file_part).resolve()
                if not target.exists():
                    missing.append("{0} -> {1}".format(rel_page, href))
                    continue
                if anchor and target.suffix == ".html":
                    if target not in anchor_cache:
                        anchor_cache[target] = set(
                            re.findall(
                                r'\bid="([^"]+)"',
                                target.read_text(encoding="utf-8"),
                            )
                        )
                    if anchor not in anchor_cache[target]:
                        missing.append(
                            "{0} -> {1}（目标缺少 #{2}）".format(rel_page, href, anchor)
                        )
        self.assertEqual(missing, [], "站内死链：\n" + "\n".join(sorted(set(missing))))

    def test_language_and_canonical_are_self_consistent(self):
        """每页 html lang 与页面记录一致，canonical 必须是自己的公开 URL。"""
        for dst, record in self.records_by_dst.items():
            text = (self.site / dst).read_text(encoding="utf-8")
            lang = re.search(r'<html lang="([^"]+)">', text)
            canonical = re.search(r'<link rel="canonical" href="([^"]+)">', text)
            self.assertIsNotNone(lang, dst)
            self.assertIsNotNone(canonical, dst)
            self.assertEqual(
                lang.group(1),
                build_site.LOCALES[record.locale]["html_lang"],
                dst,
            )
            self.assertEqual(
                canonical.group(1),
                build_site.canonical_url(BASE_URL, dst),
                dst,
            )
            title = re.search(r"<title>(.*?)</title>", text, re.S)
            self.assertIsNotNone(title, dst)
            self.assertNotIn("__", title.group(1), dst)

    def test_localized_chrome_uses_current_language_home(self):
        """非中文页的导航、过滤、复制与面包屑不能残留中文控件。"""
        expectations = {
            "en/index.html": ("Open navigation", "Filter navigation", "Copy code"),
            "ja/index.html": (
                "ナビゲーションを開く",
                "ナビゲーションを絞り込む",
                "コードをコピー",
            ),
            "es/index.html": (
                "Abrir navegación",
                "Filtrar navegación",
                "Copiar código",
            ),
            "zh-Hant/index.html": (
                "開啟導覽",
                "篩選目錄",
                "複製程式碼",
            ),
        }
        for dst, labels in expectations.items():
            text = (self.site / dst).read_text(encoding="utf-8")
            brand_href = re.search(
                r'<a class="brand" href="([^"]+)"',
                text,
            ).group(1)
            self.assertEqual(brand_href, "index.html", dst)
            self.assertNotIn('<div class="crumb">', text, dst)
            self.assertIn('aria-label="{0}"'.format(labels[0]), text, dst)
            self.assertIn('"filterLabel":"{0}"'.format(labels[1]), text, dst)
            self.assertIn('"copyCodeLabel":"{0}"'.format(labels[2]), text, dst)
            self.assertNotIn('aria-label="打开导航"', text, dst)

        translated_doc = "en/docs/Claude-Code-不要加v1-2026-10-18.html"
        text = (self.site / translated_doc).read_text(encoding="utf-8")
        crumb_href = re.search(
            r'<div class="crumb"><a href="([^"]+)">',
            text,
        ).group(1)
        self.assertEqual(crumb_href, "../index.html", translated_doc)
        self.assertNotIn("筛选目录", text, translated_doc)
        self.assertNotIn("__JS_I18N__", text, translated_doc)

    def test_hreflang_groups_are_symmetric_and_not_fabricated(self):
        """只声明真实同组翻译；首页五语言与 x-default 完整，未翻译页不伪造互链。"""
        records_by_group = {}
        for record in self.records:
            records_by_group.setdefault(record.translation_group, []).append(record)

        actual_by_dst = {}
        for dst in self.records_by_dst:
            text = (self.site / dst).read_text(encoding="utf-8")
            pairs = re.findall(
                r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">',
                text,
            )
            actual_by_dst[dst] = dict(pairs)

        for dst, record in self.records_by_dst.items():
            actual = actual_by_dst[dst]
            expected = {}
            if record.translation_group:
                for alternate in records_by_group[record.translation_group]:
                    expected[build_site.LOCALES[alternate.locale]["html_lang"]] = (
                        build_site.canonical_url(BASE_URL, alternate.dst)
                    )
            self.assertEqual(
                {key: value for key, value in actual.items() if key != "x-default"},
                expected,
                "{0} 的 hreflang 不对称或声明了不存在的翻译".format(dst),
            )
            if record.is_home:
                self.assertEqual(actual.get("x-default"), BASE_URL + "/", dst)
            else:
                self.assertNotIn("x-default", actual, dst)

    def test_faq_structured_data_parses(self):
        text = (self.site / "faq.html").read_text(encoding="utf-8")
        data = parse_jsonld(text)
        faq_pages = [item for item in data if item.get("@type") == "FAQPage"]
        self.assertEqual(len(faq_pages), 1)
        faq_page = faq_pages[0]
        self.assertGreaterEqual(len(faq_page["mainEntity"]), 20)
        for item in faq_page["mainEntity"]:
            self.assertEqual(item["@type"], "Question")
            self.assertTrue(item["acceptedAnswer"]["text"].strip())
        articles = [item for item in data if item.get("@type") == "TechArticle"]
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["url"], build_site.canonical_url(BASE_URL, "faq.html"))
        self.assertEqual(
            articles[0]["dateModified"],
            build_site.source_last_modified(Path("FAQ.md")),
        )

    def test_error_pages_have_tech_article_jsonld(self):
        """8 个报错 slug 的所有既有语言页都必须输出与页面一致的 TechArticle。"""
        error_records = [page for page in self.records if page.schema_type == "TechArticle"]
        self.assertEqual(len(error_records), 17)
        self.assertEqual(
            {
                page.translation_group.removeprefix("doc:")
                if page.translation_group
                else page.src.stem
                for page in error_records
            },
            build_site.ERROR_SLUGS,
        )
        for record in error_records:
            text = (self.site / record.dst).read_text(encoding="utf-8")
            articles = [
                item for item in parse_jsonld(text) if item.get("@type") == "TechArticle"
            ]
            self.assertEqual(len(articles), 1, record.dst)
            article = articles[0]
            self.assertTrue(article["headline"].strip(), record.dst)
            self.assertGreaterEqual(len(article["description"]), 20, record.dst)
            self.assertEqual(
                article["url"],
                build_site.canonical_url(BASE_URL, record.dst),
                record.dst,
            )
            self.assertEqual(
                article["inLanguage"],
                build_site.LOCALES[record.locale]["html_lang"],
                record.dst,
            )
            self.assertEqual(
                article.get("dateModified"),
                build_site.source_last_modified(record.src),
                record.dst,
            )

    def test_page_kind_contract_matches_page_records(self):
        """41 个页面都通过稳定的 body 标识声明版式类型。"""
        expected = Counter({"home": 5, "faq": 1, "error": 17, "doc": 18})
        self.assertEqual(
            Counter(build_site.page_kind(page) for page in self.records),
            expected,
        )
        for record in self.records:
            text = (self.site / record.dst).read_text(encoding="utf-8")
            match = re.search(r'<body data-page-kind="([^"]+)">', text)
            self.assertIsNotNone(match, record.dst)
            self.assertEqual(match.group(1), build_site.page_kind(record), record.dst)

    def test_faq_has_thirty_numbered_manual_entries(self):
        """FAQ 以连续编号的手册条目呈现，不拆成三十张卡片。"""
        text = (self.site / "faq.html").read_text(encoding="utf-8")
        entries = re.findall(
            r'<section\b[^>]*class="[^"]*\bfaq-entry\b[^"]*"[^>]*'
            r'data-entry="(\d{2})"',
            text,
        )
        self.assertEqual(entries, ["{0:02d}".format(i) for i in range(1, 31)])
        self.assertNotIn("faq-card", text)

    def test_error_sections_have_layout_roles_in_all_locales(self):
        """报错页章节都带角色；两种四语言短页保留症状、配置和验证。"""
        allowed = {"symptom", "fix", "verify", "related", "detail"}
        error_records = [page for page in self.records if page.schema_type == "TechArticle"]
        for record in error_records:
            text = (self.site / record.dst).read_text(encoding="utf-8")
            roles = set(re.findall(r'data-role="([^"]+)"', text))
            self.assertTrue(roles, record.dst)
            self.assertLessEqual(roles, allowed, record.dst)

        for slug in (
            "Gemini-CLI-platform-is-not-gemini-2026-10-18",
            "Claude-Code-不要加v1-2026-10-18",
        ):
            records = [
                page
                for page in error_records
                if page.translation_group == "doc:" + slug
            ]
            self.assertEqual(len(records), 4, slug)
            for record in records:
                text = (self.site / record.dst).read_text(encoding="utf-8")
                roles = set(re.findall(r'data-role="([^"]+)"', text))
                self.assertTrue(
                    {"symptom", "fix", "verify"}.issubset(roles),
                    "{0} 缺少必需的章节角色：{1}".format(record.dst, sorted(roles)),
                )

    def test_unknown_error_heading_falls_back_to_detail(self):
        """未知翻译仍会渲染，不能因标题词表漏项而丢掉章节包装。"""
        self.assertEqual(document_structure.section_role("未识别章节"), "detail")
        self.assertEqual(document_structure.section_role("A new locale heading"), "detail")
        self.assertEqual(document_structure.section_role("30 秒判断"), "symptom")
        self.assertEqual(document_structure.section_role("最短修复"), "fix")
        self.assertEqual(document_structure.section_role("成功判据"), "verify")

    def test_og_image_has_expected_social_dimensions(self):
        """社交预览图保持 1200×630，避免平台裁切后丢失纸面排版。"""
        data = (ROOT / "docs" / "og-image.png").read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        width, height = struct.unpack(">II", data[16:24])
        self.assertEqual((width, height), (1200, 630))

    def test_home_jsonld_and_language_variants(self):
        """五个首页都有 WebApplication 与 TechArticle；FAQ 数据只属于中文首页。"""
        for dst in (
            "index.html",
            "en/index.html",
            "ja/index.html",
            "es/index.html",
            "zh-Hant/index.html",
        ):
            data = parse_jsonld((self.site / dst).read_text(encoding="utf-8"))
            self.assertEqual(data[0]["@type"], "WebApplication", dst)
            faq_pages = [item for item in data if item.get("@type") == "FAQPage"]
            articles = [item for item in data if item.get("@type") == "TechArticle"]
            if dst == "index.html":
                self.assertEqual(len(faq_pages), 1, dst)
            else:
                self.assertEqual(faq_pages, [], dst)
            self.assertEqual(len(articles), 1, dst)
            self.assertEqual(
                articles[0]["url"],
                build_site.canonical_url(BASE_URL, dst),
                dst,
            )

    def test_home_protocol_table_jsonld_matches_visible_table(self):
        """中文首页恰好一个 Table 标记，四行来自可见协议表且保留表头。"""
        home = (self.site / "index.html").read_text(encoding="utf-8")
        tables = [item for item in parse_jsonld(home) if item.get("@type") == "Table"]
        self.assertEqual(len(tables), 1)
        table = tables[0]
        self.assertEqual(table["mainEntity"]["numberOfItems"], 4)
        names = [item["name"] for item in table["about"]]
        self.assertEqual(
            names,
            ["Chat Completions", "Responses", "Messages", "Gemini 原生 REST"],
        )
        headers = [
            item["item"]["name"]
            for item in table["mainEntity"]["itemListElement"][0]["item"]["itemListElement"]
        ]
        self.assertEqual(headers, ["协议面孔", "实际请求路径", "客户端 Base URL", "典型客户端"])
        for dst in ("en/index.html", "ja/index.html", "es/index.html", "zh-Hant/index.html"):
            data = parse_jsonld((self.site / dst).read_text(encoding="utf-8"))
            self.assertEqual(
                [item for item in data if item.get("@type") == "Table"],
                [],
                dst,
            )

    def test_search_verification_meta_toggles_with_environment(self):
        """仓库变量为空时不输出验证标签，有值时每页输出三家搜索平台标签。"""
        for text in (
            (self.site / page.dst).read_text(encoding="utf-8")
            for page in self.records
        ):
            self.assertNotIn("google-site-verification", text)
            self.assertNotIn("msvalidate.01", text)
            self.assertNotIn("baidu-site-verification", text)

        with tempfile.TemporaryDirectory() as tmp:
            verified = Path(tmp) / "site"
            with mock.patch.dict(
                os.environ,
                {
                    "GOOGLE_SITE_VERIFICATION": "google-test-token",
                    "BING_SITE_VERIFICATION": "bing-test-token",
                    "BAIDU_SITE_VERIFICATION": "baidu-test-token",
                },
            ):
                run_build(verified)
            for page in self.records:
                text = (verified / page.dst).read_text(encoding="utf-8")
                self.assertIn(
                    '<meta name="google-site-verification" content="google-test-token">',
                    text,
                )
                self.assertIn(
                    '<meta name="msvalidate.01" content="bing-test-token">',
                    text,
                )
                self.assertIn(
                    '<meta name="baidu-site-verification" content="baidu-test-token">',
                    text,
                )

    def test_readme_first_headings_link_nuapi(self):
        """五语言首标题的第一个词必须是可点击的规范实例页链接。"""
        expected = "[NuoAPI](https://nuoapi.net/model-plaza)"
        for readme in (
            Path("README.md"),
            Path("README.en.md"),
            Path("README.ja.md"),
            Path("README.es.md"),
            Path("README.zh-Hant.md"),
        ):
            _, body = build_site.split_frontmatter(
                (ROOT / readme).read_text(encoding="utf-8")
            )
            self.assertTrue(
                build_site.first_heading(body).startswith(expected),
                "{0} 的 H1 没有从 NuoAPI 实例链接开始".format(readme),
            )

        h1_link = re.compile(
            r'<h1\b[^>]*>\s*'
            r'<a\b[^>]*\bhref="https://nuoapi\.net/model-plaza"[^>]*>'
            r"\s*NuoAPI\s*</a>",
            re.S,
        )
        for page in self.records:
            if not page.is_home:
                continue
            text = (self.site / page.dst).read_text(encoding="utf-8")
            self.assertIn('class="home-disclaimer"', text, page.dst)
            self.assertRegex(
                text,
                h1_link,
                "{0} 的构建后 H1 缺少 NuoAPI 真实链接".format(page.dst),
            )

        for page in self.records:
            text = (self.site / page.dst).read_text(encoding="utf-8")
            self.assertNotIn(
                "[NuoAPI](",
                text,
                "{0} 的导航仍显示原始 Markdown 标题".format(page.dst),
            )

    def test_readme_hero_prioritizes_plan_and_keeps_error_guides(self):
        """五语言首页先给不花钱的计划，再放状态行和六个高意图报错入口。"""
        guides = (
            (
                Path("README.md"),
                "index.html",
                "常见问题速查",
                "先看计划，不花钱",
                (
                    "docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.md",
                    "docs/Codex-一直Reconnecting-2026-10-18.md",
                    "docs/Claude-Code-不要加v1-2026-10-18.md",
                    "docs/401-invalid-api-key.md",
                    "docs/400-invalid-request-error.md",
                    "docs/model_not_found.md",
                ),
            ),
            (
                Path("README.en.md"),
                "en/index.html",
                "Common errors at a glance",
                "Start without spending",
                (
                    "docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.en.md",
                    "docs/Codex-一直Reconnecting-2026-10-18.en.md",
                    "docs/Claude-Code-不要加v1-2026-10-18.en.md",
                    "docs/401-invalid-api-key.md",
                    "docs/400-invalid-request-error.md",
                    "docs/model_not_found.md",
                ),
            ),
            (
                Path("README.ja.md"),
                "ja/index.html",
                "よくあるエラー早見表",
                "課金せずに確認する",
                (
                    "docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.ja.md",
                    "docs/Codex-一直Reconnecting-2026-10-18.ja.md",
                    "docs/Claude-Code-不要加v1-2026-10-18.ja.md",
                    "docs/401-invalid-api-key.md",
                    "docs/400-invalid-request-error.md",
                    "docs/model_not_found.md",
                ),
            ),
            (
                Path("README.es.md"),
                "es/index.html",
                "Errores frecuentes",
                "Empieza sin gastar",
                (
                    "docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.en.md",
                    "docs/Codex-一直Reconnecting-2026-10-18.en.md",
                    "docs/Claude-Code-不要加v1-2026-10-18.en.md",
                    "docs/401-invalid-api-key.md",
                    "docs/400-invalid-request-error.md",
                    "docs/model_not_found.md",
                ),
            ),
            (
                Path("README.zh-Hant.md"),
                "zh-Hant/index.html",
                "常見問題速查",
                "先看計畫，不花錢",
                (
                    "docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.zh-Hant.md",
                    "docs/Codex-一直Reconnecting-2026-10-18.zh-Hant.md",
                    "docs/Claude-Code-不要加v1-2026-10-18.zh-Hant.md",
                    "docs/401-invalid-api-key.md",
                    "docs/400-invalid-request-error.md",
                    "docs/model_not_found.md",
                ),
            ),
        )

        for readme, dst, heading, plan_heading, links in guides:
            _, body = build_site.split_frontmatter(
                (ROOT / readme).read_text(encoding="utf-8")
            )
            self.assertEqual(body.count(heading), 1, "{0} 的速查标题不唯一".format(readme))
            plan_heading_line = re.compile(
                r"(?m)^##\s+{0}\s*$".format(re.escape(plan_heading))
            )
            self.assertEqual(
                len(plan_heading_line.findall(body)),
                1,
                "{0} 的计划标题不唯一".format(readme),
            )

            section_end = body.find("\n## ", body.index(heading) + len(heading))
            self.assertNotEqual(section_end, -1, "{0} 的速查区块没有下一节".format(readme))
            section = body[body.index(heading) : section_end]
            self.assertEqual(
                re.findall(r"\]\((docs/[^)]+)\)", section),
                list(links),
                "{0} 的六个报错目标不完整或顺序变化".format(readme),
            )

            article = (
                (self.site / dst)
                .read_text(encoding="utf-8")
                .split("<article>", 1)[1]
                .split("</article>", 1)[0]
            )
            hero_start = article.index('<header class="home-hero">')
            hero_end = article.index("</header>", hero_start)
            first_section_start = article.find("<section", hero_end)
            first_section_end = article.find("</section>", first_section_start)
            self.assertNotEqual(first_section_start, -1, "{0} 缺少正文区块".format(dst))
            first_section = article[first_section_start : first_section_end + len("</section>")]
            self.assertIn(
                ">{0}</h2>".format(plan_heading),
                first_section,
                "{0} 的首个区块不是不花钱的 DRY RUN 计划".format(dst),
            )
            self.assertIn("--selftest", first_section, dst)
            self.assertIn("model_verify.py", first_section, dst)

            status_start = article.find('<div class="home-status">')
            self.assertGreater(status_start, first_section_end, dst)
            guide_start = article.find(heading, status_start)
            self.assertGreater(guide_start, status_start, dst)
            guide_section_start = article.rfind("<section", 0, guide_start)
            guide_section_end = article.find("</section>", guide_section_start)
            guide_section = article[guide_section_start:guide_section_end]
            self.assertEqual(
                len(re.findall(r'href="[^"]*docs/[^"]+\.html"', guide_section)),
                6,
                "{0} 的速查区块没有恰好六个站内报错链接".format(dst),
            )

    def test_pages_workflow_uses_actions_deploy(self):
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
        self.assertIn("actions/deploy-pages@", workflow)
        self.assertIn("actions/upload-pages-artifact@", workflow)
        self.assertIn("pages: write", workflow)
        self.assertIn("build_site.py", workflow)
        self.assertIn('"docs/**"', workflow)
        self.assertIn('"google*.html"', workflow)
        self.assertIn('verification_pages = sorted(site.glob("google*.html"))', workflow)
        self.assertIn("if path not in verification_pages", workflow)
        self.assertIn("vars.GOOGLE_SITE_VERIFICATION", workflow)
        self.assertIn("vars.BING_SITE_VERIFICATION", workflow)
        self.assertIn("vars.BAIDU_SITE_VERIFICATION", workflow)
        self.assertEqual(workflow.count("fetch-depth: 0"), 2)

        ci_workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("fetch-depth: 0", ci_workflow)

    def test_google_verification_file_is_copied_but_not_in_sitemap(self):
        """Google 根目录验证文件必须原样部署，但不属于可索引页面。"""
        source = (ROOT / build_site.GOOGLE_SITE_VERIFICATION_FILE).read_text(
            encoding="utf-8"
        )
        deployed = (self.site / build_site.GOOGLE_SITE_VERIFICATION_FILE).read_text(
            encoding="utf-8"
        )
        self.assertEqual(deployed, source)
        self.assertRegex(source, r"^google-site-verification: google[0-9a-f]+\.html\s*$")
        sitemap = (self.site / "sitemap.xml").read_text(encoding="utf-8")
        self.assertNotIn(build_site.GOOGLE_SITE_VERIFICATION_FILE, sitemap)

    def test_pages_workflow_notifies_indexnow_after_deploy(self):
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
        self.assertIn("  indexnow:\n    needs: deploy", workflow)
        self.assertIn('python h5/submit_indexnow.py --site-url "$SITE_URL"', workflow)
        self.assertIn("GITHUB_STEP_SUMMARY", workflow)
        self.assertIn("::warning::", workflow)
        self.assertIn("exit 0", workflow)


class TestOutboundLinks(unittest.TestCase):
    """外链配额：每篇对外文档都必须有正文锚文本指向实例站点，且不超上限。"""

    TARGETS = [Path("README.md"), Path("FAQ.md"), Path("examples/README.md")]

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.site = Path(cls._tmp.name) / "site"
        build_site.build(BASE_URL, REPO_URL, cls.site)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_every_page_links_to_instance_in_body(self):
        """正文（非页脚）至少 1 处到 nuoapi.net 的真锚点；纯文本域名不算外链。"""
        home_dsts = {page.dst for page in all_page_records() if page.is_home}
        for page in sorted(
            path
            for path in self.site.rglob("*.html")
            if path.name != build_site.GOOGLE_SITE_VERIFICATION_FILE
        ):
            text = page.read_text(encoding="utf-8")
            body = text.split("<article>")[1].split("</article>")[0]
            hits = [h for h in re.findall(r'href="(https?://[^"]+)"', body) if "nuoapi.net" in h]
            # 首页是 24KB / 12 节的落地页，注册引导 + 实例说明 + 选型节各算一处；
            # 其余子页卡在 2 处，避免整站变成推广页。
            dst = page.relative_to(self.site).as_posix()
            limit = 3 if dst in home_dsts else 2
            self.assertGreaterEqual(
                len(hits), 1, "{0} 正文没有指向实例站点的链接".format(dst))
            self.assertLessEqual(
                len(hits), limit, "{0} 实例链接超过 {1} 处，会变成硬广".format(dst, limit))

    def test_outbound_links_carry_no_tracking_params(self):
        """所有外链都不带追踪参数；实例链接只使用无查询串的规范页。"""
        tracking_key = re.compile(r"^(?:utm_.+|ref|aff)$", re.IGNORECASE)
        pages = [H5 / "index.html"] + sorted(
            path
            for path in self.site.rglob("*.html")
            if path.name != build_site.GOOGLE_SITE_VERIFICATION_FILE
        )
        for page in pages:
            text = page.read_text(encoding="utf-8")
            for href in re.findall(r'href="(https?://[^"]+)"', text):
                parsed = urlsplit(href)
                tracking_params = [
                    key for key, _ in parse_qsl(parsed.query, keep_blank_values=True)
                    if tracking_key.match(key)
                ]
                self.assertEqual(
                    tracking_params,
                    [],
                    "{0} 中的外链带了追踪参数：{1}".format(page.name, href),
                )
                hostname = (parsed.hostname or "").lower()
                if hostname == "nuoapi.net" or hostname.endswith(".nuoapi.net"):
                    self.assertEqual(
                        parsed.query, "", "{0} 中的实例链接带了查询参数：{1}".format(page.name, href))
                    self.assertEqual(
                        parsed.fragment, "", "{0} 中的实例链接带了片段：{1}".format(page.name, href))


class TestSearchMetadata(unittest.TestCase):
    """搜索/点击率约定：每篇对外文档都有可控的 title 与 description。"""

    TARGETS = [
        Path("README.md"),
        Path("README.en.md"),
        Path("README.ja.md"),
        Path("README.es.md"),
        Path("README.zh-Hant.md"),
        Path("FAQ.md"),
        Path("examples/README.md"),
    ]

    @staticmethod
    def width(text: str) -> int:
        """按显示宽度算：中日韩字符占 2 列，搜索结果按宽度截断。"""
        return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)

    def documents(self):
        return self.TARGETS + [
            path.relative_to(ROOT)
            for path in sorted((ROOT / "docs").glob("*.md"))
        ]

    def test_every_doc_has_frontmatter_meta(self):
        for doc in self.documents():
            meta, body = build_site.split_frontmatter(doc.read_text(encoding="utf-8"))
            self.assertIn("title", meta, "{0} 缺少 title 头".format(doc))
            self.assertIn("description", meta, "{0} 缺少 description 头".format(doc))
            # 头被拆掉后，正文首行必须还是大标题（导航与正文结构不变）
            self.assertTrue(build_site.first_heading(body), doc.as_posix())

    def test_all_documents_are_covered_once(self):
        """元数据扫描必须覆盖五语言首页、固定页和全部 docs，不漏掉翻译页。"""
        expected = {
            Path("README.md"),
            Path("README.en.md"),
            Path("README.ja.md"),
            Path("README.es.md"),
            Path("README.zh-Hant.md"),
            Path("FAQ.md"),
            Path("examples/README.md"),
        } | {path.relative_to(ROOT) for path in (ROOT / "docs").glob("*.md")}
        self.assertEqual(set(self.documents()), expected)

    def test_title_and_description_fit_search_snippet(self):
        for doc in self.documents():
            meta, _ = build_site.split_frontmatter(doc.read_text(encoding="utf-8"))
            self.assertLessEqual(
                self.width(meta["title"]), 70, "{0} 标题过长会被截断".format(doc))
            self.assertLessEqual(
                self.width(meta["description"]), 160, "{0} 描述过长会被截断".format(doc))
            self.assertGreaterEqual(
                self.width(meta["description"]), 60, "{0} 描述太短，浪费结果页空间".format(doc))

    def test_major_pages_have_intent_rich_search_descriptions(self):
        """主要入口的描述为手写版本，长度落在 120–155 个搜索显示列。"""
        for doc, phrases in MAJOR_SEO_PAGES.items():
            meta, _ = build_site.split_frontmatter(doc.read_text(encoding="utf-8"))
            description = meta["description"]
            width = self.width(description)
            self.assertGreaterEqual(width, 120, "{0}: {1}".format(doc, width))
            self.assertLessEqual(width, 155, "{0}: {1}".format(doc, width))
            folded = description.casefold()
            for phrase in phrases:
                self.assertIn(phrase.casefold(), folded, "{0}: {1}".format(doc, phrase))

    def test_home_title_is_question_or_problem_oriented(self):
        """首页搜索结果标题先说问题与解法，不改正文 H1。"""
        meta, body = build_site.split_frontmatter((ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertTrue(meta["title"].startswith("AI 中转站防掺水："))
        self.assertEqual(
            build_site.first_heading(body),
            "[NuoAPI](https://nuoapi.net/model-plaza) 接入脚手架与防掺水取证工具箱",
        )

    def test_faq_title_carries_symptom_keywords(self):
        """报错长尾是点击率最高的一类词，FAQ 标题必须带至少一个报错原文。"""
        meta, _ = build_site.split_frontmatter((ROOT / "FAQ.md").read_text(encoding="utf-8"))
        self.assertTrue(
            any(word in meta["title"] for word in ("model_not_found", "platform is not gemini", "400", "401")),
            "FAQ 标题应包含用户会直接搜索的报错原文",
        )

    def test_priority_pages_put_search_intent_in_title_h1_or_lead(self):
        """六个优先页的首屏必须出现目标意图，标题与 H1 不能各写各的。"""
        for path, expected in PRIORITY_PAGES.items():
            meta, body = build_site.split_frontmatter(
                (ROOT / path).read_text(encoding="utf-8")
            )
            self.assertEqual(build_site.first_heading(body), expected["h1"], path.as_posix())
            first_paragraph = next(
                (
                    line.strip()
                    for line in body.splitlines()
                    if line.strip() and not line.startswith(("#", ">", "-", "|", "```"))
                ),
                "",
            )
            searchable = " ".join((meta["title"], expected["h1"], first_paragraph))
            normalized = re.sub(r"\s+", "", searchable)
            for phrase in expected["phrases"]:
                self.assertIn(
                    re.sub(r"\s+", "", phrase),
                    normalized,
                    "{0} 的首屏缺少目标短语：{1}".format(path, phrase),
                )

    def test_error_pages_use_three_fixed_sections_and_one_primary_action(self):
        """五个报错页固定三段式，只设一个主操作，并保留一条相关 FAQ 排错内链。"""
        for path in list(PRIORITY_PAGES)[1:]:
            source = (ROOT / path).read_text(encoding="utf-8")
            _meta, body = build_site.split_frontmatter(source)
            for heading in ERROR_SECTION_HEADINGS:
                self.assertEqual(
                    len(re.findall(r"(?m)^" + re.escape(heading) + r"\s*$", body)),
                    1,
                    "{0} 缺少或不唯一的章节：{1}".format(path, heading),
                )
            self.assertEqual(
                body.count("**主操作**"),
                1,
                "{0} 必须且只能有一个主操作".format(path),
            )
            self.assertRegex(
                body,
                r"\]\([^)]*FAQ\.md#[^)]+\)",
                "{0} 缺少相关 FAQ 排错内链".format(path),
            )

    def test_methodology_hub_has_four_steps_and_safe_entry_action(self):
        """方法学页首屏给出四步流程、三态结论和唯一离线主操作。"""
        source = (ROOT / "docs" / "MODEL_VERIFICATION_METHODS.md").read_text(encoding="utf-8")
        _meta, body = build_site.split_frontmatter(source)
        lead = body.split("\n## ", 1)[0]
        for phrase in ("同一协议入口", "输出分布", "长上下文", "证据不足"):
            self.assertIn(phrase, lead)
        self.assertIn("**匹配 / 不匹配 / 证据不足**", lead)
        self.assertEqual(body.count("**主操作**"), 1)
        self.assertIn("python examples/model_verify.py --selftest", body)
        self.assertIn("https://nuoapi.net/model-plaza", body)
        self.assertNotIn("https://nuoapi.net)", body)

    def test_multilingual_entry_pages_have_one_action_and_context_link(self):
        """英日西入口页各自回答一个市场问题，并保留单一主操作与核验内链。"""
        for path, expected in MULTILINGUAL_ENTRY_PAGES.items():
            meta, body = build_site.split_frontmatter(
                (ROOT / path).read_text(encoding="utf-8")
            )
            self.assertEqual(build_site.first_heading(body), expected["h1"], path.as_posix())
            self.assertEqual(
                body.count(expected["action"]),
                1,
                "{0} 必须且只能有一个主操作".format(path),
            )
            searchable = re.sub(
                r"\s+",
                "",
                " ".join((meta["title"], expected["h1"], body)),
            ).casefold()
            for phrase in expected["phrases"]:
                self.assertIn(
                    re.sub(r"\s+", "", phrase).casefold(),
                    searchable,
                    "{0} 的首屏缺少目标短语：{1}".format(path, phrase),
                )
            self.assertRegex(
                body,
                r"\]\(MODEL_VERIFICATION_METHODS\.md(?:#[^)]+)?\)",
                "{0} 缺少模型核验方法学内链".format(path),
            )
            self.assertGreaterEqual(body.count("https://nuoapi.net/model-plaza"), 1, path)
            self.assertLessEqual(body.count("https://nuoapi.net/model-plaza"), 2, path)


class TestSingleFileSync(unittest.TestCase):
    def test_h5_index_is_up_to_date(self):
        """h5/index.html 必须与 README + theme.py 的当前构建结果一致。"""
        committed = (H5 / "index.html").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "index.html"
            build_h5.build(output=snapshot)
            rebuilt = snapshot.read_text(encoding="utf-8")
            # 构建时间戳每次不同，比较前剔除
            stamp = re.compile(r"构建于 \d{4}-\d{2}-\d{2} \d{2}:\d{2}")
            self.assertEqual(
                stamp.sub("构建于 <时间>", committed),
                stamp.sub("构建于 <时间>", rebuilt),
                "h5/index.html 已过期：请运行 python h5/build_h5.py 后提交产物",
            )

    def test_h5_index_is_tagged_as_home(self):
        """单文件 H5 只有首页形态，固定用它自己的页面类型选择器。"""
        text = (H5 / "index.html").read_text(encoding="utf-8")
        self.assertIn('<body data-page-kind="home">', text)

    def test_h5_drawer_links_every_doc(self):
        """中文单文件抽屉列全部中文 docs，不把翻译页重复成近似目录。"""
        text = (H5 / "index.html").read_text(encoding="utf-8")
        drawer = text.split('id="drawer"', 1)[1].split("</nav>", 1)[0]
        self.assertIn("专题文档", drawer)
        missing = []
        docs = sorted((ROOT / "docs").glob("*.md"), key=lambda item: item.name)
        chinese_docs = [
            doc
            for doc in docs
            if not any(doc.stem.endswith("." + locale) for locale in ("en", "ja", "es", "zh-Hant"))
        ]
        for doc in chinese_docs:
            href = "/docs/{0}.html".format(doc.stem)
            if href not in drawer:
                missing.append(doc.name)
        self.assertEqual(missing, [], "抽屉缺少文档链接：" + ", ".join(missing))
        self.assertLess(
            drawer.index("/docs/MODEL_VERIFICATION_METHODS.html"),
            drawer.index("/docs/model_not_found.html"),
            "单文件抽屉应按平台无关的文件名字符串排序",
        )
        for doc in sorted(set(docs) - set(chinese_docs)):
            self.assertNotIn(
                "/docs/{0}.html".format(doc.stem),
                drawer,
                "中文离线抽屉不应列翻译页：" + doc.name,
            )


def parse_jsonld(text: str) -> list:
    import json

    return [
        json.loads(match)
        for match in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>',
            text,
            re.S,
        )
    ]



if __name__ == "__main__":
    unittest.main()
