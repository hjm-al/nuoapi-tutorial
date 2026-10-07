#!/usr/bin/env python3
"""账单对账与系统前缀估算（零第三方依赖，默认 DRY RUN）。

回答买方最关心的两个问题：
  1. 我每发一条请求，网关替上游"白送"了多少我没写的输入 token（系统前缀注入）？
  2. 缓存读取项（cache_read / cached_tokens）有没有收我的钱？占比多少？

两种数据来源：
  A. 离线模式 --from-bundle evidence/*.json
     直接消费 evidence_capture.py 落盘的证据包（推荐，零新增计费）；
     也接受裸的 chat completion 响应 JSON（含 usage 字段），此时用户字符数记为"未知"。
  B. 实时模式（默认）：发"短/长"两条差分最小请求反推前缀量。
     短提示 "ping"，长提示为可控填充词；默认 DRY RUN，--run 才发 2 次计费请求。

口径声明（重要）：
  - 用户 token 只能按字符数估算（英文约 4 字符/token，中文约 1 字符/token），
    所以前缀量给的是【区间】，结论属 C 级推断，不是精确审计值；
  - 精确扣费以控制台账单为准，本脚本只核对响应 usage 字段与量级；
  - 不同分组倍率不同，--rate-input 给出的是站内倍率口径（页面约定 1 CNY=1 USD）。

用法：
  python examples/cost_audit.py --from-bundle evidence/a.json evidence/b.json
  python examples/cost_audit.py --model MODEL_NAME --run
  python examples/cost_audit.py --model MODEL_NAME --run --rate-input 0.3 --out audit.csv
"""

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.request

CACHE_KEY_HINTS = ("cache_read", "cache_creation", "cached_tokens", "prompt_tokens_details")
KEY_MASK = "sk-abc…xyz"


def mask_key_text(text: str, key: str) -> str:
    """错误文本对外输出前先把 Key 整串掩码。"""
    s = str(text)
    return s.replace(key, KEY_MASK) if key else s


def user_chars_of_body(body: dict | None) -> int | None:
    if not body:
        return None
    total = 0
    for msg in body.get("messages", []):
        content = msg.get("content")
        if isinstance(content, str):
            total += len(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    total += len(part["text"])
    return total or None


def cache_fields(usage: dict) -> dict:
    """递归找出所有缓存相关 usage 字段（字段名本身就是 A 级痕迹，缺失也要显式记录）。"""
    found = {}

    def walk(obj, prefix=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                name = f"{prefix}.{k}" if prefix else k
                # 只记录标量叶子：父级 dict 展开后信息量为零，还会让表格噪声变大
                if any(hint in k.lower() for hint in CACHE_KEY_HINTS) and isinstance(v, (int, float, str, bool)):
                    found[name] = v
                walk(v, name)
    walk(usage)
    return found


def estimate_user_tokens(chars: int | None) -> tuple[float, float]:
    """字符→token 粗估区间：中文密（1 字符/token）到英文疏（4 字符/token）。"""
    if chars is None:
        return (float("nan"), float("nan"))
    return (chars / 4.0, float(chars))


def analyze_record(label: str, usage: dict, user_chars: int | None, rate_input: float | None) -> dict:
    prompt = usage.get("prompt_tokens", usage.get("input_tokens"))
    completion = usage.get("completion_tokens", usage.get("output_tokens"))
    total = usage.get("total_tokens")
    caches = cache_fields(usage)
    cache_read_value = None
    for name, value in caches.items():
        if "cache_read" in name and isinstance(value, (int, float)):
            cache_read_value = value
    low, high = estimate_user_tokens(user_chars)
    overhead_low = overhead_high = None
    if isinstance(prompt, (int, float)) and user_chars is not None:
        overhead_low = max(prompt - high, 0.0)
        overhead_high = max(prompt - low, 0.0)
    cost_in = None
    if rate_input is not None and isinstance(prompt, (int, float)):
        cost_in = prompt * rate_input / 1_000_000
    return {
        "记录": label,
        "用户字符": "未知" if user_chars is None else user_chars,
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
        "缓存字段": json.dumps(caches, ensure_ascii=False) if caches else "（无缓存字段）",
        "cache_read_tokens": "未知" if cache_read_value is None else cache_read_value,
        "估算前缀/额外输入token区间": (
            "未知" if overhead_low is None else f"{overhead_low:.0f} ~ {overhead_high:.0f}"
        ),
        "输入成本估算(倍率口径)": "未知" if cost_in is None else f"{cost_in:.6f}",
    }


def load_bundles(paths: list[str]) -> list[dict]:
    """加载证据包/裸响应。usage 缺失或为空 dict（错误信封）时返回 usage=None 的标记记录，
    由上层统一打印"请求未返回 usage"且不计入对账统计，而不是静默丢弃。"""
    records = []
    for path in paths:
        label = os.path.basename(path)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            records.append({"label": label, "usage": None, "chars": None,
                            "reason": f"文件无法解析（{type(exc).__name__}），未取得 usage"})
            continue
        # evidence_capture.py 的证据包形态
        if isinstance(doc, dict) and "response" in doc and "request" in doc:
            resp_json = doc["response"].get("json") if isinstance(doc.get("response"), dict) else None
            usage = resp_json.get("usage") if isinstance(resp_json, dict) else None
            chars = user_chars_of_body(doc["request"].get("body"))
        else:
            usage = doc.get("usage") if isinstance(doc, dict) else None
            chars = None
        if not isinstance(usage, dict) or not usage:
            records.append({"label": label, "usage": None, "chars": chars,
                            "reason": "请求未返回 usage（错误信封或字段缺失/为空）"})
        else:
            records.append({"label": label, "usage": usage, "chars": chars, "reason": ""})
    return records


def live_collect(endpoint: str, model: str, key: str, filler_chars: int) -> list[dict]:
    root = endpoint.rstrip("/")
    if root.endswith("/v1beta"):
        root = root[: -len("/v1beta")]
    url = root if root.endswith("/v1") else root + "/v1"
    url += "/chat/completions"
    filler = ("the quick brown fox jumps over the lazy dog. " * (filler_chars // 45 + 1))[:filler_chars]
    prompts = {"短请求": "ping", "长请求": filler + "\n ping"}
    records = []
    for label, text in prompts.items():
        body = {"model": model, "max_tokens": 1, "messages": [{"role": "user", "content": text}]}
        req = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read()
                status = resp.status
                content_type = resp.headers.get("Content-Type", "")
        except urllib.error.HTTPError as err:
            # 先掩码 Key 再截断：错误信封可能回显 Authorization
            detail = mask_key_text(err.read().decode("utf-8", "replace"), key)[:300]
            raise SystemExit(f"错误: {label} HTTP {err.code}：{detail}")
        except urllib.error.URLError as err:
            why = getattr(err, "reason", err)
            detail = mask_key_text(str(why), key)[:300]
            raise SystemExit(f"错误: {label} 网络请求未完成（{type(why).__name__}：{detail}），已停止对账。")
        # 与 check_usage 同一纪律：200 HTML 是网关兜底页，不是账单数据
        if "json" not in content_type.lower():
            raise SystemExit(
                f"错误: {label} 返回 HTTP {status} 但 Content-Type={content_type!r}，不是 JSON"
                "（疑似网关兜底页），不予对账，已停止。")
        try:
            payload = json.loads(raw.decode("utf-8", "replace"))
        except json.JSONDecodeError:
            raise SystemExit(f"错误: {label} 响应声明为 JSON 但解析失败，按证据不足处理，已停止对账。")
        usage = payload.get("usage") if isinstance(payload, dict) else None
        if not isinstance(usage, dict) or not usage:
            # 错误信封（{"error": ...}）或网关吞字段：标记并排除，不拿空 usage 凑统计
            print(f"[不计入对账] {label}：请求未返回 usage（错误信封或网关吞字段）", file=sys.stderr)
            records.append({"label": label, "usage": None, "chars": len(text),
                            "reason": "请求未返回 usage（错误信封或网关吞字段）"})
            continue
        records.append({"label": label, "usage": usage, "chars": len(text), "reason": ""})
    return records


def print_table(rows: list[dict]):
    if not rows:
        print("没有可分析的记录。")
        return
    headers = list(rows[0].keys())
    widths = {h: max(len(h), *(len(str(r.get(h, ""))) for r in rows)) for h in headers}
    print(" | ".join(h.ljust(widths[h]) for h in headers))
    print("-+-".join("-" * widths[h] for h in headers))
    for r in rows:
        print(" | ".join(str(r.get(h, "")).ljust(widths[h]) for h in headers))


def main() -> int:
    ap = argparse.ArgumentParser(description="账单对账与系统前缀估算（默认 DRY RUN）")
    ap.add_argument("--from-bundle", nargs="+", default=[], help="evidence_capture 证据包或裸响应 JSON")
    ap.add_argument("--endpoint", default=os.environ.get("NUOAPI_BASE_URL", "https://nuoapi.net/v1"))
    ap.add_argument("--model", default=os.environ.get("NUOAPI_MODEL", ""))
    ap.add_argument("--filler-chars", type=int, default=3000, help="实时长请求填充字符数")
    ap.add_argument("--rate-input", type=float, default=None, help="分组输入倍率（每 1M token，站内 1:1 口径）")
    ap.add_argument("--out", help="可选：把表格另存为 CSV")
    ap.add_argument("--run", action="store_true", help="实时模式下真正发起 2 次计费请求")
    args = ap.parse_args()

    if args.from_bundle:
        raw_records = load_bundles(args.from_bundle)
    else:
        plan = {"mode": "live", "endpoint": args.endpoint.rstrip("/"), "model": args.model or "MODEL_NAME_FROM_MODEL_PLAZA",
                "计费请求数": 2, "长请求填充字符": args.filler_chars}
        print("=== DRY RUN 计划（加 --run 才执行；离线分析请用 --from-bundle）===")
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        if not args.run:
            return 0
        key = os.environ.get("NUOAPI_API_KEY", "")
        if not key or not args.model:
            print("错误: 实时模式 --run 需要 NUOAPI_API_KEY 与 --model。", file=sys.stderr)
            return 2
        raw_records = live_collect(args.endpoint, args.model, key, args.filler_chars)

    # usage 缺失/为空的记录只做标记，不进入对账统计
    skipped = [r for r in raw_records if r.get("usage") is None]
    valid = [r for r in raw_records if r.get("usage") is not None]
    for r in skipped:
        print(f"[不计入对账] {r['label']}：{r.get('reason') or '请求未返回 usage'}")
    rows = [analyze_record(r["label"], r["usage"], r["chars"], args.rate_input) for r in valid]
    print_table(rows)
    if rows:
        print("\n口径: 前缀区间为 C 级估算（用户 token 按 1~4 字符/token 包络）；cache_read 字段存在即说明缓存项被单独计量，"
              "是否打折/是否重复计入以控制台账单为准。")

    if args.out:
        if not rows:
            print("错误: 没有可写入 CSV 的对账记录（所有记录均未返回 usage），未写出文件。", file=sys.stderr)
            return 1
        with open(args.out, "w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"已写出: {os.path.abspath(args.out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
