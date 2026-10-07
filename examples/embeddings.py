#!/usr/bin/env python3
"""最小 Embeddings 请求（零第三方依赖，默认 DRY RUN）。

用于确认网关是否挂载 /v1/embeddings（RAG / Aider 等场景）。
返回 404 page not found = 该版本未挂载此路由，不要换 Gemini 路径去试探。

用法：
  python examples/embeddings.py --model MODEL_NAME_FROM_MODEL_PLAZA --run
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    ap = argparse.ArgumentParser(description="Embeddings 最小示例（默认 DRY RUN）")
    ap.add_argument("--endpoint", default=os.environ.get("NUOAPI_BASE_URL", "https://nuoapi.net/v1"))
    ap.add_argument("--model", default=os.environ.get("NUOAPI_MODEL", ""))
    ap.add_argument("--input", dest="text", default="hello")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()

    root = args.endpoint.rstrip("/")
    url = f"{root}/embeddings"
    body = {"model": args.model or "MODEL_NAME_FROM_MODEL_PLAZA", "input": args.text}

    print("=== DRY RUN 计划（加 --run 才执行）===" if not args.run else "=== 执行计划 ===")
    print(json.dumps({"method": "POST", "url": url, "body": body, "计费": "1 次极短 embedding"}, ensure_ascii=False, indent=2))
    if not args.run:
        return 0
    key = os.environ.get("NUOAPI_API_KEY", "")
    if not key or not args.model:
        print("错误: --run 需要环境变量 NUOAPI_API_KEY 与 --model。", file=sys.stderr)
        return 2

    request = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as err:
        print(f"HTTP {err.code}: {err.read().decode('utf-8', errors='replace')[:300]}", file=sys.stderr)
        return 3
    except urllib.error.URLError as err:
        print(f"网络错误: 无法连接网关（DNS 解析失败/TLS 握手失败/请求超时）：{err.reason}", file=sys.stderr)
        return 3

    data = payload.get("data") or []
    vector = (data[0].get("embedding") if data else None) or []
    print(f"维度: {len(vector)}")
    print(f"前 3 个分量: {vector[:3]}")
    print(f"usage: {json.dumps(payload.get('usage', {}), ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
