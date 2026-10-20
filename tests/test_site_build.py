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
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
H5 = ROOT / "h5"
sys.path.insert(0, str(H5))

import build_h5  # noqa: E402
import build_site  # noqa: E402
BASE_URL = "https://example.github.io/nuoapi-tutorial"
REPO_URL = "https://github.com/example/nuoapi-tutorial"
EXPECTED_PAGE_COUNT = 33


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
            {"GOOGLE_SITE_VERIFICATION": "", "BING_SITE_VERIFICATION": ""},
        ):
            run_build(cls.site)
        cls.pages = sorted(cls.site.rglob("*.html"))
        cls.records = all_page_records()
        cls.records_by_dst = {page.dst: page for page in cls.records}

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_pages_and_required_files(self):
        """四语言首页、固定页和全部 docs 应生成恰好 33 个产物。"""
        for required in ("sitemap.xml", "robots.txt", "llms.txt", ".nojekyll"):
            self.assertTrue((self.site / required).exists(), "缺少 " + required)
        names = {p.relative_to(self.site).as_posix() for p in self.pages}
        self.assertEqual(names, {page.dst for page in self.records})
        self.assertEqual(len(self.pages), EXPECTED_PAGE_COUNT)
        self.assertIn("en/index.html", names)
        self.assertIn("ja/index.html", names)
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

    def test_robots_allows_ai_crawlers_and_llms_lists_dry_run(self):
        """AI 爬虫显式放行；llms.txt 只引导到不花钱的探针和三态结论。"""
        robots = (self.site / "robots.txt").read_text(encoding="utf-8")
        for name in build_site.AI_CRAWLERS:
            self.assertIn("User-agent: {0}".format(name), robots)
        self.assertIn("Sitemap: {0}/sitemap.xml".format(BASE_URL), robots)
        llms = (self.site / "llms.txt").read_text(encoding="utf-8")
        self.assertIn("python examples/model_verify.py --selftest", llms)
        self.assertIn("evidence_capture.py --probe models", llms)
        self.assertIn("platform is not gemini", llms)
        self.assertIn("insufficient evidence", llms)
        self.assertIn("匹配 / 不匹配 / 证据不足", llms)
        self.assertIn(BASE_URL + "/", llms)
        self.assertNotIn("utm_", llms)
        home = (self.site / "index.html").read_text(encoding="utf-8")
        self.assertIn('"@type":"WebApplication"', home)
        self.assertIn('"featureList":', home)
        self.assertIn('"@type":"FAQPage"', home)
        self.assertIn("会不会把 API Key 传走", home)
        self.assertNotIn("98%", home)

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
        """只声明真实同组翻译；首页四语言与 x-default 完整，未翻译页不伪造互链。"""
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
        data = parse_jsonld(text)[0]
        self.assertEqual(data["@type"], "FAQPage")
        self.assertGreaterEqual(len(data["mainEntity"]), 20)
        for item in data["mainEntity"]:
            self.assertEqual(item["@type"], "Question")
            self.assertTrue(item["acceptedAnswer"]["text"].strip())

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

    def test_home_jsonld_and_language_variants(self):
        """四个首页都有 WebApplication；不能把中文 FAQ 结构化数据复制到译文首页。"""
        for dst in ("index.html", "en/index.html", "ja/index.html", "zh-Hant/index.html"):
            data = parse_jsonld((self.site / dst).read_text(encoding="utf-8"))
            self.assertEqual(data[0]["@type"], "WebApplication", dst)
            faq_pages = [item for item in data if item.get("@type") == "FAQPage"]
            if dst == "index.html":
                self.assertEqual(len(faq_pages), 1, dst)
            else:
                self.assertEqual(faq_pages, [], dst)

    def test_search_verification_meta_toggles_with_environment(self):
        """仓库变量为空时不输出验证标签，有值时每页输出 Google/Bing 两个标签。"""
        for text in (
            (self.site / page.dst).read_text(encoding="utf-8")
            for page in self.records
        ):
            self.assertNotIn("google-site-verification", text)
            self.assertNotIn("msvalidate.01", text)

        with tempfile.TemporaryDirectory() as tmp:
            verified = Path(tmp) / "site"
            with mock.patch.dict(
                os.environ,
                {
                    "GOOGLE_SITE_VERIFICATION": "google-test-token",
                    "BING_SITE_VERIFICATION": "bing-test-token",
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

    def test_pages_workflow_uses_actions_deploy(self):
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
        self.assertIn("actions/deploy-pages@", workflow)
        self.assertIn("actions/upload-pages-artifact@", workflow)
        self.assertIn("pages: write", workflow)
        self.assertIn("build_site.py", workflow)
        self.assertIn("vars.GOOGLE_SITE_VERIFICATION", workflow)
        self.assertIn("vars.BING_SITE_VERIFICATION", workflow)


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
        for page in sorted(self.site.rglob("*.html")):
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
        """实例链接只用规范页，不带 UTM、ref、aff 或 iframe 嵌入参数。"""
        for page in self.site.rglob("*.html"):
            text = page.read_text(encoding="utf-8")
            for href in re.findall(r'href="(https?://[^"]+)"', text):
                if "nuoapi.net" not in href:
                    continue
                self.assertNotIn("?", href, "{0} 中的外链带了查询参数：{1}".format(page.name, href))
                self.assertNotIn("#", href, "{0} 中的外链带了片段：{1}".format(page.name, href))


class TestSearchMetadata(unittest.TestCase):
    """搜索/点击率约定：每篇对外文档都有可控的 title 与 description。"""

    TARGETS = [
        Path("README.md"),
        Path("README.en.md"),
        Path("README.ja.md"),
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
        """元数据扫描必须覆盖四语言首页、固定页和全部 docs，不漏掉翻译页。"""
        expected = {
            Path("README.md"),
            Path("README.en.md"),
            Path("README.ja.md"),
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

    def test_faq_title_carries_symptom_keywords(self):
        """报错长尾是点击率最高的一类词，FAQ 标题必须带至少一个报错原文。"""
        meta, _ = build_site.split_frontmatter((ROOT / "FAQ.md").read_text(encoding="utf-8"))
        self.assertTrue(
            any(word in meta["title"] for word in ("model_not_found", "platform is not gemini", "400", "401")),
            "FAQ 标题应包含用户会直接搜索的报错原文",
        )


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
            if not any(doc.stem.endswith("." + locale) for locale in ("en", "ja", "zh-Hant"))
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
