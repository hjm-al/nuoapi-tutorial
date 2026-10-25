# -*- coding: utf-8 -*-
"""下划线保真回归测试。

背景：``build_site.plain_text`` 曾把 ``_`` 当装饰字符整段删掉，于是
``401 invalid_api_key`` 在侧栏锚文本里变成 ``401 invalidapikey``。
``<title>``、``<h1>``、``<meta description>`` 都是对的，肉眼从首页完全看不出来，
坏的是侧栏锚文本、抽屉导航、上下页翻页和 JSON-LD——也就是搜索侧真正读的信号。

这里**直接 import 真实的** ``build_site``，不做任何兜底：
一旦 import 失败就让测试模块加载失败，而不是退回一份"内置实现"把 bug 判成通过。
"""

import html as html_lib
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
H5 = ROOT / "h5"
sys.path.insert(0, str(H5))

import build_site  # noqa: E402  故意不加 try/except：import 失败必须直接报错

BASE_URL = "https://example.github.io/nuoapi-tutorial"
REPO_URL = "https://github.com/example/nuoapi-tutorial"

# 这些标识符就是站点主打的长尾搜索词，下划线被吃掉等于把词从锚文本里抹掉。
KEY_IDENTIFIERS = (
    "invalid_api_key",
    "model_not_found",
    "invalid_request_error",
    "supports_websockets",
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_AUTH_TOKEN",
    "GOOGLE_GEMINI_BASE_URL",
    "wire_api",
)

# 源文档里带下划线的标识符（snake_case / SCREAMING_CASE）。
UNDERSCORE_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+")

# 当年那行"把下划线当装饰删掉"的实现，防止被人原样改回去。
NAIVE_STRIP = 're.sub(r"[*_`>|]", "", text)'


def mangled_form(identifier: str) -> str:
    """去掉下划线的写法——这正是 bug 产出的错误形式。"""
    return identifier.replace("_", "")


def as_word(pattern_text: str) -> re.Pattern:
    """标识符按整词匹配，避免 ``apikey`` 命中 ``APIKEY`` 之类的巧合。"""
    return re.compile(r"(?<![A-Za-z0-9])" + re.escape(pattern_text) + r"(?![A-Za-z0-9])")


class TestUnderscorePlainText(unittest.TestCase):
    """单元层：plain_text 对下划线的处理。"""

    def test_identifiers_keep_underscores(self):
        """snake_case 与 SCREAMING_CASE 必须原样保留。"""
        for identifier in KEY_IDENTIFIERS:
            with self.subTest(identifier=identifier):
                source = "报 {0} 错误".format(identifier)
                self.assertEqual(build_site.plain_text(source), source)

    def test_no_mangled_variants(self):
        """去掉下划线的写法一个都不许冒出来。"""
        for identifier in KEY_IDENTIFIERS:
            with self.subTest(identifier=identifier):
                text = build_site.plain_text("401 {0} 处理".format(identifier))
                self.assertIn(identifier, text)
                self.assertNotIn(mangled_form(identifier), text)

    def test_emphasis_markers_are_still_stripped(self):
        """强调标记照旧剥离，不能为了保下划线把星号也留下。"""
        cases = {
            "**加粗**": "加粗",
            "*斜体*": "斜体",
            "_斜体_": "斜体",
            "__加粗__": "加粗",
            "普通文本": "普通文本",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(build_site.plain_text(source), expected)

    def test_underscore_in_code_span_is_kept(self):
        """行内代码里的标识符同样不能被吃掉。"""
        self.assertEqual(
            build_site.plain_text("`invalid_api_key` 变量"),
            "invalid_api_key 变量",
        )

    def test_intraword_underscore_follows_commonmark(self):
        """贴住字母的下划线是字面量，两侧有空白才是强调标记。"""
        self.assertEqual(build_site.plain_text("a_b_c"), "a_b_c")
        self.assertEqual(build_site.plain_text("_foo_bar_"), "foo_bar")
        self.assertEqual(build_site.plain_text("snake_case 混排_结尾"), "snake_case 混排_结尾")

    def test_naive_strip_is_not_reintroduced(self):
        """防止把"删掉所有下划线"的实现原样改回来。"""
        source = Path(build_site.__file__).read_text(encoding="utf-8")
        self.assertNotIn(NAIVE_STRIP, source)


class TestRealHeadings(unittest.TestCase):
    """语料层：仓库里真实的标题必须保留下划线。"""

    def documents(self):
        paths = [ROOT / "README.md", ROOT / "FAQ.md", ROOT / "examples" / "README.md"]
        for folder in ("docs", "topics"):
            paths.extend(sorted((ROOT / folder).glob("*.md")))
        return [path for path in paths if path.is_file()]

    def test_real_headings_keep_underscores(self):
        """真实文档标题里的标识符，导航标签里必须原样出现。"""
        checked = 0
        for doc in self.documents():
            _, body = build_site.split_frontmatter(doc.read_text(encoding="utf-8"))
            heading = build_site.first_heading(body)
            if not heading:
                continue
            checked += 1
            label = build_site.plain_text(heading)
            for token in UNDERSCORE_TOKEN.findall(heading):
                with self.subTest(doc=doc.as_posix(), token=token):
                    self.assertIn(token, label)
                    self.assertNotIn(mangled_form(token), label)
        self.assertGreater(checked, 20, "语料太少，测试没覆盖到真实标题")


class TestBuiltSite(unittest.TestCase):
    """产物层：真实构建出来的页面里不许有被吃掉的标识符。"""

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
            code = build_site.build(BASE_URL, REPO_URL, cls.site)
        if code != 0:
            raise AssertionError("站点构建失败：存在站内死链")
        cls.pages = sorted(cls.site.rglob("*.html"))

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_built_site_has_no_mangled_identifiers(self):
        """任何产物页里都不允许出现去掉下划线的标识符写法。"""
        offenders = []
        for page in self.pages:
            text = page.read_text(encoding="utf-8")
            for identifier in KEY_IDENTIFIERS:
                count = len(as_word(mangled_form(identifier)).findall(text))
                if count:
                    offenders.append(
                        (page.relative_to(self.site).as_posix(), identifier, count)
                    )
        self.assertEqual(offenders, [], "产物里仍有被吃掉下划线的标识符")

    def test_side_nav_label_matches_page_h1(self):
        """侧栏里当前页的锚文本必须等于正文 H1 的可见文字。

        正文由 Python-Markdown 渲染，是基准；两边不一致就说明纯文本提取与渲染分叉了。
        """
        mismatches = []
        for page in self.pages:
            text = page.read_text(encoding="utf-8")
            h1 = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.S)
            nav = re.search(r'<ul class="side-nav">(.*?)</ul>', text, re.S)
            if not h1 or not nav:
                continue
            visible = html_lib.unescape(re.sub(r"<[^>]+>", "", h1.group(1))).strip()
            current = re.search(
                r'<a href="[^"]*" class="current"[^>]*>([^<]*)</a>', nav.group(1)
            )
            if not current:
                continue
            label = html_lib.unescape(current.group(1)).strip()
            if label != visible:
                mismatches.append(
                    (page.relative_to(self.site).as_posix(), label, visible)
                )
        self.assertEqual(mismatches, [], "侧栏锚文本与正文 H1 不一致")


if __name__ == "__main__":
    unittest.main()
