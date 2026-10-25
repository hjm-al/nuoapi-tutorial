#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取 NuoAPI 模型广场的公开清单接口，落地成带明细的取证快照。

数据源是站点自己的公开 JSON 接口 ``GET https://nuoapi.net/api/v1/model-plaza``
（模型广场页面渲染用的就是它）。该接口不需要登录、不需要 API Key，
**不发起任何计费请求**，因此属于 B 级证据：只能证明"站点当前声明了什么"，
不能证明"你的 Key 实际能调用成功"。

用法::

    python examples/capture_model_plaza.py                 # 只打印统计
    python examples/capture_model_plaza.py --write         # 写 xlsx 明细
    python examples/capture_model_plaza.py --write --md     # 额外写 Markdown

口径（已用页面截图逐项核对）：

- **实付价格(折后) = 接口 ``pricing`` 字段 × 分组倍率**。接口返回的 ``pricing``
  是分组基准单价（单位 $/token），乘上 ``rate_multiplier`` 才是页面表格里
  "实付价格(折后)" 那一列。
- **官方价格 = 接口 ``official_pricing`` 字段**，是厂商参考价，与分组倍率
  没有固定算式关系，不能互相推算。
- 价格单位统一换算成 ``$ / 1M token``；按张/按秒计价的（图像、视频）单列。
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.request

PLAZA_URL = "https://nuoapi.net/api/v1/model-plaza"
ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
TOKEN_SCALE = 1_000_000


# --------------------------------------------------------------------------
# 取数
# --------------------------------------------------------------------------
def fetch_plaza(url: str = PLAZA_URL, timeout: int = 60) -> dict:
    """拉取模型广场公开接口。零计费、零凭据。"""
    request = urllib.request.Request(url, headers={"User-Agent": "nuoapi-tutorial-plaza/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


# --------------------------------------------------------------------------
# 价格换算与格式化
# --------------------------------------------------------------------------
def per_million(price_per_token) -> float | None:
    """$/token → $/1M token。"""
    if price_per_token is None:
        return None
    return float(price_per_token) * TOKEN_SCALE


def money(value) -> str:
    """按仓库既有明细表的写法格式化金额：最多 5 位小数，至少保留 2 位。"""
    if value is None:
        return "-"
    text = "{0:.6f}".format(float(value)).rstrip("0").rstrip(".")
    if "." not in text:
        return "$" + text + ".00"
    head, tail = text.split(".", 1)
    if len(tail) < 2:
        tail = tail.ljust(2, "0")
    return "$" + head + "." + tail


def tier_list(pricing: dict, key: str) -> list[tuple[str, object]]:
    """返回 [(档位标签, 单价)]；无分档时用空标签表示单档。"""
    intervals = pricing.get("intervals") or []
    if not intervals:
        return [("", pricing.get(key))]
    return [(item.get("tier_label") or "", item.get(key)) for item in intervals]


def pay_tiers(pricing: dict, key: str, multiplier: float) -> list[tuple[str, object]]:
    """实付 = 基准价 × 分组倍率。"""
    return [
        (label, None if value is None else float(value) * multiplier)
        for label, value in tier_list(pricing, key)
    ]


def format_tiers(tiers: list[tuple[str, object]], scale: float = TOKEN_SCALE) -> str:
    """把分档价格拼成一个单元格文本。"""
    parts = []
    for label, value in tiers:
        amount = money(None if value is None else value * scale)
        parts.append("{0} {1}".format(label, amount).strip())
    return " ".join(parts) if parts else "-"


def format_cache(pricing: dict, multiplier: float) -> str:
    """缓存价：写 / 1h 写 / 读。"""
    write = pricing.get("cache_write_price")
    write_1h = pricing.get("cache_write_1h_price")
    read = pricing.get("cache_read_price")
    if write is None and read is None:
        return "-"
    write_text = money(None if write is None else write * multiplier * TOKEN_SCALE)
    write_1h_text = money(None if write_1h is None else write_1h * multiplier * TOKEN_SCALE)
    read_text = money(None if read is None else read * multiplier * TOKEN_SCALE)
    return "写 {0} (1h {1}) 读 {2}".format(write_text, write_1h_text, read_text)


def format_cache_official(pricing: dict) -> str:
    write = pricing.get("cache_write_price")
    write_1h = pricing.get("cache_write_1h_price")
    read = pricing.get("cache_read_price")
    if write is None and read is None:
        return "-"
    return "写 {0} (1h {1}) 读 {2}".format(
        money(per_million(write)),
        money(per_million(write_1h)),
        money(per_million(read)),
    )


# --------------------------------------------------------------------------
# 行模型
# --------------------------------------------------------------------------
def build_rows(payload: dict) -> list[dict]:
    """把接口结构摊平成明细表行。"""
    rows = []
    for group in payload["data"]["groups"]:
        multiplier = float(group["rate_multiplier"])
        for model in group["models"]:
            pricing = model.get("pricing") or {}
            official = model.get("official_pricing") or {}
            rows.append(
                {
                    "group": group["name"],
                    "group_id": group["id"],
                    "platform": model.get("platform") or group["platform"],
                    "multiplier": multiplier,
                    "model": model["name"],
                    "pay_in": format_tiers(pay_tiers(pricing, "input_price", multiplier)),
                    "pay_out": format_tiers(pay_tiers(pricing, "output_price", multiplier)),
                    "pay_cache": format_cache(pricing, multiplier),
                    "off_in": format_tiers(tier_list(official, "input_price")),
                    "off_out": format_tiers(tier_list(official, "output_price")),
                    "off_cache": format_cache_official(official),
                    "billing_mode": pricing.get("billing_mode") or "token",
                    "per_request": pricing.get("per_request_price"),
                }
            )
    return rows


def group_summary(payload: dict) -> list[dict]:
    summary = []
    for group in payload["data"]["groups"]:
        summary.append(
            {
                "group": group["name"],
                "multiplier": group["rate_multiplier"],
                "count": len(group["models"]),
                "platform": group["platform"],
                "description": group.get("description") or "",
                "long_context": group.get("long_context_pricing_enabled"),
                "image_independent": group.get("image_rate_independent"),
            }
        )
    return summary


# --------------------------------------------------------------------------
# 输出
# --------------------------------------------------------------------------
def write_xlsx(
    rows: list[dict],
    summary: list[dict],
    path: pathlib.Path,
    source: str,
    billing_note: str = "",
) -> None:
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill

    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "模型广场"
    header = [
        "分组",
        "分组倍率",
        "模型",
        "实付输入($/1M)",
        "实付输出($/1M)",
        "实付缓存",
        "官方输入($/1M)",
        "官方输出($/1M)",
        "官方缓存",
        "行倍率",
    ]
    sheet.append(header)
    for row in rows:
        sheet.append(
            [
                row["group"],
                "{0}x".format(row["multiplier"]),
                row["model"],
                row["pay_in"],
                row["pay_out"],
                row["pay_cache"],
                row["off_in"],
                row["off_out"],
                row["off_cache"],
                "{0}x".format(row["multiplier"]),
            ]
        )

    head_fill = PatternFill("solid", fgColor="1F3B2C")
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = head_fill
        cell.alignment = Alignment(vertical="center")
    widths = [26, 10, 34, 30, 24, 44, 30, 24, 40, 10]
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[chr(64 + index)].width = width
    sheet.freeze_panes = "A2"

    total = book.create_sheet("分组汇总")
    total.append(["分组", "分组倍率", "模型数", "平台", "分组说明", "长上下文分档"])
    for item in summary:
        total.append(
            [
                item["group"],
                "{0}x".format(item["multiplier"]),
                item["count"],
                item["platform"],
                item["description"],
                "是" if item["long_context"] else "否",
            ]
        )
    for cell in total[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = head_fill
    for index, width in enumerate([28, 12, 10, 14, 24, 14], start=1):
        total.column_dimensions[chr(64 + index)].width = width
    total.freeze_panes = "A2"

    notes = book.create_sheet("说明")
    notes.append(["项目", "内容"])
    notes.append(["数据源", source])
    notes.append(["取数方式", "GET 公开 JSON 接口，未登录、未使用 API Key、未发起任何计费请求"])
    notes.append(["证据等级", "B 级（站点当前声明，不代表你的 Key 一定能调用成功）"])
    notes.append(
        ["实付价格口径", "实付价格(折后) = 接口 pricing 字段（$/token）× 分组倍率，再换算为 $/1M token"]
    )
    notes.append(["官方价格口径", "官方价格 = 接口 official_pricing 字段（$/token）换算为 $/1M token；与倍率没有固定算式"])
    notes.append(["计费口径", billing_note])
    notes.append(["生成脚本", "examples/capture_model_plaza.py"])
    for cell in notes[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = head_fill
    notes.column_dimensions["A"].width = 18
    notes.column_dimensions["B"].width = 100
    for row in notes.iter_rows(min_row=2):
        row[1].alignment = Alignment(wrap_text=True, vertical="top")

    path.parent.mkdir(parents=True, exist_ok=True)
    book.save(path)


def print_summary(payload: dict, rows: list[dict]) -> None:
    groups = payload["data"]["groups"]
    names = {row["model"] for row in rows}
    print("计费口径：{0}".format(payload["data"].get("description")))
    print("分组数：{0}".format(len(groups)))
    print("行数：{0}".format(len(rows)))
    print("去重模型名：{0}".format(len(names)))
    print("倍率档位：{0}".format(sorted({g["rate_multiplier"] for g in groups})))
    print()
    for group in groups:
        print(
            "{0:32} {1:>8}x  {2:>3} 个  platform={3}  {4}".format(
                group["name"][:32],
                group["rate_multiplier"],
                len(group["models"]),
                group["platform"],
                group.get("description") or "",
            )
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="抓取模型广场公开清单接口并落地快照")
    parser.add_argument("--url", default=PLAZA_URL, help="模型广场公开接口地址")
    parser.add_argument("--write", action="store_true", help="写出 xlsx 明细")
    parser.add_argument(
        "--out",
        type=pathlib.Path,
        default=None,
        help="xlsx 输出路径（默认 docs/模型广场清单-2026-10-25.xlsx）",
    )
    parser.add_argument("--md", action="store_true", help="同时打印 Markdown 分节表格")
    args = parser.parse_args(argv)

    payload = fetch_plaza(args.url)
    rows = build_rows(payload)
    summary = group_summary(payload)
    print_summary(payload, rows)

    if args.md:
        print()
        for item in summary:
            names = [row["model"] for row in rows if row["group"] == item["group"]]
            print("### `{0}`（{1}x，{2} 个）".format(item["group"], item["multiplier"], len(names)))
            print("、".join("`{0}`".format(name) for name in names))
            print()

    if args.write:
        target = args.out or (DOCS / "模型广场清单-2026-10-25.xlsx")
        write_xlsx(
            rows,
            summary,
            target,
            args.url,
            payload["data"].get("description", ""),
        )
        print("\n已写出：{0}".format(target))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
