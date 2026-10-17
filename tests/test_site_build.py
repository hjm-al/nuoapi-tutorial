# -*- coding: utf-8 -*-
"""站点构建契约测试（GitHub Pages 多页站）。

目的：
1. 用固定参数构建到临时目录，断言页面数、sitemap/robots/.nojekyll 齐备；
2. 断言站内链接全部有对应产物（构建器自身已自检，这里做第二道闸）；
3. 断言每页都有 canonical，且 FAQ 页带 FAQPage 结构化数据（能被富结果解析）；
4. 断言已提交的 h5/index.html 与当前 README/theme.py 构建结果一致，
   防止"README 改了、移动端页面静默过期"；
5. 断言 Pages workflow 仍以 GitHub Actions 方式部署（不是 branch 部署）。
"""

import re
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
H5 = ROOT / "h5"
sys.path.insert(0, str(H5))

import build_h5  # noqa: E402
import build_site  # noqa: E402
BASE_URL = "https://example.github.io/nuoapi-tutorial"
REPO_URL = "https://github.com/example/nuoapi-tutorial"


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
        run_build(cls.site)
        cls.pages = sorted(cls.site.rglob("*.html"))

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_pages_and_required_files(self):
        """每篇对外 Markdown 都应成为一个页面，且站点元文件齐备。"""
        for required in ("sitemap.xml", "robots.txt", ".nojekyll"):
            self.assertTrue((self.site / required).exists(), "缺少 " + required)
        names = {p.relative_to(self.site).as_posix() for p in self.pages}
        for expected in ("index.html", "faq.html", "examples.html"):
            self.assertIn(expected, names)
        docs = sorted(p.stem for p in (ROOT / "docs").glob("*.md"))
        self.assertEqual(len([n for n in names if n.startswith("docs/")]), len(docs))
        self.assertEqual(len(self.pages), len(docs) + 3)

    def test_sitemap_matches_page_count(self):
        sitemap = (self.site / "sitemap.xml").read_text(encoding="utf-8")
        self.assertEqual(sitemap.count("<loc>"), len(self.pages))
        self.assertIn(BASE_URL + "/", sitemap)

    def test_internal_links_resolve(self):
        """站内链接（相对路径）必须指向真实产物，锚点只校验非空。"""
        missing = []
        for page in self.pages:
            rel_page = page.relative_to(self.site).as_posix()
            for href in re.findall(r'href="([^"]+)"', page.read_text(encoding="utf-8")):
                if href.startswith(("http://", "https://", "mailto:", "tel:", "data:", "#")):
                    continue
                target = (page.parent / href.split("#")[0]).resolve()
                if not target.exists():
                    missing.append("{0} -> {1}".format(rel_page, href))
        self.assertEqual(missing, [], "站内死链：\n" + "\n".join(sorted(set(missing))))

    def test_every_page_has_canonical(self):
        for page in self.pages:
            text = page.read_text(encoding="utf-8")
            self.assertIn('<link rel="canonical"', text, page.name)
            self.assertNotIn("__", re.search(r"<title>(.*?)</title>", text, re.S).group(1))

    def test_faq_structured_data_parses(self):
        import json

        text = (self.site / "faq.html").read_text(encoding="utf-8")
        match = re.search(
            r'<script type="application/ld\+json">(.*?)</script>', text, re.S
        )
        self.assertIsNotNone(match, "FAQ 页缺少 JSON-LD")
        data = json.loads(match.group(1))
        self.assertEqual(data["@type"], "FAQPage")
        self.assertGreaterEqual(len(data["mainEntity"]), 20)
        for item in data["mainEntity"]:
            self.assertEqual(item["@type"], "Question")
            self.assertTrue(item["acceptedAnswer"]["text"].strip())

    def test_pages_workflow_uses_actions_deploy(self):
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
        self.assertIn("actions/deploy-pages@", workflow)
        self.assertIn("actions/upload-pages-artifact@", workflow)
        self.assertIn("pages: write", workflow)
        self.assertIn("build_site.py", workflow)


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
        for page in sorted(self.site.rglob("*.html")):
            text = page.read_text(encoding="utf-8")
            body = text.split("<article>")[1].split("</article>")[0]
            hits = [h for h in re.findall(r'href="(https?://[^"]+)"', body) if "nuoapi.net" in h]
            # 首页是 24KB / 12 节的落地页，注册引导 + 实例说明 + 选型节各算一处；
            # 其余子页卡在 2 处，避免整站变成推广页。
            limit = 3 if page.name == "index.html" else 2
            self.assertGreaterEqual(
                len(hits), 1, "{0} 正文没有指向实例站点的链接".format(page.name))
            self.assertLessEqual(
                len(hits), limit, "{0} 实例链接超过 {1} 处，会变成硬广".format(page.name, limit))

    def test_outbound_links_carry_no_tracking_params(self):
        """外链不带 UTM 等追踪参数：追踪痕迹会破坏“独立技术研究”定位。"""
        for page in self.site.rglob("*.html"):
            text = page.read_text(encoding="utf-8")
            for href in re.findall(r'href="(https?://[^"]+)"', text):
                if "nuoapi.net" not in href:
                    continue
                self.assertNotRegex(
                    href, r"[?&](utm_|ref=|aff|src=)",
                    "{0} 中的外链带了追踪参数：{1}".format(page.name, href))


class TestSearchMetadata(unittest.TestCase):
    """搜索/点击率约定：每篇对外文档都有可控的 title 与 description。"""

    TARGETS = [Path("README.md"), Path("FAQ.md"), Path("examples/README.md")]

    @staticmethod
    def width(text: str) -> int:
        """按显示宽度算：中日韩字符占 2 列，搜索结果按宽度截断。"""
        return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)

    def documents(self):
        return self.TARGETS + sorted((ROOT / "docs").glob("*.md"))

    def test_every_doc_has_frontmatter_meta(self):
        for doc in self.documents():
            meta, body = build_site.split_frontmatter(doc.read_text(encoding="utf-8"))
            self.assertIn("title", meta, "{0} 缺少 title 头".format(doc))
            self.assertIn("description", meta, "{0} 缺少 description 头".format(doc))
            # 头被拆掉后，正文首行必须还是大标题（导航与正文结构不变）
            self.assertTrue(build_site.first_heading(body), doc.as_posix())

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



if __name__ == "__main__":
    unittest.main()
