#!/usr/bin/env sh
set -eu

if [ -z "${NUOAPI_API_KEY:-}" ]; then
    echo "错误: 请先设置环境变量 NUOAPI_API_KEY (sk-...)" >&2
    exit 1
fi

if [ -z "${NUOAPI_MODEL:-}" ]; then
    echo "错误: 请先设置环境变量 NUOAPI_MODEL，值为模型广场中当前 Key 分组可见的精确模型 ID" >&2
    exit 1
fi

# -sS: 静默但保留错误信息；--fail-with-body: HTTP 4xx/5xx 时返回非零且保留响应体。
# 注意: --fail-with-body 需要 curl 7.76.0+，老版本 curl 可降级为 -f -S
curl -sS --fail-with-body "https://nuoapi.net/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${NUOAPI_API_KEY}" \
  -d "{\"model\":\"${NUOAPI_MODEL}\",\"messages\":[{\"role\":\"user\",\"content\":\"hello\"}]}"
