"""Minimal Anthropic Messages API request through NuoAPI."""

import json
import os
import urllib.error
import urllib.request


api_key = os.environ.get("NUOAPI_API_KEY")
if not api_key:
    raise SystemExit("错误: 请先设置环境变量 NUOAPI_API_KEY 再运行本示例。")

model = os.environ.get("NUOAPI_MODEL", "MODEL_NAME_FROM_MODEL_PLAZA")
body = {
    "model": model,
    "max_tokens": 64,
    "messages": [{"role": "user", "content": "hello"}],
}
request = urllib.request.Request(
    "https://nuoapi.net/v1/messages",
    data=json.dumps(body).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
except urllib.error.HTTPError as error:
    detail = error.read().decode("utf-8", errors="replace")
    raise SystemExit(f"HTTP {error.code}: {detail}") from error
except urllib.error.URLError as error:
    raise SystemExit(f"网络错误: 无法连接网关（DNS 解析失败/TLS 握手失败/请求超时）：{error.reason}") from error

text = [
    block["text"]
    for block in payload.get("content", [])
    if block.get("type") == "text"
]
print("\n".join(text))
