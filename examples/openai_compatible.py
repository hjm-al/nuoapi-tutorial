"""Minimal OpenAI-compatible request through NuoAPI."""

import os

from openai import OpenAI


api_key = os.environ.get("NUOAPI_API_KEY")
if not api_key:
    raise SystemExit("Set NUOAPI_API_KEY before running this example.")

client = OpenAI(
    api_key=api_key,
    base_url="https://nuoapi.net/v1",
)

model = os.environ.get("NUOAPI_MODEL", "MODEL_NAME_FROM_MODEL_PLAZA")
response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "hello"}],
)

print(response.choices[0].message.content)
