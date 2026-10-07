#!/usr/bin/env python3
"""只读额度查询：GET /v1/usage 的安全探路与多级兜底解析（零第三方依赖）。

对应文档：docs/余额与额度查询-2026-10-06.md
该端点截至 2026-10-06 为 C 级证据（未单点实测），字段以你实际响应为准。

纪律：
  1. 默认 DRY RUN，只打印请求计划；加 --run 才发起一次只读 GET（不产生 token 计费）。
  2. Key 只走 Authorization: Bearer 头，绝不拼进 URL；只从 NUOAPI_API_KEY 读取。
  3. 先校验 Content-Type 是 JSON，防止 SPA 兜底把 200 HTML 当成功。
  4. 缺字段一律输出"未知"，绝不用 0 填充（0 会被误读成余额耗尽）。
  5. 不爆破候选路径：--path 返回 404 就以控制台为准并退出。

退出码：0=取到 JSON 并完成解析；2=参数/Key 缺失；3=HTTP 错误；4=200 但不是 JSON；5=JSON 中未找到余额字段。

用法：
  python examples/check_usage.py                 # DRY RUN
  python examples/check_usage.py --run           # 实际查询
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

KEY_MASK = "sk-abc…xyz"


def mask_key_text(text: str, key: str) -> str:
    """错误体打印前先把 Key 整串替换为掩码，避免上游回显凭据到终端。"""
    s = str(text)
    return s.replace(key, KEY_MASK) if key else s


def extract_usage(resp: dict) -> dict:
    """与余额专篇第 3 节一致的多级兜底解析；缺字段记 None（上层显示为"未知"）。"""
    quota = resp.get("quota")
    # 上游可能返回 quota 为标量/None，.get 会 AttributeError —— 只有 dict 才当对象用
    if not isinstance(quota, dict):
        quota = {}
    remaining = resp.get("remaining", quota.get("remaining", resp.get("balance")))
    unit = resp.get("unit", quota.get("unit"))
    # is_active/isValid 显式 null = 上游明确"未知"，不得当 True；两个字段都缺失才按启用处理（兼容旧网关）
    if "is_active" in resp:
        raw_active = resp["is_active"]
    elif "isValid" in resp:
        raw_active = resp["isValid"]
    else:
        raw_active = True
    is_active = "未知" if raw_active is None else raw_active
    return {
        "remaining": remaining,
        "unit": unit or "USD（缺省假定，以实际为准）",
        "is_active": is_active,
        "remaining_present": remaining is not None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="只读额度查询（默认 DRY RUN）")
    ap.add_argument("--endpoint", default=os.environ.get("NUOAPI_BASE_URL", "https://nuoapi.net/v1"),
                    help="OpenAI 形态基址，默认 https://nuoapi.net/v1")
    ap.add_argument("--path", default="/usage", help="查询路径，默认 /usage（404 时不要爆破其他路径）")
    ap.add_argument("--run", action="store_true", help="真正发起只读 GET；不加则只打印计划")
    args = ap.parse_args()

    key = os.environ.get("NUOAPI_API_KEY", "")
    base = args.endpoint.rstrip("/")
    url = f"{base}{args.path}"

    print("=== DRY RUN 计划（加 --run 才执行）===" if not args.run else "=== 执行计划 ===")
    print(json.dumps({"method": "GET", "url": url, "auth": f"Authorization: Bearer {KEY_MASK}",
                      "计费": "无模型 token 消耗"}, ensure_ascii=False, indent=2))
    if not args.run:
        print("\n未发起任何请求。确认后加 --run。")
        return 0
    if not key:
        print("错误: --run 需要环境变量 NUOAPI_API_KEY。", file=sys.stderr)
        return 2

    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as resp:
            raw = resp.read()
            status = resp.status
            content_type = resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as err:
        # 先掩码 Key 再截断：部分网关会把 Authorization 原样回显进错误体
        detail = mask_key_text(err.read().decode("utf-8", errors="replace"), key)[:300]
        print(f"HTTP {err.code}: {detail}", file=sys.stderr)
        if err.code in (401, 403, 404, 429):
            print("对照文档第 5 节错误码表处理；404 表示当前版本可能未挂载此路由，改以控制台为准。", file=sys.stderr)
        return 3

    if "json" not in content_type.lower():
        print(f"状态 {status} 但 Content-Type={content_type!r}，疑似 SPA 兜底返回 HTML，不是额度数据。", file=sys.stderr)
        print("不要解析该响应；余额以控制台页面为准。", file=sys.stderr)
        return 4

    try:
        payload = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        print("响应声明为 JSON 但解析失败，按证据不足处理。", file=sys.stderr)
        return 4

    result = extract_usage(payload)
    if not result["remaining_present"]:
        print("响应是 JSON，但 remaining / quota.remaining / balance 三个位置均无字段；记为证据不足。", file=sys.stderr)
        print("原始字段键：" + ", ".join(payload.keys()) if isinstance(payload, dict) else "(非对象)", file=sys.stderr)
        return 5

    print("\n=== 归一化结果 ===")
    print(f"剩余额度: {result['remaining']}")
    print(f"计量单位: {result['unit']}")
    print(f"Key 启用: {result['is_active']}")
    print("\n提醒: 余额只证明'钱包'，不证明模型可用；cache_read 等缓存读取项照常收费。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
