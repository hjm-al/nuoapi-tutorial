# -*- coding: utf-8 -*-
"""文档完整性与内部相对链接契约测试套件 (Docs Integrity & Relative Link Contract Tests).

目的：
1. 遍历仓库中所有 Markdown 文件，提取其中的相对链接（含 #锚点）；
2. 严格核验所有内部相对链接的目标文件是否存在、锚点是否能在目标文件中定位，杜绝内部 404 死链；
3. 核验四种语言的 README 必须包含法律与商标免责声明及不代售声明；
4. 抽取反引号中以仓库内路径形态出现的引用，核验目标存在（防止"纯文本路径指向未发布文件"）。
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 匹配 Markdown 中的超链接格式 [link text](target_path)
MD_LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
# 匹配行内代码 `path/like/this.ext`
INLINE_CODE_PATTERN = re.compile(r'`([^`\n]+)`')

# 视为"可能是文件"的后缀；裸文件名（不含 /）歧义太大，不做检查
PATH_LIKE_PATTERN = re.compile(
    r'^[\w.@/\-]+\.'
    r'(?:md|py|sh|ps1|json|toml|yaml|yml|example|service|env|js|cmd|java|go|rs|cs|php|mjs|txt|csv)$'
)
# 家目录 / 环境变量 / URL 形态，不属于仓库内相对路径
NON_REPO_PREFIXES = ("http://", "https://", "mailto:", "~/", "$", "%")


def github_anchor_slug(heading: str) -> str:
    """按 GitHub 渲染规则把标题文本转成锚点 slug（与 github-slugger 行为对齐）。

    - 全部转小写；
    - 删除除 \\w（含中文）、空白、连字符之外的字符；
    - 每个空白字符各自替换成一个连字符（不折叠，连续空格会产生多个连字符）。
    """
    s = heading.strip().lower()
    # Markdown 链接保留文字、丢弃地址；行内代码反引号直接去掉
    s = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', s)
    s = s.replace('`', '')
    s = re.sub(r'[^\w\s-]', '', s, flags=re.UNICODE)
    s = re.sub(r'\s', '-', s)
    return s


def collect_anchors(md_file: Path) -> set:
    """收集文件内全部可定位锚点：Markdown 标题 slug 与显式 <a id=...>。代码块内的 # 行不算标题。"""
    anchors = set()
    in_fence = False
    for line in md_file.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        explicit = re.search(r'<a\s+id="([^"]+)"', line)
        if explicit:
            anchors.add(explicit.group(1))
        m = re.match(r'^#{1,6}\s+(.+?)\s*#*\s*$', line)
        if m:
            anchors.add(github_anchor_slug(m.group(1)))
    return anchors


class TestDocsIntegrityAndLinks(unittest.TestCase):
    """测试 Markdown 相对链接、锚点与必要免责合规条款。"""

    def setUp(self):
        exclude_dirs = {".git", "__pycache__", ".pytest_cache", ".venv", "tests", "evidence", "outputs"}
        self.md_files = [
            p for p in ROOT.rglob("*.md")
            if not any(part in exclude_dirs for part in p.parts)
        ]

    def test_all_relative_links_resolve_to_existing_files(self):
        """断言所有 Markdown 中的内部相对链接目标文件真实存在。"""
        broken_links = []

        for md_file in self.md_files:
            content = md_file.read_text(encoding="utf-8")
            for match in MD_LINK_PATTERN.finditer(content):
                link_text, link_target = match.group(1), match.group(2).strip()

                # 跳过外部 URL、纯锚点以外的非文件目标、邮件
                if link_target.startswith(("http://", "https://", "mailto:")):
                    continue
                # 跳过可能的模板变量或空链接
                if not link_target or link_target.startswith("<") and link_target.endswith(">"):
                    continue

                # 剥离内部锚点部分 (例如 path/to/file.md#section)
                file_target = link_target.split("#", 1)[0]
                if not file_target:
                    continue

                # 解析相对路径
                resolved_path = (md_file.parent / file_target).resolve()

                if not resolved_path.exists():
                    broken_links.append(
                        f"文件 {md_file.relative_to(ROOT)} 中的链接 [{link_text}]({link_target}) 指向不存在的目标: {file_target}"
                    )

        self.assertEqual(
            broken_links,
            [],
            "发现内部死链 (Broken Relative Links)，请检查路径！\n" + "\n".join(broken_links)
        )

    def test_all_internal_anchors_resolve(self):
        """断言文件内与跨文件链接的 #锚点 能在目标 Markdown 的标题/显式 id 中定位。"""
        broken = []
        for md_file in self.md_files:
            anchors_by_file = {}
            content = md_file.read_text(encoding="utf-8")
            for link_text, link_target in MD_LINK_PATTERN.findall(content):
                link_target = link_target.strip()
                if "#" not in link_target or link_target.startswith(("http://", "https://", "mailto:")):
                    continue
                file_part, anchor = link_target.split("#", 1)
                if not anchor:
                    continue
                target_file = (md_file.parent / file_part).resolve() if file_part else md_file.resolve()
                if target_file.suffix.lower() != ".md" or not target_file.exists():
                    # 文件缺失由上一个用例负责；非 md 目标不校验锚点
                    continue
                if target_file not in anchors_by_file:
                    anchors_by_file[target_file] = collect_anchors(target_file)
                if anchor not in anchors_by_file[target_file]:
                    broken.append(
                        f"文件 {md_file.relative_to(ROOT)} 的链接 [{link_text}]({link_target}) "
                        f"锚点 #{anchor} 在 {target_file.relative_to(ROOT)} 中不存在"
                    )
        self.assertEqual(broken, [], "发现失效锚点（改标题后请同步更新链接）：\n" + "\n".join(broken))

    def test_inline_code_repo_paths_exist(self):
        """断言行内代码里出现的仓库内相对路径（含已知后缀且带目录分隔符）真实存在。

        家目录（~/、$VAR、%VAR%）与隐藏目录（.workbuddy/ 等）属于客户端本机路径，不在检查范围。
        """
        broken = []
        for md_file in self.md_files:
            for line_no, line in enumerate(md_file.read_text(encoding="utf-8").splitlines(), start=1):
                for token in INLINE_CODE_PATTERN.findall(line):
                    if "/" not in token:
                        continue
                    if token.startswith(NON_REPO_PREFIXES):
                        continue
                    # 隐藏目录（.workbuddy/...）但排除 ../ 与 ./ 这两种仓库内相对写法
                    if token.startswith(".") and not token.startswith(("../", "./")):
                        continue
                    if not PATH_LIKE_PATTERN.match(token):
                        continue
                    resolved = (md_file.parent / token).resolve()
                    if not resolved.exists():
                        broken.append(
                            f"文件 {md_file.relative_to(ROOT)}:{line_no} 的行内路径 `{token}` 不存在"
                        )
        self.assertEqual(
            broken,
            [],
            "发现指向不存在文件的行内路径（仓库外材料请改写为'本机留存、未随仓库发布'）：\n" + "\n".join(broken),
        )

    def test_readme_exists(self):
        """断言中文默认入口与英、日、繁三个语言入口都存在。"""
        for name in ("README.md", "README.en.md", "README.ja.md", "README.zh-Hant.md"):
            self.assertTrue((ROOT / name).exists(), f"核心入口缺失: {name}")

    def test_legal_and_trademark_disclaimer_present(self):
        """断言四语言首页都包含等量的法律、不代售、厂商关系与 Key 保护声明。"""
        disclaimer_checks = {
            ROOT / "README.md": [
                "法律与第三方商标免责声明",
                "本仓库本身不提供、不代售任何 API 服务",
                "不收集任何人的 Key",
            ],
            ROOT / "README.en.md": [
                "Legal and trademark notice",
                "does not provide or resell API access",
                "does not collect anyone's API key",
            ],
            ROOT / "README.ja.md": [
                "法的通知と商標について",
                "API サービスを提供・再販しません",
                "API キーも収集しません",
            ],
            ROOT / "README.zh-Hant.md": [
                "法律與第三方商標免責聲明",
                "不提供、不代售任何 API 服務",
                "不收集任何人的 API Key",
            ],
        }

        for path, required_texts in disclaimer_checks.items():
            self.assertTrue(path.exists(), f"核心入口缺失: {path.name}")
            content = path.read_text(encoding="utf-8")
            for req in required_texts:
                self.assertIn(
                    req,
                    content,
                    f"{path.name} 缺少必要的免责声明文本片段: '{req}'"
                )
            self.assertIn("YOUR_NUOAPI_API_KEY", content)
            for vendor in ("OpenAI", "Anthropic", "Google", "xAI", "ByteDance", "DeepSeek", "MiniMax"):
                self.assertIn(vendor, content, f"{path.name} 的厂商关系声明漏掉了 {vendor}")


if __name__ == "__main__":
    unittest.main()
