#!/usr/bin/env python3
"""A 级证据采集器：把一次最小请求固化成可复核的证据包（零第三方依赖）。

配套方法学：docs/MODEL_VERIFICATION_METHODS.md（A 档：协议与字段残留）与
docs/TEST_REPORT_SPEC.md 模块一（元数据：原始报文 / 响应体哈希 / 毫秒时间戳）。

证据包内容（写入 --out 指定目录，默认 evidence/，已在 .gitignore 排除）：
  <时间戳>-<claims>.json   元数据：取证窗口(UTC 毫秒)、端点、模型、状态码、
                           全量响应头（同名头逐个保留，等价 get_all()）、
                           请求体、响应 JSON（若为 JSON）、响应体 SHA-256；
  <时间戳>-<claims>.body   原始响应体字节（按 UTF-8 替换解码保存，不做二次加工）。

纪律：
  1. 默认 DRY RUN，只打印计划，不发任何请求；加 --run 才执行。
  2. --probe chat 会产生 1 次极短计费请求（max_tokens=1）；
     --probe models 打 GET /v1/models，零计费，用于路由/响应头取证。
  3. Key 只从环境变量 NUOAPI_API_KEY 读取，绝不写进证据文件；
     证据 JSON 中如意外出现 Key 字串会被掩码为 sk-abc…xyz 形态。
  4. 截图不作为证据；以本脚本落盘的原始响应体 + 哈希为准。

用法：
  python examples/evidence_capture.py --probe models --run          # 零成本
  python examples/evidence_capture.py --claims openai --run
  python examples/evidence_capture.py --claims anthropic --run
  python examples/evidence_capture.py --claims gemini --run
"""

import argparse
import datetime as _dt
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_ENDPOINT = "https://nuoapi.net"
SENSITIVE_HEADER_NAMES = ("authorization", "x-api-key", "x-goog-api-key", "cookie", "set-cookie")
MASK = "sk-abc…xyz"


def root_of(endpoint: str) -> str:
    """把任意填法归一为站点根地址（去掉尾部斜杠与 /v1、/v1beta）。"""
    root = endpoint.rstrip("/")
    for suffix in ("/v1beta", "/v1"):
        if root.endswith(suffix):
            root = root[: -len(suffix)]
            break
    return root


def mask_value(value: str, secret: str | None) -> str:
    if secret and secret in value:
        value = value.replace(secret, MASK)
    return value


def build_request(probe: str, claims: str, root: str, model: str, key: str):
    """返回 (method, url, headers, body_dict|None)。"""
    headers = {"Accept": "application/json"}
    if probe == "models":
        return "GET", f"{root}/v1/models", {**headers, "Authorization": f"Bearer {key}"}, None

    if claims == "openai":
        return (
            "POST",
            f"{root}/v1/chat/completions",
            {"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
            {"model": model, "max_tokens": 1, "messages": [{"role": "user", "content": "ping"}]},
        )
    if claims == "anthropic":
        return (
            "POST",
            f"{root}/v1/messages",
            {
                "Content-Type": "application/json",
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
            {"model": model, "max_tokens": 1, "messages": [{"role": "user", "content": "ping"}]},
        )
    if claims == "gemini":
        encoded = urllib.parse.quote(model, safe="")
        return (
            "POST",
            f"{root}/v1beta/models/{encoded}:generateContent",
            {"Content-Type": "application/json", "x-goog-api-key": key},
            {"contents": [{"parts": [{"text": "ping"}]}]},
        )
    raise ValueError(f"未知 claims: {claims}")


def masked_headers(headers: dict, secret: str) -> dict:
    out = {}
    for name, value in headers.items():
        out[name] = MASK if name.lower() in SENSITIVE_HEADER_NAMES else mask_value(str(value), secret)
    return out


def response_headers_multimap(http_message) -> dict:
    """同名响应头逐个保留（多跳 X-Request-Id 痕迹不能被字典化吞掉）。"""
    result = {}
    for name in http_message.keys():
        result[name] = http_message.get_all(name)
    return result


def masked_response_headers(headers_multimap: dict, secret: str) -> dict:
    """响应头落盘前按 SENSITIVE_HEADER_NAMES 掩码。

    多值头逐值替换为 MASK 占位并保留值个数（形状不变，Set-Cookie 数量仍可复核）；
    X-Request-Id 等非敏感头保留原值，仅对意外出现的 Key 整串做掩码。
    """
    out = {}
    for name, values in headers_multimap.items():
        values = values if isinstance(values, list) else [values]
        if name.lower() in SENSITIVE_HEADER_NAMES:
            out[name] = [MASK for _ in values]
        else:
            out[name] = [mask_value(str(v), secret) for v in values]
    return out


def unique_evidence_paths(out_dir: str, base_name: str) -> tuple[str, str]:
    """同毫秒撞名时追加 -1、-2 后缀，避免证据互相覆盖。"""
    meta_path = os.path.join(out_dir, base_name + ".json")
    body_path = os.path.join(out_dir, base_name + ".body")
    if not os.path.exists(meta_path) and not os.path.exists(body_path):
        return meta_path, body_path
    i = 1
    while True:
        stem = f"{base_name}-{i}"
        meta_path = os.path.join(out_dir, stem + ".json")
        body_path = os.path.join(out_dir, stem + ".body")
        if not os.path.exists(meta_path) and not os.path.exists(body_path):
            return meta_path, body_path
        i += 1


def main() -> int:
    ap = argparse.ArgumentParser(description="A 级证据采集器（默认 DRY RUN）")
    ap.add_argument("--endpoint", default=os.environ.get("NUOAPI_BASE_URL", DEFAULT_ENDPOINT),
                    help="站点地址，根地址或带 /v1 均可")
    ap.add_argument("--probe", choices=("chat", "models"), default="chat",
                    help="chat=1 次极短计费请求；models=GET /v1/models 零计费")
    ap.add_argument("--claims", choices=("openai", "anthropic", "gemini"), default="openai")
    ap.add_argument("--model", default=os.environ.get("NUOAPI_MODEL", ""),
                    help="当前 Key 分组可见的精确模型名（probe=chat 时必填）")
    ap.add_argument("--out", default="evidence", help="证据包输出目录")
    ap.add_argument("--run", action="store_true", help="真正发起请求；不加则只打印计划")
    args = ap.parse_args()

    key = os.environ.get("NUOAPI_API_KEY", "")
    root = root_of(args.endpoint)

    if args.run and args.probe == "chat" and not args.model:
        print("错误: --probe chat 的 --run 需要 --model（或环境变量 NUOAPI_MODEL），模型名以模型广场为准。", file=sys.stderr)
        return 2

    # DRY RUN 阶段允许占位模型名，方便先核对端点与报文形状
    plan_model = args.model or "MODEL_NAME_FROM_MODEL_PLAZA"
    plan_key = key or "<未提供 Key>"
    method, url, headers, body = build_request(args.probe, args.claims, root, plan_model, plan_key)

    plan = {
        "probe": args.probe,
        "claims": args.claims,
        "method": method,
        "url": url,
        "model": args.model or "(不适用)",
        "计费请求数": 0 if args.probe == "models" else 1,
        "输出目录": os.path.abspath(args.out),
    }
    print("=== DRY RUN 计划（加 --run 才执行）===" if not args.run else "=== 执行计划 ===")
    print(json.dumps(plan, ensure_ascii=False, indent=2))

    if not args.run:
        print("\n未发起任何请求。确认计划后加 --run；chat 探针为 1 次 max_tokens=1 的计费请求。")
        return 0
    if not key:
        print("错误: --run 需要环境变量 NUOAPI_API_KEY。", file=sys.stderr)
        return 2
    method, url, headers, body = build_request(args.probe, args.claims, root, args.model, key)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    started_ms = time.time()
    started_iso = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    try:
        with urllib.request.urlopen(request, timeout=60) as resp:
            raw = resp.read()
            status, reason = resp.status, resp.reason
            resp_headers = masked_response_headers(response_headers_multimap(resp.headers), key)
            content_type = resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as err:
        # 4xx/5xx 同样是证据（拒绝阶梯、SPA 兜底都要靠它）
        raw = err.read()
        status, reason = err.code, err.reason
        resp_headers = masked_response_headers(response_headers_multimap(err.headers), key)
        content_type = err.headers.get("Content-Type", "")
    except urllib.error.URLError as err:
        # DNS/TLS/超时/连接被拒：没有上游响应就没有证据，给掩码后的友好错误，不抛 traceback
        why = getattr(err, "reason", err)
        detail = mask_value(str(why), key)[:300]
        print(f"错误: 网络请求未完成（{type(why).__name__}：{detail}）。"
              "通常是 DNS/TLS/超时/连接被拒，而非上游业务响应；本次没有可固化的证据，"
              "请检查网络与 NUOAPI_BASE_URL 后重试。", file=sys.stderr)
        return 3
    latency_ms = round((time.time() - started_ms) * 1000, 1)
    sha = hashlib.sha256(raw).hexdigest()

    text = raw.decode("utf-8", errors="replace")
    response_json = None
    if "json" in content_type.lower():
        try:
            response_json = json.loads(text)
        except json.JSONDecodeError:
            response_json = None

    stamp = started_iso.replace(":", "").replace("-", "").replace(".", "").replace("Z", "Z")
    os.makedirs(args.out, exist_ok=True)
    base_name = f"{stamp}-{args.claims}-{args.probe}"
    meta_path, body_path = unique_evidence_paths(args.out, base_name)
    with open(body_path, "wb") as fh:
        fh.write(raw)

    meta = {
        "captured_at_utc": started_iso,
        "captured_epoch_ms": int(started_ms * 1000),
        "latency_ms": latency_ms,
        "probe": args.probe,
        "claims": args.claims,
        "request": {
            "method": method,
            "url": url,
            "headers": masked_headers(headers, key),
            "body": body,
        },
        "response": {
            "status": status,
            "reason": reason,
            "content_type": content_type,
            "headers": resp_headers,
            "body_length_bytes": len(raw),
            "body_sha256": f"sha256:{sha}",
            "json": response_json,
            "body_preview": mask_value(text[:500], key),
        },
        "evidence_note": "原始响应体见同名 .body 文件；截图不构成证据。判定只用 匹配/不匹配/证据不足。",
    }
    safe_meta = mask_value(json.dumps(meta, ensure_ascii=False, indent=2), key)
    with open(meta_path, "w", encoding="utf-8") as fh:
        fh.write(safe_meta)

    print(f"\n[采集完成] HTTP {status} {reason} · {latency_ms} ms · {len(raw)} bytes")
    print(f"元数据:   {os.path.abspath(meta_path)}")
    print(f"原始响应: {os.path.abspath(body_path)}")
    print(f"SHA-256:  sha256:{sha}")
    print("提醒: 证据目录默认不进 Git；对外分享前再次核对是否含敏感输入。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
