"""Minimal OpenAI-compatible streaming request through NuoAPI."""

import os
import sys

from openai import OpenAI


api_key = os.environ.get("NUOAPI_API_KEY")
if not api_key:
    raise SystemExit("错误: 请先设置环境变量 NUOAPI_API_KEY 再运行本示例。")

client = OpenAI(
    api_key=api_key,
    base_url="https://nuoapi.net/v1",
)

model = os.environ.get("NUOAPI_MODEL", "MODEL_NAME_FROM_MODEL_PLAZA")
stream = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "hello"}],
    stream=True,
)

for chunk in stream:
    # usage 汇总块 / 保活块的 choices 为空，直接跳过
    if not chunk.choices:
        continue
    delta = chunk.choices[0].delta
    # delta 或 content 为 None 时按空串处理，不要让 None 写进 stdout
    content = (getattr(delta, "content", None) if delta else None) or ""
    sys.stdout.write(content)
    sys.stdout.flush()

sys.stdout.write("\n")
