# -*- coding: utf-8 -*-
"""model_verify.py 离线自测契约 (Offline Selftest Contract).

断言 examples/model_verify.py 的 `--selftest` 分支在零网络请求、零计费的前提下通过，
保证统计口径、置换检验与基线包装等核心逻辑在发布前始终可用。

用 runpy 以 __main__ 方式在同进程执行脚本（与命令行 `--selftest` 走同一条入口代码），
避免对"当前解释器能否再次派生自身"的环境依赖。

另含总评降级契约：当 A 段请求直接失败（如 HTTP 401）时，main() 必须返回 0 且
总评为「证据不足」，绝不能在请求失败时反推出「匹配」；非法 --tier 必须被 argparse
以非零 SystemExit 拒绝。
"""

import contextlib
import importlib.util
import io
import os
import runpy
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "examples" / "model_verify.py"


def _load_model_verify_module():
    """用 importlib 以普通模块方式加载 model_verify.py（不触发 __main__ 入口）。"""
    spec = importlib.util.spec_from_file_location("model_verify_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestModelVerifySelftest(unittest.TestCase):
    def test_selftest_passes_offline(self):
        """`--selftest` 必须正常完成并输出全部通过标记，且不依赖任何 NUOAPI_* 凭据。"""
        removed = {k: os.environ.pop(k) for k in list(os.environ) if k.startswith("NUOAPI_")}
        old_argv = sys.argv
        sys.argv = [str(SCRIPT), "--selftest"]
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                try:
                    runpy.run_path(str(SCRIPT), run_name="__main__")
                except SystemExit as exc:
                    self.assertIn(exc.code, (0, None), f"selftest 以非零状态退出: {exc.code}")
        finally:
            sys.argv = old_argv
            os.environ.update(removed)

        output = buf.getvalue()
        self.assertIn("全部通过", output)
        self.assertIn("不发送任何网络请求", output)


class TestModelVerifyVerdictDowngrade(unittest.TestCase):
    """请求失败 / 非法参数时的总评降级契约。"""

    def setUp(self):
        self.mod = _load_model_verify_module()

    def test_http_error_downgrades_verdict_to_inconclusive(self):
        """A 段 call_api 固定抛 RuntimeError("HTTP 401 boom") 时，必须降级为「证据不足」且返回 0。"""
        # 与 README 文档示例一致的命令行形态（--endpoint / --model 已原生登记，
        # 同名环境变量仅作回退；此处为夹具 Key，非真实凭据）。
        argv = [
            "model_verify.py",
            "--endpoint", "https://127.0.0.1:1/v1",
            "--claims", "openai",
            "--model", "m",
            "--tier", "A",
            "--run",
        ]
        env = {"NUOAPI_API_KEY": "sk-1234567890abcdef"}

        saved_argv = sys.argv
        saved_env = {k: os.environ.get(k) for k in env}
        sys.argv = argv
        os.environ.update(env)
        buf = io.StringIO()
        rc = None
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
                with mock.patch.object(self.mod, "call_api",
                                       side_effect=RuntimeError("HTTP 401 boom")):
                    rc = self.mod.main()
        finally:
            sys.argv = saved_argv
            for key, value in saved_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        output = buf.getvalue()
        self.assertEqual(rc, 0, f"请求失败应降级为证据不足并返回 0，实际返回 {rc}\n输出:\n{output}")
        self.assertIn("总评：证据不足", output)
        self.assertNotIn("总评：匹配", output)

    def test_invalid_tier_d_exits_nonzero(self):
        """--tier D 属非法档位，argparse 必须以非零 SystemExit 退出。"""
        saved_argv = sys.argv
        sys.argv = ["model_verify.py", "--tier", "D"]
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as ctx:
                    self.mod.main()
        finally:
            sys.argv = saved_argv
        self.assertNotIn(ctx.exception.code, (0, None),
                         f"--tier D 必须以非零状态退出，实际 code={ctx.exception.code!r}")


if __name__ == "__main__":
    unittest.main()
