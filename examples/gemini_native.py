"""Minimal Gemini generateContent request through NuoAPI."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request


api_key = os.environ.get("NUOAPI_API_KEY")
if not api_key:
    raise SystemExit("错误: 请先设置环境变量 NUOAPI_API_KEY 再运行本示例。")

model = os.environ.get("NUOAPI_MODEL", "MODEL_NAME_FROM_MODEL_PLAZA")
encoded_model = urllib.parse.quote(model, safe="")
body = {
    "contents": [{"parts": [{"text": "hello"}]}],
}
request = urllib.request.Request(
    f"https://nuoapi.net/v1beta/models/{encoded_model}:generateContent",
    data=json.dumps(body).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
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

# content 可能是 JSON null（SAFETY 拦截等），逐级兜底避免 None.get 崩溃
candidate = (payload.get("candidates") or [{}])[0]
parts = (candidate.get("content") or {}).get("parts") or []
text = [
    part["text"]
    for part in parts
    if isinstance(part, dict) and "text" in part
]
if not text:
    raise SystemExit(
        "响应中没有可输出的文本（可能被 SAFETY 安全拦截，或 finishReason 非 STOP）。"
        f"原始响应: {json.dumps(payload, ensure_ascii=False)[:300]}"
    )
print("\n".join(text))
