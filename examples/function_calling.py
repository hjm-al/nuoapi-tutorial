"""Minimal Function Calling (Tool Use) example through NuoAPI.

Demonstrates how to invoke local tools with gpt-6-astra via NuoAPI.
Zero-dependency: uses Python standard library urllib.
"""

import json
import os
import sys
import urllib.error
import urllib.request


API_KEY = os.environ.get("NUOAPI_API_KEY")
BASE_URL = os.environ.get("NUOAPI_BASE_URL", "https://nuoapi.net/v1")
MODEL = os.environ.get("NUOAPI_MODEL", "gpt-6-astra")

if not API_KEY:
    raise SystemExit("错误: 请先设置环境变量 NUOAPI_API_KEY 再运行本示例。")


# 1. 模拟本地自定义工具函数
def get_current_weather(location: str, unit: str = "celsius"):
    """Mock local weather tool."""
    mock_db = {
        "beijing": {"temp": 22, "condition": "晴朗", "humidity": "45%"},
        "tokyo": {"temp": 19, "condition": "多云", "humidity": "60%"},
        "shanghai": {"temp": 25, "condition": "小雨", "humidity": "80%"},
    }
    loc_key = location.lower()
    info = mock_db.get(loc_key, {"temp": 20, "condition": "阴天", "humidity": "50%"})
    return json.dumps({"location": location, **info}, ensure_ascii=False)


# 2. 工具定义 (OpenAI Tools Schema)
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "获取指定城市的实时天气数据",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称，如 Beijing, Tokyo",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位",
                    },
                },
                "required": ["location"],
            },
        },
    }
]


def post_chat(messages, tools=None):
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.0,
    }
    if tools:
        payload["tools"] = tools

    req = urllib.request.Request(
        f"{BASE_URL.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        raise SystemExit(
            f"请求失败 HTTP {err.code}: {err.read().decode('utf-8', errors='replace')[:300]}"
        ) from err
    except urllib.error.URLError as err:
        raise SystemExit(
            f"网络错误: 无法连接网关（DNS 解析失败/TLS 握手失败/请求超时）：{err.reason}"
        ) from err


def main():
    print(f"[*] 正在向 NuoAPI 发送带 Tools 的提问 (模型: {MODEL})...")
    messages = [
        {"role": "user", "content": "请帮我查一下北京和东京现在的天气分别是多少度？"}
    ]

    # 第一轮：模型决定调用工具
    res1 = post_chat(messages, tools=tools_schema)
    choices1 = res1.get("choices") or []
    if not choices1:
        raise SystemExit(f"错误: 第一轮响应 choices 为空：{json.dumps(res1, ensure_ascii=False)[:300]}")
    message = choices1[0].get("message")
    if not message:
        raise SystemExit(f"错误: 第一轮响应缺少 message 字段：{json.dumps(res1, ensure_ascii=False)[:300]}")
    tool_calls = message.get("tool_calls", [])

    if not tool_calls:
        print("[!] 模型未触发函数调用，直接回复了：")
        print(message.get("content"))
        return

    print(f"[+] 模型决定调用 {len(tool_calls)} 个工具：")
    messages.append(message)  # 将模型的 tool_calls 响应加入上下文

    # 执行本地函数并将结果加入上下文
    for tc in tool_calls:
        fn_name = (tc.get("function") or {}).get("name") or ""
        call_id = tc.get("id") or ""
        # arguments 为空/None 或非法 JSON 时按 {} 处理，不能让第二轮带着崩溃继续
        raw_args = (tc.get("function") or {}).get("arguments")
        try:
            fn_args = json.loads(raw_args) if raw_args else {}
        except json.JSONDecodeError:
            print(f"  [!] 函数 {fn_name} 的 arguments 不是合法 JSON，按空参数处理：{raw_args!r}")
            fn_args = {}
        if not isinstance(fn_args, dict):
            fn_args = {}
        print(f"  -> 执行本地函数: {fn_name}({fn_args})")

        if fn_name == "get_current_weather":
            # 只透传函数签名里声明过的参数，模型多给的参数直接丢弃
            known_args = {k: v for k, v in fn_args.items() if k in ("location", "unit")}
            if "location" not in known_args:
                result = json.dumps({"error": "缺少必填参数 location"}, ensure_ascii=False)
            else:
                result = get_current_weather(**known_args)
        else:
            # 未知函数也要回一条 role:"tool" 的结果，否则第二轮请求会 400
            result = json.dumps({"error": f"未知函数: {fn_name}"}, ensure_ascii=False)
        messages.append({
            "role": "tool",
            "tool_call_id": call_id,
            "content": result,
        })

    # 第二轮：将工具执行结果回传给模型进行自然语言归纳
    print("[*] 回传工具执行结果，等待模型最终总结...")
    res2 = post_chat(messages)
    choices2 = res2.get("choices") or []
    final_reply = (choices2[0].get("message") or {}).get("content") if choices2 else None
    if not final_reply:
        raise SystemExit(f"错误: 第二轮响应缺少回复内容：{json.dumps(res2, ensure_ascii=False)[:300]}")
    print("\n[最终模型回答]:")
    print(final_reply)


if __name__ == "__main__":
    main()
