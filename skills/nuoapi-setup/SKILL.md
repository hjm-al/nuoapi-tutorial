---
name: nuoapi-setup
description: 配置 Codex、Claude Code、Gemini CLI，并运行不花钱的模型真伪探针。只在用户明确要求接入或自测时使用。
disable-model-invocation: true
---

# 接入脚手架：配置与不花钱的自测

本仓库是配置脚手架和诊断探针，不代售 API，也不给中转站打分或排名。只在用户点名时运行，不要自动套用到每一次对话。

## 什么时候用

用户要接 Codex、Claude Code、Gemini CLI，或要判断「付费调用的是不是声称的那个模型」。

## 先跑这两条

工作目录是仓库根：

```bash
python examples/model_verify.py --selftest
python examples/model_verify.py
python examples/evidence_capture.py --probe models
```

第一条不联网。后两条不带 `--run` 时只打印计划，不产生计费。加上 `--run` 才会使用用户自己的 Key，用完即撤。`--probe models` 是一次清单请求，不计 token。

一键写配置：[`quick_setup.ps1`](../../examples/quick_setup.ps1) 或 [`quick_setup.sh`](../../examples/quick_setup.sh)。

## 报错直接看短页

- Gemini CLI 报 `platform is not gemini`：[短页](../../docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.md)
- Codex 一直 Reconnecting：[短页](../../docs/Codex-一直Reconnecting-2026-10-18.md)
- Claude Code 的 Base URL 加了 `/v1`：[短页](../../docs/Claude-Code-不要加v1-2026-10-18.md)

## 不许做的

- 脚本输出原样给用户。不自己打分，不把三态改成百分制或可信 / 存疑 / 不可信。
- 不把本文件、探针或答案写进 `AGENTS.md`、`.windsurfrules`、`.clinerules`、`copilot-instructions.md` 这类每次对话都会读的文件。
- 不覆盖用户已有配置。一键脚本会先备份；用户没明确说覆盖，就停下来问。
- 不写匹配 / 不匹配 / 证据不足以外的判词，不写准确率百分比。
- 不新增带 `utm_`、`ref=` 的链接。实例地址只用 `https://nuoapi.net/model-plaza`。
- 不编造模型名、分组或倍率。抄名用 `docs/模型广场清单` 里当前窗口那一份，并说明以控制台为准。
