#!/usr/bin/env python3
"""最小图片生成请求（零第三方依赖，默认 DRY RUN）。

对应文档：docs/图片生成实测教程-2026-09-28.md
两种返回形态都要能处理：b64_json 内联，或 url 指向第三方托管（拿到 URL 的人可能可读，勿传敏感素材）。

用法：
  python examples/images_generations.py --model MODEL_NAME_FROM_MODEL_PLAZA --run
  python examples/images_generations.py --model ... --prompt "一只白猫" --size 1024x1024 --run
"""

import argparse
import base64
import binascii
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


def detect_format(data: bytes) -> str:
    """按文件头识别实际格式——不能只信 URL 扩展名或请求参数。"""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return "bin"


def png_dimensions(data: bytes):
    """PNG 的宽高在 IHDR（文件头第 16–24 字节）；其他格式不强行解析。"""
    if detect_format(data) == "png" and len(data) >= 24:
        width = int.from_bytes(data[16:20], "big")
        height = int.from_bytes(data[20:24], "big")
        return width, height
    return None, None


# 标准 Base64 字符集（A-Z a-z 0-9 + /），末尾允许 0-2 个 '=' 补齐
_B64_RE = re.compile(r"^[A-Za-z0-9+/]*={0,2}$")


def decode_b64_image(raw: str) -> bytes:
    """解码前先剥 data: 前缀、校字符集、补 padding；脏数据抛 ValueError（中文消息）。"""
    b64 = raw.split(",", 1)[-1] if raw.strip().lower().startswith("data:") else raw
    b64 = "".join(b64.split())  # 去掉换行/空白
    if not b64 or not _B64_RE.match(b64):
        raise ValueError("返回的 b64_json 含非 Base64 字符，疑似脏数据，已中止解码。")
    pad = (-len(b64)) % 4  # 缺几个 '=' 就补几个
    b64 += "=" * pad
    try:
        return base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError) as err:
        raise ValueError(f"Base64 解码失败（长度或 padding 非法）：{err}") from err


def main() -> int:
    ap = argparse.ArgumentParser(description="图片生成最小示例（默认 DRY RUN）")
    ap.add_argument("--endpoint", default=os.environ.get("NUOAPI_BASE_URL", "https://nuoapi.net/v1"))
    ap.add_argument("--model", default=os.environ.get("NUOAPI_MODEL", ""))
    ap.add_argument("--prompt", default="一只白猫，干净背景，写实风格，无文字无水印")
    ap.add_argument("--size", default="1024x1024")
    ap.add_argument("--quality", default="low")
    ap.add_argument("--outdir", default="outputs", help="图片保存目录（已在 .gitignore 排除）")
    ap.add_argument("--run", action="store_true", help="真正发起计费请求")
    args = ap.parse_args()

    root = args.endpoint.rstrip("/")
    if root.endswith("/v1beta"):
        root = root[: -len("/v1beta")]
    if not root.endswith("/v1"):
        root += "/v1"
    url = f"{root}/images/generations"
    body = {"model": args.model or "MODEL_NAME_FROM_MODEL_PLAZA", "prompt": args.prompt,
            "n": 1, "size": args.size, "quality": args.quality}

    print("=== DRY RUN 计划（加 --run 才执行）===" if not args.run else "=== 执行计划 ===")
    print(json.dumps({"method": "POST", "url": url, "body": body, "计费": "1 次图片生成"}, ensure_ascii=False, indent=2))
    if not args.run:
        return 0
    key = os.environ.get("NUOAPI_API_KEY", "")
    if not key or not args.model:
        print("错误: --run 需要环境变量 NUOAPI_API_KEY 与 --model（模型名以模型广场为准）。", file=sys.stderr)
        return 2

    request = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=360) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as err:
        print(f"HTTP {err.code}: {err.read().decode('utf-8', errors='replace')[:300]}", file=sys.stderr)
        print("404 model_not_found 查分组与模型名；400 requires an image model 查模型名前缀白名单。", file=sys.stderr)
        return 3
    except urllib.error.URLError as err:
        print(f"网络错误: 无法连接网关（DNS 解析失败/TLS 握手失败/请求超时）：{err.reason}", file=sys.stderr)
        return 3

    item = (payload.get("data") or [{}])[0]
    b64 = item.get("b64_json") or item.get("b64")
    image_url = item.get("url") or item.get("image_url")
    if not b64 and not image_url:
        print("响应里既无 b64_json 也无 url，打印前 300 字符：", file=sys.stderr)
        print(json.dumps(payload, ensure_ascii=False)[:300], file=sys.stderr)
        return 4

    if b64:
        try:
            image_bytes = decode_b64_image(b64)
        except ValueError as err:
            print(f"错误: {err}", file=sys.stderr)
            return 5
    else:
        parsed = urllib.parse.urlparse(image_url)
        if parsed.scheme != "https":
            print(f"错误: 第三方图片 URL 必须是 https，实际为 {parsed.scheme or '未知'}：{image_url}", file=sys.stderr)
            return 5
        print(f"下载第三方托管 URL: {image_url}（勿用于敏感素材）")
        try:
            with urllib.request.urlopen(image_url, timeout=120) as img_resp:
                image_bytes = img_resp.read()
        except urllib.error.HTTPError as err:
            print(f"下载失败 HTTP {err.code}: {err.read().decode('utf-8', errors='replace')[:300]}", file=sys.stderr)
            return 5
        except urllib.error.URLError as err:
            print(f"下载失败: 网络错误（DNS/TLS/超时）：{err.reason}", file=sys.stderr)
            return 5

    os.makedirs(args.outdir, exist_ok=True)
    fmt = detect_format(image_bytes)
    out_path = os.path.join(args.outdir, f"image-{int(__import__('time').time())}.{fmt}")
    with open(out_path, "wb") as fh:
        fh.write(image_bytes)
    width, height = png_dimensions(image_bytes)
    dim_text = f"{width}x{height}" if width else "非 PNG，未解析尺寸"
    print(f"已保存: {os.path.abspath(out_path)}")
    print(f"实际格式: {fmt} · 字节数: {len(image_bytes)} · 实际尺寸: {dim_text}（请求 size={args.size} 不能替代交付检查）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
