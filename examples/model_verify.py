#!/usr/bin/env python3
"""三段式模型真伪探针（防掺水 / 防调包）· 零依赖标准库实现。

设计原则（详见 docs/MODEL_VERIFICATION_METHODS.md）：
  A 段 —— 协议与字段取证：只读响应骨架、计费字段与响应头，不依赖模型配合，判别力高、成本≈0；
  B 段 —— 输出分布指纹：37 道「只回一个词/一个数」的探针（18 道闭集题 + 19 道开放命名题，含 6 道中文题），
          闭集题比整份分布的 JS 散度、开放题比众数占比差，每题重复 n 次，
          与基线做置换检验 + Holm-Bonferroni 校正，判别力中-高；
  C 段 —— 能力埋针：长上下文 canary，证明「标称能力是否兑现」，默认关闭（费用最高）。
          自动化范围说明：C 段目前只实现长上下文针探；附件真读（PDF/图片暗号）、
          工具链/结构输出、web_search 空结果检测是方法学第四节的手工方法，未自动化。

输出只允许三态：匹配 / 不匹配 / 证据不足。
只有 A/B/C 段信号可以支撑「不匹配」；耗时、模型自述一律不参与判定。

B 段的统计纪律（本次修订的核心，务必读完再对外引用结论）：
  1. 高基数开放题（"说一种动物"）在 n=5 时**必然**互不相同，逐符号分布比对会把随机性
     误判成调包 —— 实测同一模型自比 JS 散度可达 1.000。因此开放题只比「众数占比」
     这类低方差集中度统计量，闭集题（硬币/猜拳/星期）才比整份分布（JS）。
  2. 阈值不再拍脑袋：每道探针做置换检验（打乱新旧标签重算统计量），得到经验 p 值，
     再对全部被检探针做 Holm-Bonferroni 校正；同时要求效应量过下限。
  3. 单道探针失败不定罪：至少 `--min-fails`（默认 2）道探针同时显著且过效应下限，
     总评才允许「不匹配」，否则记「证据不足」。

用法：
  python examples/model_verify.py                      # DRY RUN，打印计划与预估用量（不产生计费）
  python examples/model_verify.py --selftest           # 离线自测，零请求零计费
  python examples/model_verify.py --tier A --run       # 只跑 A 段（1 次极短计费请求）
  python examples/model_verify.py --claims anthropic --run   # 改打 /v1/messages，字段取证同步切换
  python examples/model_verify.py --tier A,B --reps 8 --run --save baseline_sol.json
  python examples/model_verify.py --tier B --run --compare baseline_sol.json

参数与环境变量（同名命令行参数优先于环境变量）：
  NUOAPI_API_KEY             必填（--run 时）
  --endpoint / NUOAPI_BASE_URL  默认 https://nuoapi.net/v1
  --model / NUOAPI_MODEL     必填（--run 时），必须是当前 Key 分组里真实存在的模型名
"""

import argparse
import json
import math
import os
import random
import re
import string
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE_URL = "https://nuoapi.net/v1"
PERM_SEED = 20260925

# ── B 段探针：期望答案是单个词或数字，用来观测输出分布 ────────────────────────
# class="closed" 选项集合很小（≤12），比对整份分布（JS 散度）有意义；
# class="open"   开放命名题，词汇空间近乎无限，只能比对集中度（众数占比）。
TOKEN_PROBES = [
    ("coin", "You flip a coin. Reply with ONLY heads or tails.", "closed"),
    ("rps", "Reply with ONLY one of: rock, paper, scissors.", "closed"),
    ("digit_repeat", "Reply with a single random digit (0-9) and nothing else.", "closed"),
    ("rand_1_10", "Pick a random integer from 1 to 10. Reply with ONLY the digit.", "closed"),
    ("weekday", "Name one day of the week. Reply with ONLY one word.", "closed"),
    ("month", "Name one month of the year. Reply with ONLY one word.", "closed"),
    ("planet", "Name one planet of the solar system. Reply with ONLY one word.", "closed"),
    ("yes_no_maybe", "Reply with ONLY one of: yes, no, maybe.", "closed"),
    ("direction", "Name one compass direction (N/E/S/W). Reply with ONLY one word.", "closed"),
    ("vowel", "Name one vowel letter. Reply with ONLY that letter.", "closed"),
    ("season", "Name one season of the year. Reply with ONLY one word.", "closed"),
    ("die_face", "Roll a six-sided die. Reply with ONLY the number.", "closed"),
    ("color", "Name one color. Reply with ONLY one word.", "closed"),
    ("traffic_light", "Name one traffic-light color. Reply with ONLY one word.", "closed"),
    ("suit", "Name one playing-card suit. Reply with ONLY one word.", "closed"),
    ("rand_1_100", "Think of a random integer between 1 and 100. Reply with ONLY that number.", "open"),
    ("animal", "Name one animal. Reply with ONLY one word.", "open"),
    ("fruit", "Name one fruit. Reply with ONLY one word.", "open"),
    ("verb", "Name one action verb. Reply with ONLY one word.", "open"),
    ("metal", "Name one metal. Reply with ONLY one word.", "open"),
    ("vehicle", "Name one vehicle. Reply with ONLY one word.", "open"),
    ("body_part", "Name one body part. Reply with ONLY one word.", "open"),
    ("tool", "Name one hand tool. Reply with ONLY one word.", "open"),
    ("music_instr", "Name one musical instrument. Reply with ONLY one word.", "open"),
    ("weather", "Name one weather condition. Reply with ONLY one word.", "open"),
    ("fabric", "Name one fabric. Reply with ONLY one word.", "open"),
    ("sport", "Name one sport. Reply with ONLY one word.", "open"),
    ("emotion", "Name one emotion. Reply with ONLY one word.", "open"),
    ("shape", "Name one geometric shape. Reply with ONLY one word.", "open"),
    ("mineral", "Name one gemstone. Reply with ONLY one word.", "open"),
    ("tree", "Name one kind of tree. Reply with ONLY one word.", "open"),
    ("zh_color", "说出一种颜色。只回复一个词，不要加标点。", "closed"),
    ("zh_month", "说出一年中的一个月份。只回复一个词。", "closed"),
    ("zh_digit", "随意想一个 0 到 9 的数字。只回复那个数字。", "closed"),
    ("zh_animal", "说出一种动物。只回复一个词。", "open"),
    ("zh_fruit", "说出一种水果。只回复一个词。", "open"),
    ("zh_emotion", "说出一种情绪。只回复一个词。", "open"),
]

PROBE_BY_NAME = {name: (prompt, cls) for name, prompt, cls in TOKEN_PROBES}

# 每类探针下结论所需的最低有效样本量（低于此数一律「证据不足」）
MIN_REPS_BY_CLASS = {"closed": 8, "open": 5}
# 每类探针使用的统计量：closed → 整份分布的 JS 散度；open → 众数占比之差
STAT_BY_CLASS = {"closed": "js", "open": "modal"}
# 效应量下限：p 显著但差异过小，不足以指控调包
EFFECT_FLOOR = {"js": 0.15, "modal": 0.30}

# 上游协议族的期望特征：端点路径、计费字段、骨架字段
FAMILY_SIGNATURES = {
    "openai": {
        "id_prefix": "chatcmpl-",
        "usage_fields": {"prompt_tokens", "completion_tokens", "total_tokens"},
        "usage_key": "usage",
        "skeleton_fields": {"choices"},
    },
    "anthropic": {
        "id_prefix": "msg_",
        "usage_fields": {"input_tokens", "output_tokens"},
        "usage_key": "usage",
        "skeleton_fields": {"content", "stop_reason"},
    },
    "gemini": {
        "id_prefix": None,
        "usage_fields": {"promptTokenCount", "candidatesTokenCount"},
        "usage_key": "usageMetadata",
        "skeleton_fields": {"candidates"},
    },
}


def mask(secret):
    if not secret or len(secret) < 12:
        return "***"
    return f"{secret[:4]}…{secret[-4:]}"


def safe_error_text(text, key=None, limit=400):
    """构造向上抛/对外打印的错误文本前，先把 Key 整串掩码，再截断。

    上游错误体（4xx/5xx HTML 或 JSON 信封）可能回显 Authorization 头，
    所有 RuntimeError/提示语一律走这里，避免凭据明文进日志与终端。
    """
    s = str(text)
    if key:
        s = s.replace(key, mask(key))
    return s[:limit]


def root_of(base_url):
    """把 https://x/v1、https://x/v1beta 归一成 https://x，供多协议族拼路径。"""
    return re.sub(r"/(v1beta\d*|v1)/?$", "", base_url.rstrip("/"))


def build_request(claims, base_url, key, model, prompt, max_tokens, temperature):
    """按声称的协议族拼出 (url, headers, payload)。--claims 与实际请求路径必须同源。"""
    root = root_of(base_url)
    if claims == "anthropic":
        return (
            f"{root}/v1/messages",
            {
                "Content-Type": "application/json",
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
            {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
    if claims == "gemini":
        enc = urllib.parse.quote(model, safe="")
        return (
            f"{root}/v1beta/models/{enc}:generateContent",
            {"Content-Type": "application/json", "x-goog-api-key": key},
            {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
            },
        )
    return (
        f"{root}/v1/chat/completions",
        {"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
    )


def extract_text(claims, obj):
    """从三种协议族的响应里取出助手文本。"""
    if not isinstance(obj, dict):
        return ""
    if claims == "anthropic":
        return "".join(
            b.get("text", "") for b in obj.get("content", []) if isinstance(b, dict)
        )
    if claims == "gemini":
        out = []
        for cand in obj.get("candidates", []) or []:
            parts = (cand.get("content") or {}).get("parts") or []
            out.append("".join(p.get("text", "") for p in parts if isinstance(p, dict)))
        return "".join(out)
    choices = obj.get("choices") or [{}]
    return str((choices[0].get("message") or {}).get("content", "") or "")


def extract_usage(claims, obj):
    fam = FAMILY_SIGNATURES.get(claims, FAMILY_SIGNATURES["openai"])
    usage = (obj or {}).get(fam["usage_key"]) or {}
    return usage if isinstance(usage, dict) else {}


def call_api(claims, base_url, key, model, prompt, max_tokens, temperature, timeout=60):
    """返回 (解析后的 JSON, 响应头对象, 原始文本, 实际请求 URL, 耗时秒)。失败时抛 RuntimeError。"""
    url, headers, payload = build_request(claims, base_url, key, model, prompt, max_tokens, temperature)
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return _safe_json(raw), resp.headers, raw, url, time.time() - t0
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        raise RuntimeError(safe_error_text(f"HTTP {exc.code} @ {url}: {raw}", key)) from exc
    except urllib.error.URLError as exc:  # DNS/TLS/超时
        raise RuntimeError(safe_error_text(f"{type(exc).__name__} @ {url}: {getattr(exc, 'reason', exc)}", key)) from exc
    except Exception as exc:  # 其它未预期异常，同样先掩码再抛出
        raise RuntimeError(safe_error_text(f"{type(exc).__name__} @ {url}: {exc}", key)) from exc


def _safe_json(raw):
    try:
        return json.loads(raw)
    except Exception:
        return None


def looks_like_html(raw):
    return raw.lstrip()[:1] == "<" or "<html" in raw[:400].lower()


def header_all(headers, name):
    """取重复响应头的全部取值。dict(headers) 只会留下第一个，必须走 get_all。"""
    getter = getattr(headers, "get_all", None)
    if callable(getter):
        vals = getter(name) or []
    elif isinstance(headers, dict):
        vals = [v for k, v in headers.items() if k.lower() == name.lower() for v in ([v] if not isinstance(v, list) else v)]
    else:
        vals = []
    return [str(v).strip() for v in vals if str(v).strip()]


# ── A 段：协议与字段取证 ───────────────────────────────────────────────────────
def tier_a(obj, headers, raw, claims):
    """返回 [(信号名, 三态, 判别力, 说明)]"""
    out = []
    fam = FAMILY_SIGNATURES.get(claims, FAMILY_SIGNATURES["openai"])

    if looks_like_html(raw):
        out.append(("响应体格式", "不匹配", "高", "标称 JSON 接口却返回 HTML —— 该路径未注册或被兜底页接管"))
        return out
    if not isinstance(obj, dict):
        out.append(("响应体解析", "证据不足", "高", "无法解析为 JSON，跳过字段取证"))
        return out

    skeleton = fam["skeleton_fields"] - set(obj)
    if skeleton:
        out.append(("响应骨架", "不匹配", "高", f"标称 {claims} 协议却缺少 {sorted(skeleton)} 顶层字段"))
    else:
        out.append(("响应骨架", "匹配", "高", f"顶层含 {sorted(fam['skeleton_fields'])}"))

    rid = str(obj.get("id", ""))
    if fam["id_prefix"]:
        if rid.startswith(fam["id_prefix"]):
            out.append(("id 前缀", "匹配", "高", f"期望 {fam['id_prefix']}，实际 {rid[:24]}"))
        elif rid and re.match(r"^[a-z]{2,10}[_-]", rid):
            out.append(("id 前缀", "不匹配", "高", f"期望 {fam['id_prefix']}，实际 {rid[:24]}（前缀属另一协议族）"))
        else:
            out.append(("id 前缀", "证据不足", "中", f"期望 {fam['id_prefix']}，实际 {rid[:24] or '(空/非典型形状)'}"))
    else:
        out.append(("id 前缀", "证据不足", "低", f"{claims} 协议本身无 id 字段，跳过（实际 {rid[:24] or '(空)'})"))

    usage = extract_usage(claims, obj)
    ukeys = set(usage)
    if fam["usage_fields"] <= ukeys:
        out.append(("usage 字段族", "匹配", "高", f"命中 {sorted(fam['usage_fields'])}"))
    elif ukeys:
        out.append(("usage 字段族", "不匹配", "高", f"期望 {sorted(fam['usage_fields'])}，实际 {sorted(ukeys)}"))
    else:
        out.append(("usage 字段族", "证据不足", "中", f"响应无 {fam['usage_key']}，无法核对计费字段"))

    foreign = {k for k in ukeys if re.search(r"(usd_ticks|cost_usd|credits)", k, re.I)}
    if foreign:
        out.append(("上游计费单位", "不匹配", "高", f"透传了非本站体系的计费字段 {sorted(foreign)}（多为上游订阅侧痕迹）"))

    echoed = obj.get("model") or obj.get("modelVersion")
    if echoed:
        out.append(("model 回显", "匹配", "低", f"回显 {echoed}（回显值由网关控制，不能证明上游身份）"))

    ids = []
    for hname in ("X-Request-Id", "X-Request-ID", "X-Oneapi-Request-Id"):
        ids += [x.strip() for v in header_all(headers, hname) for x in v.split(",") if x.strip()]
    if len(ids) > 1:
        shapes = {
            "uuid" if re.match(r"^[0-9a-f]{8}-", i)
            else "bare-hex" if re.match(r"^[0-9a-f]{32}$", i)
            else "other"
            for i in ids
        }
        out.append(("X-Request-Id 跳数", "不匹配" if len(shapes) > 1 else "证据不足", "中", f"追加了 {len(ids)} 个 ID，形状 {sorted(shapes)}"))
    elif len(ids) == 1:
        out.append(("X-Request-Id 跳数", "证据不足", "低", f"单跳 {ids[0][:24]}（网关只记一跳，不足以推断链路）"))

    cached = usage.get("prompt_tokens_details", {}) if isinstance(usage.get("prompt_tokens_details"), dict) else {}
    cr = usage.get("cache_read_input_tokens") or cached.get("cached_tokens") or 0
    pt = usage.get("prompt_tokens") or usage.get("input_tokens") or usage.get("promptTokenCount") or 0
    if pt and cr / pt > 0.5:
        out.append(("注入前缀迹象", "证据不足", "中", f"prompt={pt} 而缓存读取={cr}，本地输入极小 → 网关很可能加了系统前缀（成本项，不是身份项）"))
    return out


# ── B 段：输出分布指纹（置换检验 + 多重比较校正）────────────────────────────────
def normalize_answer(text):
    """保留 ASCII 词字符与中日韩文字；小写、去标点。"""
    s = re.sub(r"[^0-9a-z\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]", "", str(text).lower())
    return s[:16] or "empty"


def collect_profile(claims, base_url, key, model, reps, dry):
    """返回 (profile, error_stats)。

    error_stats = {"total": 实际请求数, "errors": {异常类型名: 次数}}；
    首个出现的错误类型即 next(iter(errors))，供上层区分「样本随机性」与「整段配置/鉴权失败」。
    """
    profile, error_counts = {}, {}
    total_calls = 0
    for name, prompt, _cls in TOKEN_PROBES:
        answers = []
        for _ in range(reps):
            if dry:
                answers.append("(dry-run)")
                continue
            total_calls += 1
            try:
                obj, _h, _r, _u, _t = call_api(claims, base_url, key, model, prompt, max_tokens=2, temperature=1.0)
                answers.append(normalize_answer(extract_text(claims, obj)))
            except Exception as exc:
                kind = type(exc).__name__
                error_counts[kind] = error_counts.get(kind, 0) + 1
                answers.append(f"error:{kind}")
        profile[name] = answers
    return profile, {"total": total_calls, "errors": error_counts}


def _counts(xs):
    c = {}
    for x in xs:
        c[x] = c.get(x, 0) + 1
    return c


def _entropy(counts):
    total = sum(counts.values())
    if not total:
        return 0.0
    return -sum((c / total) * math.log2(c / total) for c in counts.values() if c)


def _js_div(p, q):
    keys = set(p) | set(q)
    s1, s2 = sum(p.values()) or 1, sum(q.values()) or 1
    pv = {k: p.get(k, 0) / s1 for k in keys}
    qv = {k: q.get(k, 0) / s2 for k in keys}
    m = {k: (pv[k] + qv[k]) / 2 for k in keys}

    def kl(a, b):
        return sum(a[k] * math.log2(a[k] / b[k]) for k in keys if a[k] > 0 and b[k] > 0)

    return (kl(pv, m) + kl(qv, m)) / 2


def _modal_share(xs):
    if not xs:
        return 0.0
    return max(_counts(xs).values()) / len(xs)


def stat_value(kind, a, b):
    if kind == "js":
        return _js_div(_counts(a), _counts(b))
    return abs(_modal_share(a) - _modal_share(b))


def permutation_test(a, b, kind, n_perm, seed=PERM_SEED):
    """标签可换性零假设下的双侧经验 p 值：打乱新旧样本重算统计量。"""
    obs = stat_value(kind, a, b)
    pool = list(a) + list(b)
    n = len(a)
    rng = random.Random(seed)
    ge = 0
    for _ in range(n_perm):
        rng.shuffle(pool)
        if stat_value(kind, pool[:n], pool[n:]) >= obs - 1e-12:
            ge += 1
    return obs, (ge + 1) / (n_perm + 1)


def holm_adjust(items, alpha):
    """Holm-Bonferroni：items = [(name, p, eff)] → [(name, p_adj, eff, 是否过校正)]。"""
    order = sorted(items, key=lambda it: it[1])
    m = len(order)
    out, running = [], 0.0
    for idx, (name, p, eff) in enumerate(order):
        adjusted = min(1.0, max(running, (m - idx) * p))
        running = adjusted
        out.append((name, adjusted, eff, adjusted < alpha))
    return {name: (p_adj, eff, ok) for name, p_adj, eff, ok in out}


def _samples(container, name):
    return [a for a in (container or {}).get(name, []) if not str(a).startswith(("(dry", "error:"))]


def probes_of(container):
    """兼容两种基线形状：{探针: [...]} 或 {"_meta": {...}, "probes": {探针: [...]}}。"""
    if isinstance(container, dict) and isinstance(container.get("probes"), dict):
        return container["probes"]
    return container if isinstance(container, dict) else {}


def meta_of(container):
    if isinstance(container, dict) and isinstance(container.get("_meta"), dict):
        return container["_meta"]
    return {}


def tier_b_report(new, baseline=None, alpha=0.05, n_perm=2000, min_fails=2, seed=PERM_SEED):
    """返回 (rows, summary)。rows=[(探针, 三态, 判别力, 说明)]"""
    base = probes_of(baseline)
    rows, tested = [], []
    warnings = []

    for name, _prompt, cls in TOKEN_PROBES:
        need = MIN_REPS_BY_CLASS[cls]
        mine = _samples(new, name)
        if len(mine) < need:
            rows.append((name, "证据不足", "高", f"有效样本 {len(mine)}/{need}（{cls} 类探针的最低重复数），不足以下结论"))
            continue
        counts = _counts(mine)
        ent = max(0.0, _entropy(counts))
        modal, modal_n = max(counts.items(), key=lambda kv: kv[1])
        if baseline is None:
            rows.append((name, "证据不足", "高", f"众数 {modal}({modal_n}/{len(mine)}) 熵 {ent:.2f} —— 未提供参考分布，无法判真伪"))
            continue
        theirs = _samples(base, name)
        if len(theirs) < need:
            rows.append((name, "证据不足", "高", f"基线该探针只有 {len(theirs)}/{need} 个样本（基线覆盖不完整或探针集已换）"))
            warnings.append(f"{name} 在基线里样本不足")
            continue
        kind = STAT_BY_CLASS[cls]
        obs, p = permutation_test(mine, theirs, kind, n_perm, seed)
        tested.append((name, p, obs))
        floor = EFFECT_FLOOR[kind]
        note = f"{kind}={obs:.3f} p={p:.4f}（{n_perm} 次置换）；本次众数 {modal}({modal_n}/{len(mine)}) 熵 {ent:.2f}"
        if obs < floor:
            rows.append((name, "证据不足", "中", f"{note} —— 效应量低于下限 {floor}，差异太小不足以指控调包"))
        else:
            rows.append((name, "__pending__", "高", f"{note} —— 效应量过下限 {floor}，待多重比较校正"))

    corrected = holm_adjust(tested, alpha) if tested else {}
    min_p = 1.0 / (n_perm + 1)
    fails, underpowered = [], []
    for idx, (name, verdict, weight, detail) in enumerate(rows):
        if verdict != "__pending__":
            continue
        p_adj, _eff, ok = corrected[name]
        if ok:
            fails.append(name)
            rows[idx] = (name, "不匹配", weight, f"{detail}；Holm 校正后 p={p_adj:.4f} < {alpha}")
        elif permutation_floor(tested, name, min_p):
            # 置换分辨率不够：p 已到本次下限却仍过不了校正，只能记证据不足
            underpowered.append(name)
            rows[idx] = (name, "证据不足", "中",
                         f"{detail}；校正后 p={p_adj:.4f} —— p 已达 {n_perm} 次置换的分辨率下限 {min_p:.5f}，"
                         f"{len(tested)} 道探针校正需要 p<{alpha / max(1, len(tested)):.5f}，请增大 --n-perm（≥{int(len(tested) / alpha)}）")
        else:
            rows[idx] = (name, "匹配", weight, f"{detail}；Holm 校正后 p={p_adj:.4f} ≥ {alpha} —— 与基线一致")

    summary = {
        "tested": len(tested),
        "fails": fails,
        "underpowered": underpowered,
        "min_p": min_p,
        "min_fails": min_fails,
        "warnings": warnings,
        "conclusive": bool(fails) and len(fails) >= min_fails,
    }
    return rows, summary


def permutation_floor(tested, name, min_p):
    """该探针的原始 p 是否恰好压在置换分辨率下限上。"""
    for n, p, _eff in tested:
        if n == name:
            return p <= min_p + 1e-12
    return False


# ── C 段：长上下文埋针 ─────────────────────────────────────────────────────────
# 填充句实际 12 个词（The/quick/brown/fox/jumps/over/the/lazy/dog/near/the/riverbank）
C_FILLER_SENTENCE = "The quick brown fox jumps over the lazy dog near the riverbank. "
C_FILLER_WORDS_PER_COPY = 12
C_NEEDLE_QUESTION = "\nQuestion: What is the SECRET CODE in the text above? Reply with ONLY the code."


def build_tier_c_prompt(depth_words, needle):
    """C 段 prompt 的唯一构造点：filler 复制次数按句子实际词数 12 计算（depth_words//12）。

    depth_words>=1（argparse 已守卫）；极小值时至少放 1 份，避免空填充让暗号裸露。
    DRY RUN 费用预告与 tier_c 实际判定共用本函数，口径不再分叉。
    """
    copies = max(1, depth_words // C_FILLER_WORDS_PER_COPY)
    filler = C_FILLER_SENTENCE * copies
    return filler + f"\nSECRET CODE: {needle}\n" + filler + C_NEEDLE_QUESTION


def estimate_tokens(text):
    """本地 token 粗估（英文约 4 字符/token），全工具统一口径。"""
    return len(text) // 4


def tier_c(claims, base_url, key, model, depth_words, dry):
    needle = "".join(random.choices(string.ascii_uppercase, k=2)) + "-" + "".join(random.choices(string.digits, k=6))
    prompt = build_tier_c_prompt(depth_words, needle)
    est = estimate_tokens(prompt)
    if dry:
        return [("长上下文埋针", "证据不足", "高", f"DRY RUN：预计 prompt ≈ {est:,} token（费用最高的档位，确认后再加 --run）")]
    try:
        obj, _h, _r, _u, _el = call_api(claims, base_url, key, model, prompt, max_tokens=32, temperature=0.0)
    except Exception as exc:
        return [("长上下文埋针", "证据不足", "高", f"请求失败：{safe_error_text(exc, key)}")]
    got = extract_text(claims, obj) or ""
    usage = extract_usage(claims, obj)
    billed = usage.get("prompt_tokens") or usage.get("input_tokens") or usage.get("promptTokenCount") or 0
    if needle in got:
        v = "匹配" if billed >= est * 0.6 else "证据不足"
    else:
        v = "不匹配"
    return [(f"长上下文埋针(depth≈{depth_words}词)", v, "高", f"暗号 {needle} / 回显 {got.strip()[:24]!r} / 计费 prompt={billed}（本地估算≈{est:,}）")]


# ── 汇总 ──────────────────────────────────────────────────────────────────────
def print_signal_rows(rows, title):
    print(f"\n── {title} " + "─" * max(0, 58 - len(title)))
    for name, verdict, weight, detail in rows:
        print(f"  [{verdict}] ({weight}) {name:<28} {detail}")


def baseline_conflicts(baseline, base, model, claims):
    """基线元数据与本次请求不一致时给出告警行（同入口/同模型纪律）。"""
    meta = meta_of(baseline)
    rows = []
    if not meta:
        rows.append(("基线可比性", "证据不足", "高", "基线缺少 _meta（旧版本存的裸 profile），无法核对入口/模型/协议族是否同源"))
        return rows
    cur = {"endpoint": claims, "model": model, "base": root_of(base)}
    want = {"endpoint": meta.get("claims"), "model": meta.get("model"), "base": root_of(meta.get("base", "") or "")}
    diff = [f"{k}: 基线 {want[k]!r} ≠ 本次 {cur[k]!r}" for k in cur if want[k] not in (None, "", cur[k])]
    if diff:
        rows.append(("基线可比性", "证据不足", "高", "对照不同源 —— " + "；".join(diff) + "。跨入口/跨模型的分布差异不能算调包证据"))
    else:
        rows.append(("基线可比性", "匹配", "高", f"同源（{meta.get('claims')}/{meta.get('model')}，采样于 {meta.get('date', '?')}，reps={meta.get('reps', '?')}）"))
    return rows


def reconfigure_stdio_utf8():
    """Windows 重定向到文件时默认 GBK，emoji/中文会 UnicodeEncodeError；3.10+ 用 reconfigure 兜底。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def parse_tiers(raw):
    """--tier 必须是非空 {A,B,C} 子集（去重、保序）；""/D/AB/A,A 一律 ValueError。"""
    tiers = []
    for part in str(raw).split(","):
        t = part.strip().upper()
        if t not in ("A", "B", "C"):
            raise ValueError(f"无法识别的档位 {part!r}")
        if t in tiers:
            raise ValueError(f"档位 {t} 重复")
        tiers.append(t)
    if not tiers:
        raise ValueError("档位为空")
    return tiers


def main():
    ap = argparse.ArgumentParser(description="三段式模型真伪探针（默认 DRY RUN，不产生计费）")
    ap.add_argument("--tier", default="A", help="逗号分隔：A / A,B / A,B,C（默认 A）")
    ap.add_argument("--claims", default="openai", choices=list(FAMILY_SIGNATURES), help="该端点声称的上游协议族；决定请求路径与字段取证口径")
    ap.add_argument("--endpoint", default=None, help="Base URL；缺省取 NUOAPI_BASE_URL，再缺省 https://nuoapi.net/v1")
    ap.add_argument("--model", default=None, help="模型名（--run 必填）；缺省取 NUOAPI_MODEL")
    ap.add_argument("--reps", type=int, default=8, help="B 段每题重复次数（闭集题需 ≥8 才能下结论）")
    ap.add_argument("--run", action="store_true", help="真正发送计费请求；不加则只打印计划")
    ap.add_argument("--save", metavar="FILE", help="把本次 B 段 profile（含元数据）存为基线 JSON")
    ap.add_argument("--compare", metavar="FILE", help="与基线 JSON 比对（B 段判定的前提）")
    ap.add_argument("--depth", type=int, default=20000, help="C 段埋针的填充词数（越大越贵）")
    ap.add_argument("--alpha", type=float, default=0.05, help="B 段显著性水平（Holm 校正后）")
    ap.add_argument("--n-perm", type=int, default=2000, help="B 段置换次数")
    ap.add_argument("--min-fails", type=int, default=2, help="总评判「不匹配」所需的最少显著探针数")
    ap.add_argument("--selftest", action="store_true", help="离线自测（零请求、零计费）后退出")
    args = ap.parse_args()

    if args.selftest:
        return run_selftest()

    try:
        tiers = parse_tiers(args.tier)
    except ValueError as exc:
        ap.error(f"--tier 必须是非空的 A/B/C 逗号组合（A、A,B、A,B,C）：{exc}")
    if args.alpha <= 0:
        ap.error("--alpha 必须 > 0（否则显著性水平无意义且触发除零）")
    if args.reps < 1:
        ap.error("--reps 必须 ≥ 1")
    if args.depth < 1:
        ap.error("--depth 必须 ≥ 1")
    if args.n_perm < 1:
        ap.error("--n-perm 必须 ≥ 1")
    if args.min_fails < 1:
        ap.error("--min-fails 必须 ≥ 1")

    key = os.environ.get("NUOAPI_API_KEY", "")
    base = args.endpoint or os.environ.get("NUOAPI_BASE_URL", DEFAULT_BASE_URL)
    model = args.model or os.environ.get("NUOAPI_MODEL", "")

    need_reps = max(MIN_REPS_BY_CLASS.values())
    n_b = len(TOKEN_PROBES) * args.reps if "B" in tiers else 0
    url_preview = build_request(args.claims, base, key or "YOUR_KEY", model or "MODEL_NAME", "ping", 8, 0.0)[0]
    plan = [f"请求端点：{url_preview}（由 --claims {args.claims} 决定，取证口径与之绑定）"]
    if "A" in tiers:
        plan.append("A 段：1 次极短请求（max_tokens=8），只读骨架/计费字段/响应头")
    if n_b:
        low = "（低于闭集题门槛 %d，B 段全部记证据不足）" % need_reps if args.reps < need_reps else ""
        plan.append(f"B 段：{n_b} 次 1~2-token 请求（{len(TOKEN_PROBES)} 探针 × {args.reps} 重复）{low}")
        if args.n_perm < len(TOKEN_PROBES) / args.alpha:
            plan.append(
                "⚠ 统计分辨率不足："
                f"{len(TOKEN_PROBES)} 道探针做 Holm 校正需要 p < {args.alpha / len(TOKEN_PROBES):.5f}，"
                f"而 {args.n_perm} 次置换的最小 p 只有 {1 / (args.n_perm + 1):.5f} → 即使真换货也只能记证据不足。"
                f"建议 --n-perm {int(len(TOKEN_PROBES) / args.alpha) + 1} 以上"
            )
    if "C" in tiers:
        c_est = estimate_tokens(build_tier_c_prompt(args.depth, "XX-000000"))
        plan.append(f"C 段：1 次长上下文请求（估算 prompt ≈ {c_est:,.0f} token，档位最贵）")

    print("=" * 76)
    print("  三段式模型真伪探针")
    print(f"  Base URL : {base}")
    print(f"  模型     : {model or '(未设置 NUOAPI_MODEL)'}")
    print(f"  Key      : {mask(key) if key else '(未设置 NUOAPI_API_KEY)'}")
    print(f"  声称协议 : {args.claims}")
    print(f"  执行档位 : {','.join(tiers)}")
    print("-" * 76)
    for line in plan:
        print("  计划 · " + line)

    if not args.run:
        print("\nDRY RUN：以上请求尚未发送。确认费用后再加 --run。\n")
        return 0
    if not key or not model:
        print("\n错误：--run 需要同时提供 API Key（NUOAPI_API_KEY）与模型名（--model 或 NUOAPI_MODEL）。", file=sys.stderr)
        return 1

    baseline = None
    if args.compare:
        try:
            with open(args.compare, encoding="utf-8") as fh:
                baseline = json.load(fh)
        except FileNotFoundError:
            print(f"\n错误：基线文件不存在：{args.compare}。B 段没有基线时不具备判别力。", file=sys.stderr)
            return 1
        except Exception as exc:
            print(f"\n错误：基线文件无法解析：{type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        if not probes_of(baseline):
            print("\n错误：基线文件里没有探针样本（probes 为空），无法比对。", file=sys.stderr)
            return 1

    hard_fail, inconclusive, notes = False, False, []

    if "A" in tiers:
        try:
            obj, headers, raw, url, el = call_api(args.claims, base, key, model, "Reply with the single word: pong", 8, 0.0)
            rows = tier_a(obj, headers, raw, args.claims)
            print_signal_rows(rows, "A 段 · 协议与字段取证（判别力高）")
            hard_fail |= any(v == "不匹配" and w == "高" for _n, v, w, _d in rows)
            # 响应不可解析（且非 HTML 兜底页）时字段取证整段缺席，只能判证据不足
            if not isinstance(obj, dict) and not looks_like_html(raw):
                inconclusive = True
        except Exception as exc:
            print_signal_rows([("A 段请求", "证据不足", "高", safe_error_text(exc, key))], "A 段 · 协议与字段取证（请求失败）")
            inconclusive = True

    if "B" in tiers:
        profile, b_errors = collect_profile(args.claims, base, key, model, args.reps, dry=False)
        err_total = sum(b_errors["errors"].values())
        if b_errors["total"] and err_total == b_errors["total"]:
            # 37 题 × reps 全部请求失败：基本是配置/鉴权/网络问题，不是模型分布问题
            detail = "、".join(f"{kind}×{cnt}" for kind, cnt in b_errors["errors"].items()) or "未知错误"
            print(f"  ⚠ B 段全部 {b_errors['total']} 次请求失败（{detail}，首个类型 {next(iter(b_errors['errors']))}）"
                  "—— 疑似配置/鉴权错误，不进入统计比对，总评记证据不足")
            inconclusive = True
        elif err_total:
            print(f"  ⚠ B 段 {err_total}/{b_errors['total']} 次请求失败"
                  f"（{ '、'.join(f'{k}×{v}' for k, v in b_errors['errors'].items()) }），失败样本不参与统计")
        if baseline is not None:
            print_signal_rows(baseline_conflicts(baseline, base, model, args.claims), "B 段 · 对照可比性")
        rows, summary = tier_b_report(profile, baseline, args.alpha, args.n_perm, args.min_fails)
        print_signal_rows(rows, "B 段 · 输出分布指纹（置换检验）")
        print(f"  统计口径：{summary['tested']} 道探针完成检验，{len(summary['fails'])} 道显著且过效应下限；判定门槛 --min-fails {args.min_fails}")
        if summary["underpowered"]:
            print(f"  ⚠ {len(summary['underpowered'])} 道探针的 p 压在 {args.n_perm} 次置换的下限上，被记为证据不足而非匹配 —— 增大 --n-perm 后重跑")
        if args.save:
            wrapped = {
                "_meta": {
                    "tool": "model_verify.py",
                    "claims": args.claims,
                    "base": root_of(base),
                    "model": model,
                    "reps": args.reps,
                    "date": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "probe_count": len(TOKEN_PROBES),
                },
                "probes": profile,
            }
            with open(args.save, "w", encoding="utf-8") as fh:
                json.dump(wrapped, fh, ensure_ascii=False, indent=1)
            print(f"  已保存基线：{args.save}（含 _meta；该文件可能含模型输出样本，分享前自行检查）")
        b_all_failed = bool(b_errors["total"] and err_total == b_errors["total"])
        if b_all_failed:
            notes.append(f"B 段全部请求失败（{detail}，疑似配置/鉴权错误），未进入统计比对")
        elif baseline is None:
            notes.append("B 段没有参考分布时不具备判别力，请用 --compare 指定基线")
        elif summary["tested"] == 0:
            notes.append("B 段没有任何探针达到可比样本量，未做统计判定")
        elif summary["fails"] and not summary["conclusive"]:
            notes.append(f"仅 {len(summary['fails'])} 道探针显著（<{args.min_fails} 门槛），按纪律记证据不足而非不匹配")
        if summary["conclusive"] and not b_all_failed:
            hard_fail = True

    if "C" in tiers:
        rows = tier_c(args.claims, base, key, model, args.depth, dry=False)
        print_signal_rows(rows, "C 段 · 能力埋针")
        hard_fail |= any(v == "不匹配" and w == "高" for _n, v, w, _d in rows)
        # 请求失败或计费口径对不上暗号回显时，C 段都不能支撑「匹配」
        if any(v == "证据不足" for _n, v, _w, _d in rows):
            inconclusive = True

    print("\n" + "=" * 76)
    for n in notes:
        print(f"  备注：{n}")
    if hard_fail:
        print("  总评：不匹配 —— 存在通过统计与字段取证的双重反证（请附原始响应体复核，勿只截图）")
        return 3
    if inconclusive or notes:
        print("  总评：证据不足 —— 已执行档位内存在失败/前提缺口，样本或请求失败一律不得反推为匹配")
        return 0
    print("  总评：匹配（在已执行档位与样本量下未见反证；一致不等于证明为真）")
    return 0


# ── 离线自测：不联网、不计费，验证统计与取证代码本身 ────────────────────────────
def _fixture_openai(claims="openai"):
    obj = {
        "id": "chatcmpl-Abc123",
        "model": "gpt-6-astra",
        "choices": [{"message": {"role": "assistant", "content": "pong"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 1200, "completion_tokens": 1, "total_tokens": 1201,
                  "prompt_tokens_details": {"cached_tokens": 1190}},
    }
    return obj


def _fixture_headers(pairs):
    import email.message

    h = email.message.Message()
    for k, v in pairs:
        h[k] = v
    return h


def _synthetic_profile(pattern, reps=10, seed=7):
    """按 class 生成合成分布：pattern='diverse' 模拟正常随机性，'frozen' 模拟temperature=0 的换货底座。"""
    rng = random.Random(seed)
    vocab = {}
    profile = {}
    for name, _p, cls in TOKEN_PROBES:
        size = 6 if cls == "closed" else 60
        words = vocab.setdefault(str(size), [f"w{i}" for i in range(size)])
        if pattern == "frozen":
            profile[name] = [words[0]] * reps
        else:
            profile[name] = [rng.choice(words) for _ in range(reps)]
    return profile


def run_selftest():
    checks = []

    def check(label, ok, detail=""):
        checks.append((label, bool(ok), detail))
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' — ' + detail) if detail and not ok else ''}")

    print("=" * 76)
    print("  离线自测（零请求 / 零计费）")
    print("-" * 76)

    # 1. 中文答案不再被归一化吃掉（P0-4）
    check("P0-4 中文答案归一化", normalize_answer("红色。") == "红色", f"got {normalize_answer('红色。')!r}")
    check("P0-4 日文/全角保留", normalize_answer("みどり。") == "みどり")
    check("P0-4 空/标点答案", normalize_answer("!!!") == "empty")
    check("P0-4 表情符号归入 empty", normalize_answer("🐘") == "empty")

    # 2. 重复响应头必须全部读到（P0-5）
    hdrs = _fixture_headers([("X-Request-Id", "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
                            ("X-Request-Id", "0123456789abcdef0123456789abcdef")])
    got = header_all(hdrs, "X-Request-Id")
    check("P0-5 重复 X-Request-Id 取证", len(got) == 2, f"header_all → {got}")
    a = tier_a(_fixture_openai(), hdrs, json.dumps(_fixture_openai()), "openai")
    jump = [r for r in a if r[0] == "X-Request-Id 跳数"]
    check("P0-5 多跳形状不一致判不匹配", jump and jump[0][1] == "不匹配", str(jump))

    # 3. 同族签名必须判匹配，跨族残留必须判不匹配（P0-3）
    raw = json.dumps(_fixture_openai())
    a_ok = tier_a(_fixture_openai(), _fixture_headers([]), raw, "openai")
    check("A 段 同协议族无反证", not any(v == "不匹配" and w == "高" for _n, v, w, _d in a_ok), str(a_ok))
    swapped = _fixture_openai()
    swapped["id"] = "msg_01AA"
    swapped["usage"] = {"input_tokens": 9, "output_tokens": 1}
    a_sw = tier_a(swapped, _fixture_headers([]), json.dumps(swapped), "openai")
    check("A 段 跨族 id 前缀被抓", any(n == "id 前缀" and v == "不匹配" for n, v, _w, _d in a_sw), str(a_sw))
    check("A 段 跨族 usage 字段族被抓", any(n == "usage 字段族" and v == "不匹配" for n, v, _w, _d in a_sw), str(a_sw))
    anth = {"id": "msg_01AA", "content": [{"type": "text", "text": "pong"}], "stop_reason": "max_tokens",
            "model": "claude-sonnet-5", "usage": {"input_tokens": 11, "output_tokens": 1}}
    a_an = tier_a(anth, _fixture_headers([]), json.dumps(anth), "anthropic")
    check("A 段 anthropic 口径自洽", not any(v == "不匹配" and w == "高" for _n, v, w, _d in a_an), str(a_an))
    check("A 段 anthropic 文本抽取", extract_text("anthropic", anth) == "pong")
    gem = {"candidates": [{"content": {"parts": [{"text": "pong"}]}}], "usageMetadata": {"promptTokenCount": 7, "candidatesTokenCount": 1}}
    check("A 段 gemini 文本抽取", extract_text("gemini", gem) == "pong")
    a_gem = tier_a(gem, _fixture_headers([]), json.dumps(gem), "gemini")
    check("A 段 gemini 口径自洽", not any(v == "不匹配" and w == "高" for _n, v, w, _d in a_gem), str(a_gem))

    # 4. 端点随 --claims 切换（P0-3）
    u_oai = build_request("openai", "https://x/v1", "k", "m", "p", 8, 0)[0]
    u_ant = build_request("anthropic", "https://x/v1", "k", "m", "p", 8, 0)[0]
    u_gem = build_request("gemini", "https://x/v1", "k", "models/a", "p", 8, 0)[0]
    check("P0-3 端点路由", u_oai == "https://x/v1/chat/completions" and u_ant == "https://x/v1/messages"
          and u_gem == "https://x/v1beta/models/models%2Fa:generateContent", f"{u_oai} | {u_ant} | {u_gem}")
    check("P0-3 base 不带 /v1 时自动补版本网段",
          build_request("openai", "https://x", "k", "m", "p", 8, 0)[0] == "https://x/v1/chat/completions")
    check("P0-3 base 带 /v1beta 时不重复拼版本",
          build_request("gemini", "https://x/v1beta", "k", "m", "p", 8, 0)[0] == "https://x/v1beta/models/m:generateContent")

    # 5. 同一分布自比不得定罪（P0-1 / P0-2 回归：旧实现在这里必然报 5/24 不匹配）
    div_a = _synthetic_profile("diverse", reps=10, seed=11)
    div_b = _synthetic_profile("diverse", reps=10, seed=12)
    _rows, s = tier_b_report(div_a, div_b, n_perm=2000)
    check("P0-1 同分布零误报", s["tested"] > 0 and not s["fails"], f"tested={s['tested']} fails={s['fails']}")

    # 6. 真换货（输出被冻死）必须被抓到
    frozen = _synthetic_profile("frozen", reps=10)
    _rows, s2 = tier_b_report(frozen, div_a, n_perm=2000)
    check("B 段 冻住输出能被定罪", s2["conclusive"] and len(s2["fails"]) >= 3, f"fails={len(s2['fails'])}")

    # 6b. 置换次数不足时不得谎报「与基线一致」，要降级为证据不足
    _rows, s2b = tier_b_report(frozen, div_a, n_perm=200)
    check("B 段 分辨率不足时降级", not s2b["fails"] and len(s2b["underpowered"]) >= 3,
          f"fails={s2b['fails']} underpowered={len(s2b['underpowered'])}")

    # 7. 单道显著不定罪：只污染一道探针
    one = {k: list(v) for k, v in div_a.items()}
    one["coin"] = ["heads"] * 10
    _rows, s3 = tier_b_report(one, div_b, n_perm=500, min_fails=2)
    check("P0-2 单探针显著不定罪", len(s3["fails"]) <= 1 and not s3["conclusive"], f"fails={s3['fails']}")

    # 8. 样本量与基线覆盖纪律（P0-6）
    _rows, s4 = tier_b_report(div_a, None, n_perm=200)
    check("B 段 无基线时全部证据不足", all(r[1] == "证据不足" for r in _rows))
    short = {k: v[:3] for k, v in div_a.items()}
    _rows, s5 = tier_b_report(div_a, short, n_perm=200)
    check("P0-6 基线覆盖不足时不判定", s5["tested"] == 0 and len(s5["warnings"]) == 0 or s5["tested"] == 0,
          f"tested={s5['tested']}")
    thin = {k: v[:2] for k, v in div_a.items()}
    _rows, s6 = tier_b_report(thin, div_a, n_perm=200)
    check("P0-6 本次样本不足时不判定", s6["tested"] == 0)

    # 9. 基线元数据不同源要告警
    check("P0-6 缺 _meta 时降级", any(r[0] == "基线可比性" and r[1] == "证据不足" for r in baseline_conflicts({"probes": div_a}, "https://x/v1", "m", "openai")))
    same = {"_meta": {"claims": "openai", "model": "m", "base": "https://x", "date": "x", "reps": 10}, "probes": div_a}
    check("基线同源判定匹配", any(r[1] == "匹配" for r in baseline_conflicts(same, "https://x/v1", "m", "openai")))
    other = {"_meta": {"claims": "openai", "model": "other-model", "base": "https://x"}, "probes": div_a}
    check("跨模型基线判不可比", any(r[1] == "证据不足" for r in baseline_conflicts(other, "https://x/v1", "m", "openai")))

    # 10. profile 读写形状自洽
    wrapped = {"_meta": {"claims": "openai"}, "probes": div_a}
    check("基线包装可回读", probes_of(wrapped) == div_a and meta_of(wrapped).get("claims") == "openai")
    check("裸 profile 可回读", probes_of(div_a) == div_a)

    # 11. C 段填充按句 12 词复制，est 与 DRY RUN 预告同一口径（旧实现重复计 4 份 filler）
    p1200 = build_tier_c_prompt(1200, "XX-000000")
    check("C 段 filler 按 12 词/句复制", p1200.count(C_FILLER_SENTENCE) == 2 * (1200 // 12),
          f"copies seen={p1200.count(C_FILLER_SENTENCE)}")
    check("C 段 est 即 len(prompt)//4", estimate_tokens(p1200) == len(p1200) // 4)
    check("C 段预告与实算口径一致",
          estimate_tokens(build_tier_c_prompt(20000, "XX-000000")) == estimate_tokens(build_tier_c_prompt(20000, "AB-123456")))

    # 12. 上游错误体里的 Key 必须被整串掩码后再截断
    fake_key = "test-key-" + "A" * 32
    leak = safe_error_text("HTTP 500: upstream saw Authorization Bearer " + fake_key, fake_key)
    check("错误文本掩码 Key", fake_key not in leak and "A" * 8 not in leak, leak)
    check("错误文本截断 400 字符", len(safe_error_text("x" * 999, fake_key)) <= 400)

    # 13. --tier 只接受非空 {A,B,C} 子集
    check("--tier A,B 合法", parse_tiers(" A ,b ") == ["A", "B"])
    check("--tier A,B,C 合法", parse_tiers("A,B,C") == ["A", "B", "C"])
    for bad_tier in ("", "D", "AB", "A,A", "A,,B"):
        try:
            parse_tiers(bad_tier)
            check(f"--tier {bad_tier!r} 必须报错", False)
        except ValueError:
            check(f"--tier {bad_tier!r} 必须报错", True)

    bad = [c for c in checks if not c[1]]
    print("-" * 76)
    print(f"  自测结果：{len(checks) - len(bad)}/{len(checks)} 通过")
    if bad:
        print("  失败项：" + "、".join(c[0] for c in bad))
        return 1
    print("  全部通过（本自测不发送任何网络请求，不产生计费）")
    return 0


if __name__ == "__main__":
    reconfigure_stdio_utf8()
    sys.exit(main())
