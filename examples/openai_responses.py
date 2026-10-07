"""Minimal OpenAI Responses API request through NuoAPI."""

import os

from openai import OpenAI


api_key = os.environ.get("NUOAPI_API_KEY")
if not api_key:
    raise SystemExit("Set NUOAPI_API_KEY before running this example.")

model = os.environ.get("NUOAPI_MODEL", "MODEL_NAME_FROM_MODEL_PLAZA")
client = OpenAI(
    api_key=api_key,
    base_url="https://nuoapi.net/v1",
)

response = client.responses.create(
    model=model,
    input="hello",
)

print(response.output_text)
