# -*- coding: utf-8 -*-
"""安全与凭据契约测试套件 (Security & Credentials Contract Tests).

目的：
1. 自动化扫描整个 nuoapi-tutorial 仓库中所有可按 UTF-8 解码的文本文件
   （Markdown、脚本、配置、Python/Java/Go/Rust/C#/PHP/Node 样例、H5 产物等）；
2. 强制断言禁止出现未经掩码的明文真实 API Key
   （OpenAI 形态 sk-[a-zA-Z0-9]{16,}、Google 形态 AIza[0-9A-Za-z_-]{20,}）；
3. 检查敏感凭据文件（.env, auth.json, *.key 等）被 .gitignore 正确排除，示例文件统一采用 .example 命名；
4. 卡死 quick_setup.ps1 / quick_setup.sh 安全加固契约：
   交互取 Key 必须走不回显通道（Read-Host -AsSecureString / read -s），
   且屏幕输出语句中不得插值裸 Key 变量；
5. 确保所有对外文档严格遵守凭据安全规范，杜绝泄露事故。

注意：任何违规提示都不得回显疑似密钥片段，只输出位置、长度与 sha256 前 8 位，
避免测试日志本身成为泄露渠道。
"""

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 允许的安全占位符和掩码特征
SAFE_PLACEHOLDER_SUBSTRINGS = [
    "sk-你的完整Key",
    "sk-your-key",
    "sk-YOUR_FULL_KEY",
    "sk-YOUR_NUOAPI_KEY",
    "sk-abc...xyz",
    "sk-...",
    "YOUR_API_KEY",
    "YOUR_NUOAPI_KEY",
    "YOUR_KEY_HERE",
    "sk-ant-api03-...",
    "sk-proj-...",
]

# 匹配可能的未掩码真实 API Key：
# - OpenAI/Anthropic/中转站形态：sk- 后面紧跟超过 16 个高熵字母数字字符
# - Google 形态：AIza 开头（AIzaSy... 等），后接至少 20 个字符
REAL_KEY_PATTERNS = [
    re.compile(r'\bsk-[a-zA-Z0-9_-]{16,}\b'),
    re.compile(r'\bAIza[0-9A-Za-z_-]{20,}\b'),
]

# 已知二进制后缀：即使在少数环境里能侥幸解码，也绝不作为文本扫描
BINARY_SUFFIXES = {
    ".pyc", ".pyo", ".pyd",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp",
    ".zip", ".gz", ".tar", ".tgz", ".bz2", ".7z", ".rar",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".exe", ".dll", ".so", ".dylib", ".a", ".o", ".class", ".jar", ".bin",
}

# PowerShell 屏幕输出命令；写文件（here-string / Set-Content / [IO.File]）与请求头赋值不在此列
PS_OUTPUT_CMD_PATTERN = re.compile(r"\b(?:Write-Host|Write-Output|Write-Verbose)\b")
# 裸 Key 变量：$script:ApiKey / $ApiKey（$maskedKey 不会命中）
PS_BARE_KEY_PATTERN = re.compile(r"\$(?:script:)?ApiKey\b")

# Bash 静默读取：read 命令行内同时出现 -s 形态选项（-s / -rs 等）
SH_SILENT_READ_PATTERN = re.compile(r"(?:^|[\s;|&])read\b.*(?:^|\s)-\S*s")
# 仅判定去前导空白后以 echo/printf 开头的输出行
SH_OUTPUT_CMD_PATTERN = re.compile(r"^(?:echo|printf)(?:\b|$)")
# 裸 $API_KEY / ${API_KEY}（$MASKED_KEY / ${MASKED_KEY} 不会命中）
SH_BARE_KEY_PATTERN = re.compile(r"\$\{API_KEY\}|\$API_KEY\b")


def _is_placeholder(match_text):
    return any(safe_str in match_text for safe_str in SAFE_PLACEHOLDER_SUBSTRINGS)


def _secret_fingerprint(secret):
    """只输出长度与 sha256 前 8 位，绝不回显密钥本体。"""
    digest = hashlib.sha256(secret.encode("utf-8")).hexdigest()[:8]
    return f"长度 {len(secret)}，sha256:{digest}"


class TestDocsSecurityAndCredentials(unittest.TestCase):
    """测试凭据安全、掩码规范与敏感文件隔离。"""

    def setUp(self):
        self.scanned_files = []
        # 扫描除 .git、__pycache__、.pytest_cache、tests 外的所有「可按 UTF-8 解码」文件；
        # 这样 .mjs/.go/.rs/.java/.cs/.php 等新增样例后缀无需再逐个登记，
        # .pyc/.png 等二进制会在后缀黑名单与解码失败两道闸门处被排除。
        exclude_dirs = {".git", "__pycache__", ".pytest_cache", ".venv", "tests", "evidence", "outputs"}
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue
            if any(part in exclude_dirs for part in path.parts):
                continue
            if path.suffix.lower() in BINARY_SUFFIXES:
                continue
            try:
                path.read_bytes().decode("utf-8")
            except UnicodeDecodeError:
                continue
            except OSError:
                continue
            self.scanned_files.append(path)

    def test_no_unmasked_real_api_keys_exist(self):
        """断言所有被扫描文件中严禁出现未经掩码的明文真实 API Key（含 Google 形态）。"""
        violations = []
        for file_path in self.scanned_files:
            try:
                content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue

            for line_no, line in enumerate(content.splitlines(), start=1):
                for pattern in REAL_KEY_PATTERNS:
                    for match in pattern.findall(line):
                        if _is_placeholder(match):
                            continue
                        violations.append(
                            f"{file_path.relative_to(ROOT)}:{line_no} 存在未掩码疑似凭据"
                            f"（{_secret_fingerprint(match)}；出于安全不回显片段）"
                        )

        self.assertEqual(violations, [], "发现未掩码的疑似真实 API Key，必须使用占位符或掩码！\n" + "\n".join(violations))

    def test_gitignore_covers_sensitive_credential_files(self):
        """断言 .gitignore 必须排除真实密钥文件，且仅允许 *.example 模板。"""
        gitignore_path = ROOT / ".gitignore"
        self.assertTrue(gitignore_path.exists(), ".gitignore 文件丢失！")
        text = gitignore_path.read_text(encoding="utf-8")

        required_patterns = [
            ".env",
            "auth.json",
            "*.key",
        ]
        for pattern in required_patterns:
            self.assertIn(pattern, text, f".gitignore 必须包含排除规则: {pattern}")

    def test_no_raw_credential_files_accidentally_tracked(self):
        """断言工作区中不能存在未经模板化的敏感凭据文件实体。"""
        forbidden_raw_files = [
            ROOT / ".env",
            ROOT / "examples" / "codex" / "auth.json",
            ROOT / "examples" / "hermes.env",
            ROOT / "examples" / "hermes.yaml",
            ROOT / "examples" / "claude-code.env",
            ROOT / "examples" / "openclaw.json",
        ]
        for file_path in forbidden_raw_files:
            self.assertFalse(
                file_path.exists(),
                f"发现未模板化的真实凭据实体文件 {file_path.relative_to(ROOT)}！请仅保留对应 .example 模板。"
            )

    def test_bash_and_powershell_scripts_use_safe_input_or_masking(self):
        """交互取 Key 必须走不回显通道，且屏幕输出语句中不得插值裸 Key 变量。"""
        quick_setup_ps1 = ROOT / "examples" / "quick_setup.ps1"
        quick_setup_sh = ROOT / "examples" / "quick_setup.sh"

        # ── PowerShell ──────────────────────────────────────────────────────
        if quick_setup_ps1.exists():
            ps1_text = quick_setup_ps1.read_text(encoding="utf-8")
            ps1_lines = ps1_text.splitlines()

            # 必须存在一行同时含 Read-Host 与 -AsSecureString（不回显取 Key，经 Marshal BSTR 转明文）
            secure_input_lines = [
                f"{line_no}: {line.strip()}"
                for line_no, line in enumerate(ps1_lines, start=1)
                if "Read-Host" in line and "-AsSecureString" in line
            ]
            self.assertTrue(
                secure_input_lines,
                "quick_setup.ps1 必须使用 `Read-Host ... -AsSecureString` 交互式获取 Key（不回显）！"
            )

            # 历史契约：脚本中不得写死示例真实 Key
            self.assertNotIn("sk-1234567890", ps1_text)

            # 逐行扫描所有屏幕输出行：出现裸 $script:ApiKey / $ApiKey 即失败
            # （$maskedKey、写文件 here-string、请求头赋值不算——只盯输出关键字行）
            ps1_violations = []
            for line_no, raw in enumerate(ps1_lines, start=1):
                stripped = raw.strip()
                if not stripped or stripped.startswith("#") or stripped.startswith("<#"):
                    continue
                if PS_OUTPUT_CMD_PATTERN.search(raw) and PS_BARE_KEY_PATTERN.search(raw):
                    ps1_violations.append(
                        f"quick_setup.ps1:{line_no} 屏幕输出语句插值了裸 Key 变量：{stripped}"
                    )
            self.assertEqual(
                ps1_violations,
                [],
                "Write-Host/Write-Output/Write-Verbose 输出不得直接插值 $script:ApiKey/$ApiKey，"
                "请改用 $maskedKey！\n" + "\n".join(ps1_violations)
            )

        # ── Bash ────────────────────────────────────────────────────────────
        if quick_setup_sh.exists():
            sh_text = quick_setup_sh.read_text(encoding="utf-8")
            sh_lines = sh_text.splitlines()

            # 必须存在含 read 且含 -s 的静默读取行（注释不算）
            silent_read_lines = [
                f"{line_no}: {line.strip()}"
                for line_no, line in enumerate(sh_lines, start=1)
                if not line.lstrip().startswith("#") and SH_SILENT_READ_PATTERN.search(line)
            ]
            self.assertTrue(
                silent_read_lines,
                "quick_setup.sh 必须使用含 -s 的 read（如 read -rs API_KEY）静默交互式获取 Key！"
            )

            # 逐行扫描去前导空白后以 echo/printf 开头的行：出现裸 $API_KEY 即失败
            # （$MASKED_KEY/${MASKED_KEY}、heredoc 写文件内容、export、curl 请求头、$RESPONSE 不算）
            sh_violations = []
            for line_no, raw in enumerate(sh_lines, start=1):
                stripped = raw.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if SH_OUTPUT_CMD_PATTERN.match(stripped) and SH_BARE_KEY_PATTERN.search(stripped):
                    sh_violations.append(
                        f"quick_setup.sh:{line_no} echo/printf 输出语句出现裸 $API_KEY：{stripped}"
                    )
            self.assertEqual(
                sh_violations,
                [],
                "echo/printf 输出不得出现裸 $API_KEY，请改用 $MASKED_KEY！\n" + "\n".join(sh_violations)
            )

    def test_all_example_python_files_compile(self):
        """examples 下所有 .py 必须语法可编译（内存 compile，不写 __pycache__）。"""
        examples_dir = ROOT / "examples"
        py_files = sorted(examples_dir.rglob("*.py"))
        self.assertTrue(py_files, "examples 目录下应当存在 Python 样例文件")

        failures = []
        for py_file in py_files:
            source = py_file.read_text(encoding="utf-8")
            try:
                compile(source, str(py_file), "exec")
            except SyntaxError as exc:
                failures.append(
                    f"{py_file.relative_to(ROOT)}:{exc.lineno} 语法错误: {exc.msg}"
                )
        self.assertEqual(
            failures,
            [],
            "examples 下存在无法通过编译的 Python 文件：\n" + "\n".join(failures)
        )

    def test_legacy_authenticity_script_has_run_billing_gate(self):
        """旧脚本 model_authenticity_check.py 必须保留 --run 计费确认闸门。"""
        legacy = ROOT / "examples" / "model_authenticity_check.py"
        self.assertTrue(legacy.exists(), "model_authenticity_check.py 丢失")
        source = legacy.read_text(encoding="utf-8")
        self.assertIn('"--run"', source, "model_authenticity_check.py 必须显式提供 --run 计费确认闸门")
        self.assertIn("args.run", source, "--run 闸门必须实际参与控制是否发起计费请求")


if __name__ == "__main__":
    unittest.main()
