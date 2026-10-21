<!-- seo-meta
  title: NuoAPI 接入脚手架：Codex / Claude Code / Gemini 配置与防掺水
  description: 四种协议（Chat Completions、Responses、Messages、Gemini REST）怎么选、16+ 客户端怎么接、模型真伪怎么验，附可直接跑的探针与一键配置脚本。
-->

# [NuoAPI](https://nuoapi.net/model-plaza) 接入脚手架与防掺水取证工具箱

> **法律与第三方商标免责声明**
>
> 1. 本项目是独立开发者维护的技术研究、配置脚手架与诊断测试套件，**本仓库本身不提供、不代售任何 API 服务**，与 OpenAI、Anthropic、Google、xAI、ByteDance（字节跳动）、DeepSeek、MiniMax 等厂商不存在官方关联、投资、赞助或合作关系。
> 2. 文中 "OpenAI"、"Codex"、"Claude"、"Gemini"、"Grok" 等名称与商标归各自厂商所有，提及它们仅为描述协议兼容性、格式转换与技术指引之必要用途。
> 3. 所有示例只含占位符（`YOUR_NUOAPI_API_KEY`），不收集任何人的 Key；使用第三方服务前请自行核对其服务条款、隐私政策、价格与可用性。

[![契约测试](https://github.com/hjm-al/nuoapi-tutorial/actions/workflows/ci.yml/badge.svg)](https://github.com/hjm-al/nuoapi-tutorial/actions/workflows/ci.yml)
[![GitHub Pages](https://img.shields.io/badge/docs-GitHub%20Pages-2563eb)](https://hjm-al.github.io/nuoapi-tutorial/)
[![许可证: MIT](https://img.shields.io/badge/license-MIT-2ea44f)](LICENSE)

在线文档：<https://hjm-al.github.io/nuoapi-tutorial/> · 仓库：<https://github.com/hjm-al/nuoapi-tutorial> · 语言：[简体中文](README.md) / [English](README.en.md) / [日本語](README.ja.md) / [Español](README.es.md) / [繁體中文](README.zh-Hant.md)

一套面向**买方视角**的开源工具：把各类 AI 客户端/CLI/IDE 插件接入第三方 AI 中转站（网关）。如果正在判断 AI 中转站是否换模型、检查模型真伪，先看[模型真伪与防掺水方法学](docs/MODEL_VERIFICATION_METHODS.md)，再用可辩护的证据回答一个问题——**"我付费调用的，是不是它声称的那个模型？"**

### 多语言核验入口

- [English：LLM Gateway Checklist](docs/llm-gateway-checklist.en.md)：模型一致性、数据驻留、BYOK、审计与故障转移。
- [日本語：最低チャージと料金](docs/minimum-charge-and-pricing.ja.md)：最低充值、额度换算、公开价与实际支付价。
- [Español：每百万 Token 价格](docs/cost-per-1m-tokens.es.md)：输入、输出、缓存、长上下文与总成本模拟。

## 常见问题速查

- [Gemini CLI 报 `platform is not gemini`](docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.md)
- [Codex 一直 Reconnecting](docs/Codex-一直Reconnecting-2026-10-18.md)
- [Claude Code 不要加 `/v1`](docs/Claude-Code-不要加v1-2026-10-18.md)
- [`401 invalid_api_key`](docs/401-invalid-api-key.md)
- [`400 invalid_request_error`](docs/400-invalid-request-error.md)
- [`404 model_not_found`](docs/model_not_found.md)

## 先看计划，不花钱

接入和核对都可以先在本地看一遍将要发生什么，再决定要不要发出会计费的请求。

1. **怎么接**。Codex、Claude Code、Gemini CLI 的 Base URL 不是同一段，配错时常见的是 404，或者连上了但协议不对。
2. **是不是声称的那个模型**。探针给出的是匹配、不匹配或证据不足，对应的是当场能看到的字段和分布，不是一个总分。
3. **先看计划**。下面两条命令不读取 API Key，也不发出请求。

```bash
python examples/model_verify.py --selftest
python examples/model_verify.py
```

`--selftest` 在本机核对探针自己的统计口径，不联网。第二条不带 `--run` 时，只打印将要发出的请求和预估用量。看过计划之后，再决定要不要加 `--run`。

如果已经有一把测试 Key，只想核对模型名是否出现在当前分组里，可以用清单请求。不加 `--run` 时同样只打印计划：

```bash
python examples/evidence_capture.py --probe models
```

加上 `--run` 之后，这条是 `GET /v1/models`，不产生 token 费用。客户端配置可以改用 [`examples/quick_setup.ps1`](examples/quick_setup.ps1) 或 [`quick_setup.sh`](examples/quick_setup.sh)，已有文件会先备份。

## 交给助手

这些步骤也可以交给当前的编程助手。说明写在 `skills/nuoapi-setup/SKILL.md`，只在你提出来的时候使用。助手会先跑不带 `--run` 的探针，并把脚本印出的结论转述给你。

### 会不会把 API Key 传走？

示例和脚本都在你自己的电脑上运行。Key 来自环境变量，或来自你当时粘贴的内容；这个仓库不接收、也不保存它。打印出来的 Key 会打码。真正探测时，更稳妥的是单独建一把用完就删的测试 Key。

### 不加 `--run` 会花钱吗？

默认不会。`model_verify.py` 和 `evidence_capture.py` 不加 `--run` 时只打印计划。加上之后，`--probe models` 仍是一次清单请求，不计 token；对话探针才会产生费用，记在你自己的 Key 上。

### 结果怎么读？

探针给出三种说法：匹配、不匹配、证据不足。响应快慢，以及模型自己怎么称呼自己，只作记录，不单独形成结论。样本不够或请求失败时，记为证据不足，不能据此说成匹配。

本文以网关 `https://nuoapi.net`（[模型广场](https://nuoapi.net/model-plaza)可按「分组」筛选查看某组可用模型与倍率）为实例。模型名、分组、价格与渠道状态随时变化，**一切以模型广场和控制台实时显示为准**；文中标注取证窗口的结论只代表该时间点的观察。

---

## 目录

1. [先看计划，不花钱](#先看计划不花钱)
2. [交给助手](#交给助手)
3. [仓库里有什么](#仓库里有什么)
4. [先认清四种协议面孔](#先认清四种协议面孔)
5. [三分钟快速开始](#三分钟快速开始)
6. [各客户端/CLI 接入要点](#各客户端cli-接入要点)
7. [多语言调用样例与四协议最小示例](#多语言调用样例与四协议最小示例)
8. [模型清单与选型（带取证窗口）](#模型清单与选型带取证窗口)
9. [防掺水：模型真伪探针](#防掺水模型真伪探针)
10. [最小验收与静默降级](#最小验收与静默降级)
11. [常见错误与排错](#常见错误与排错)
12. [安全收尾](#安全收尾)
13. [证据纪律](#证据纪律)
14. [许可证](#许可证)

---

## 仓库里有什么

| 路径 | 内容 |
|---|---|
| [`examples/quick_setup.ps1`](examples/quick_setup.ps1) / [`quick_setup.sh`](examples/quick_setup.sh) | Windows / macOS·Linux·WSL 交互式一键配置脚本 |
| [`examples/`](examples/) | 八语言最小调用样例、流式、Responses、Anthropic Messages、Gemini 原生、Function Calling、Embeddings、图片生成；各客户端配置模板（**只有 `*.example` 占位文件**） |
| [`examples/model_verify.py`](examples/model_verify.py) | 三段式真伪探针（A 字段残留 / B 分布指纹 / C 埋针），**默认 DRY RUN 不花钱** |
| [`examples/evidence_capture.py`](examples/evidence_capture.py) | A 级证据采集器：毫秒时间戳 + 全量响应头 + 响应体 SHA-256 落盘，`--probe models` 零计费 |
| [`examples/check_usage.py`](examples/check_usage.py) | `/v1/usage` 只读查询：Content-Type 与多级兜底解析，缺字段记"未知" |
| [`examples/cost_audit.py`](examples/cost_audit.py) | 消费证据包（或两条差分请求）估算系统前缀注入区间与缓存读取占比 |
| [`docs/MODEL_VERIFICATION_METHODS.md`](docs/MODEL_VERIFICATION_METHODS.md) | 防掺水方法学：证据分档、统计口径、假阳性回归 |
| [`docs/TEST_REPORT_SPEC.md`](docs/TEST_REPORT_SPEC.md) | 黑盒测试报告的六模块规范模板 |
| [`docs/AI模型API协议科普-2026-10-12.md`](docs/AI模型API协议科普-2026-10-12.md) | Chat Completions、Responses、Messages、Gemini 原生协议与地址结构 |
| [`docs/模型广场清单-2026-10-18.md`](docs/模型广场清单-2026-10-18.md) | 模型广场当前窗口（10-18）：抄模型名、看分组用这一份 |
| [`docs/模型列表获取与排错-2026-10-18.md`](docs/模型列表获取与排错-2026-10-18.md) | `/v1/models` 的四个坑：分组绑定、字段形状随分组变、`/v1beta/models` 不是能力清单、列表里有≠能调；附解析脚本 |
| [`docs/模型广场清单-2026-10-12.md`](docs/模型广场清单-2026-10-12.md) | 历史窗口（10-12），数字原样保留；不要拿它当现价或抄当前模型名 |
| [`docs/接入第三方工具教程-2026-09-26.md`](docs/接入第三方工具教程-2026-09-26.md) | 按图形客户端、CLI、IDE/智能体、Provider 管理器分类的接入方法；下面三篇是 Codex / Claude Code / Gemini CLI 的症状短页 |
| [`docs/Codex-一直Reconnecting-2026-10-18.md`](docs/Codex-一直Reconnecting-2026-10-18.md) | Codex 一直 `Reconnecting` 或日志出现 `wss://…/v1/responses`：一份配置加彻底重启 |
| [`docs/Claude-Code-不要加v1-2026-10-18.md`](docs/Claude-Code-不要加v1-2026-10-18.md) | Claude Code 返回 `404`：Base URL 用根地址，Key 变量名是 `ANTHROPIC_AUTH_TOKEN` |
| [`docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.md`](docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.md) | Gemini CLI 报 `platform is not gemini`：`GOOGLE_GEMINI_BASE_URL` 只填根地址 |
| [`docs/图片生成实测教程-2026-09-28.md`](docs/图片生成实测教程-2026-09-28.md) | 图片生成接口的窗口化实测记录（含编辑入口是 JSON 而非 multipart 这个跨实现差异） |
| [`docs/图像质量复盘方法-2026-10-18.md`](docs/图像质量复盘方法-2026-10-18.md) | 图像质量复盘：C1–C10 缺陷码、归因到提示词段落、版本哈希登记、对照实验与防退化四条硬约束 |
| [`docs/余额与额度查询-2026-10-06.md`](docs/余额与额度查询-2026-10-06.md) | `/v1/usage` 只读额度查询：多级兜底解析、SPA 假成功防范、取证模板（C 级证据） |
| [`FAQ.md`](FAQ.md) | 30 条常见问题与分层排错 |
| [`h5/`](h5/) | 站点构建：`build_h5.py` 生成移动端单文件页（[`h5/index.html`](h5/index.html)），`build_site.py` 生成本文档的多页静态站并部署到 GitHub Pages；`theme.py` 为两者共用的样式与交互脚本 |
| [`tests/`](tests/) | 文档死链、凭据泄露、站点构建与产物同步的仓库自检 |

## 先认清四种协议面孔

客户端设置里名字再多，本仓库面向通用文本与 Agent 客户端归纳为四种常见报文协议：Chat Completions、Responses、Messages、Gemini 原生。xAI（Grok）、DeepSeek、MiniMax 等模型在许多第三方客户端中也通过现有兼容协议接入，不能只凭厂商名判断协议。**Base URL 是前缀，不是完整请求地址**，客户端通常会继续拼接路径。概念、报文差异和判断方法见[《AI 模型 API 协议科普》](docs/AI模型API协议科普-2026-10-12.md)，下表仅作配置速查。

| 协议面孔 | 实际请求路径 | 客户端 Base URL | 典型客户端 |
|---|---|---|---|
| **Chat Completions** | `/v1/chat/completions` | `https://nuoapi.net/v1` | 绝大多数 `OpenAI Compatible` 工具、IDE 插件、Aider；Grok、DeepSeek、MiniMax 官方接口同形态 |
| **Responses** | `/v1/responses` | `https://nuoapi.net/v1` | Codex CLI / 桌面端（`wire_api = "responses"`，必须关 WebSocket） |
| **Messages** | `/v1/messages` | `https://nuoapi.net`（**根地址，不加 /v1**） | Claude Code、Claude Desktop 第三方推理 |
| **Gemini 原生 REST** | `/v1beta/models/{模型}:generateContent` | REST 填 `https://nuoapi.net/v1beta`；**Gemini CLI 例外**，变量填根地址 | Gemini CLI、脚本直调 |

选错协议的典型症状：路径 404、报文字段 400、连上但流式异常。Gemini CLI 的变量是 `GOOGLE_GEMINI_BASE_URL=https://nuoapi.net`（根地址）+ `GEMINI_API_KEY` + `GEMINI_MODEL`；报 `400 platform is not gemini` 时按[这篇短页](docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.md)改，不要先当成 Key 无效。

## 三分钟快速开始

1. 在 `https://nuoapi.net` 注册并创建一个**专门用于测试**的 API Key。
2. 从模型广场或当前 Key 的 `/v1/models` 复制**精确模型名**，不要凭印象写、不要照抄别的账号。
3. 判断客户端走哪张协议面孔（上表），选对 Base URL。
4. 跑一键脚本（可选），或按下文手动配置。
5. **完全退出并重新打开**客户端，发固定短句 `请只回复：连接成功` 验证。
6. 到控制台调用记录里核对：模型名、时间、扣费是否与刚才一致。

一键脚本（会交互式引导，也可用参数直接指定）：

```powershell
# Windows PowerShell
.\examples\quick_setup.ps1
# 或：.\examples\quick_setup.ps1 -ApiKey "sk-YOUR_NUOAPI_KEY" -Model "MODEL_NAME_FROM_MODEL_PLAZA"
```

```bash
# macOS / Linux / WSL
bash ./examples/quick_setup.sh
```

环境要求：**Python 3.10+**（真伪探针与全部零依赖示例；3 个 OpenAI SDK 示例另需 `pip install openai`）、Windows PowerShell 5.1+ 或任意 POSIX bash。脚本不会内置任何模型名，模型 ID 一律以你当前 Key 的模型广场列表为准。命令行客户端本身（Claude Code / Codex / Gemini CLI）需要先装 Node.js 再用 npm 安装，步骤见[接入教程第 2 节](docs/接入第三方工具教程-2026-09-26.md#2-命令行客户端先安装-nodejs-与-cli)。

## 各客户端/CLI 接入要点

| 客户端 | 协议 / Base URL | 关键点 |
|---|---|---|
| [**Codex CLI / 桌面端**](docs/Codex-一直Reconnecting-2026-10-18.md) | Responses · `https://nuoapi.net/v1` | `~/.codex/config.toml` 里 `wire_api = "responses"`、`supports_websockets = false`；Key 写 `auth.json`；桌面端共享同一配置，改完彻底重启。步骤见[短页](docs/Codex-一直Reconnecting-2026-10-18.md)，总表索引在[第 5.2 节](docs/接入第三方工具教程-2026-09-26.md#52-codex-cli-与其他-responses-cli)，模板 [`examples/codex/`](examples/codex/)，排错见 [FAQ §4](FAQ.md#4-codex-一直显示-reconnecting-或尝试-wssv1responses-怎么办)/[§11](FAQ.md#11-codex-读取不到配置怎么办) |
| [**Claude Code**](docs/Claude-Code-不要加v1-2026-10-18.md) | Messages · `https://nuoapi.net` | `ANTHROPIC_BASE_URL` 用根地址，**严禁加 `/v1`**；Key 变量名是 `ANTHROPIC_AUTH_TOKEN`。步骤见[短页](docs/Claude-Code-不要加v1-2026-10-18.md)，总表索引在[第 5.1 节](docs/接入第三方工具教程-2026-09-26.md#51-claude-code-与-claude-类工具)，模板 [`claude-code.env.example`](examples/claude-code.env.example)，排错见 [FAQ §2](FAQ.md#2-claude-code-的-base-url-要不要加-v1) |
| [**Claude Desktop (Cowork)**](docs/接入第三方工具教程-2026-09-26.md#51-claude-code-与-claude-类工具) | Messages · `https://nuoapi.net` | 登录页开启开发者模式 → Configure third-party inference，只填 Key 和根地址；模板 [`claude_desktop_config.json.example`](examples/claude_desktop_config.json.example)（MCP 配置另见[教程第 8 节](docs/接入第三方工具教程-2026-09-26.md#8-mcp-工具)） |
| [**Gemini CLI**](docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.md) | Gemini · 根地址 | `~/.gemini/.env` 写 `GOOGLE_GEMINI_BASE_URL=https://nuoapi.net`，不加 `/v1beta`。步骤见[短页](docs/Gemini-CLI-platform-is-not-gemini-2026-10-18.md)，总表索引在[第 5.3 节](docs/接入第三方工具教程-2026-09-26.md#53-gemini-cli)，协议说明见[协议科普第 6 节](docs/AI模型API协议科普-2026-10-12.md#6-gemini-原生协议)，模板 [`gemini.env.example`](examples/gemini.env.example)，排错见 [FAQ §9](FAQ.md#9-gemini-cli-配置后没有响应怎么办) |
| [**Cursor / Roo / Cline / Continue / Aider / OpenCode / Cherry**](docs/接入第三方工具教程-2026-09-26.md#71-cursorroo-codecline-与-continue) | Chat Completions · `/v1` | Provider 选 `OpenAI Compatible`，四字段照填；IDE 插件见[教程第 7.1 节](docs/接入第三方工具教程-2026-09-26.md#71-cursorroo-codecline-与-continue)、通用图形客户端见[第 4 节](docs/接入第三方工具教程-2026-09-26.md#4-图形客户端)，排错见 [FAQ §27](FAQ.md#27-如何在-cursor-或-roo-code-cline-中配置-nuoapi)；模板 [`opencode.json.example`](examples/opencode.json.example) |
| [**VS Code 智能体（Copilot Chat / BYOK）**](docs/接入第三方工具教程-2026-09-26.md#72-vs-code-智能体) | Custom Endpoint · 按协议填完整 URL | 不登录 GitHub 也能用（BYOK）；模型选择器齿轮或命令面板运行 `Chat: Manage Language Models` → Add Models → Custom Endpoint，在 `chatLanguageModels.json` 填 `vendor: customendpoint`、`apiType`、完整 `url` 与能力；agent 模式要求模型支持工具调用，BYOK 不驱动补全/语义检索。详见[教程第 7.2 节](docs/接入第三方工具教程-2026-09-26.md#72-vs-code-智能体)、模板 [`vscode-chatLanguageModels.json.example`](examples/vscode-chatLanguageModels.json.example) |
| [**CC Switch**](docs/接入第三方工具教程-2026-09-26.md#6-provider-配置管理器cc-switch) | 按目标工具分 | 图形化读写本机配置文件、不代理流量；安装与"导入到 CCS"一键导入见[教程第 6 节](docs/接入第三方工具教程-2026-09-26.md#6-provider-配置管理器cc-switch)；Claude 模式填根地址，Codex 模式填 `/v1`，切换后重启客户端。导入不生效见 [FAQ §10](FAQ.md#10-cc-switch-导入后没有生效怎么办) |
| [**Hermes（养马）**](examples/README.md#配置示例) | Chat Completions · `/v1` | `~/.hermes/config.yaml` + `.env`，模板 [`hermes.yaml.example`](examples/hermes.yaml.example)、[`hermes.env.example`](examples/hermes.env.example)（[模板说明](examples/README.md#配置示例)）；VPS 常驻可用 [`linux_agent.service.example`](examples/linux_agent.service.example) |
| [**OpenClaw（龙虾）**](examples/README.md#配置示例) | Chat Completions · `/v1` | `~/.openclaw/openclaw.json`，模板 [`openclaw.json.example`](examples/openclaw.json.example)（[模板说明](examples/README.md#配置示例)） |
| [**Trae CN（TRAE 国内版）**](docs/接入第三方工具教程-2026-09-26.md#trae-cntrae-国内版桌面端--traecode) | Chat Completions · `/v1`（也支持 Messages · 根地址） | 设置 → 模型 → 添加模型 → 自定义模型；「完整 URL」开关关掉填基础地址（OpenAI `https://nuoapi.net/v1`、Anthropic 根地址），打开则填整条；模型 ID 照抄，保存后记得切到该模型。详见[IDE 与编程助手](docs/接入第三方工具教程-2026-09-26.md#73-其他-ide-与编程助手)（仅桌面端支持） |
| [**ZCode（智谱 Z.ai）**](docs/接入第三方工具教程-2026-09-26.md#zcode智谱-zai-桌面端) | OpenAI `/v1` 与 Anthropic 根地址均可 | 「Agents 设置 / 模型 → 添加提供商」，自定义 Base URL + Key 后自动拉模型列表；代理项留空=直连、不跟随系统变量。详见[桌面客户端](docs/接入第三方工具教程-2026-09-26.md#41-桌面客户端逐个配置) |
| [**WorkBuddy（腾讯云）**](docs/接入第三方工具教程-2026-09-26.md#workbuddy腾讯云桌面-agent) | Chat Completions · **填完整 URL** | 头像 → 设置 → 模型 → 自定义模型 → Custom，接口地址要填到 `https://nuoapi.net/v1/chat/completions`；模型名不支持别名；也可写 `~/.workbuddy/models.json`（UTF-8 无 BOM）。详见[桌面客户端](docs/接入第三方工具教程-2026-09-26.md#41-桌面客户端逐个配置) |
| [**Marvis（腾讯 AI 管家）**](docs/接入第三方工具教程-2026-09-26.md#marvis腾讯操作系统级-ai-管家) | 行业通用接口（字段以界面为准） | 设置 → 模型管理 → 自定义模型（2026-09-01 上线，配置跨设备同步、走自己账户计费）；前缀/完整 URL 两种填法报 404 就互换。字段级证据不足，详见[桌面客户端](docs/接入第三方工具教程-2026-09-26.md#41-桌面客户端逐个配置) |
| [**Qoder CN / Qoder CLI / 国际版**](docs/接入第三方工具教程-2026-09-26.md#qoder国际版-ide--qoder-cli--qoder-cn) | 按形态分 | **Qoder CN IDE 个人版只有百炼/智谱/Kimi/MiniMax 四家预置、填不了任意网关地址（文档窗口 2026-07）**；Qoder CLI ≥ v1.1.50（CN/国际均可）与国际版 IDE 支持 OpenAI/Anthropic Compatible 自定义端点。详见[IDE 与编程助手](docs/接入第三方工具教程-2026-09-26.md#73-其他-ide-与编程助手) |
| [**dsh（DeepSeek Harness）**](docs/接入第三方工具教程-2026-09-26.md#dshdeepseek-harness) | Chat Completions · `/v1` | `dsh web` → Settings → Models → Add a custom provider，protocol 选 `openai-completions`、Base URL 填 `/v1`；或写 `~/.dsh/settings.yaml` 用 `apiKeyEnv` 引环境变量。详见[命令行 Agent](docs/接入第三方工具教程-2026-09-26.md#55-其他命令行-agent) |
| [**通用图形客户端**](docs/接入第三方工具教程-2026-09-26.md#4-图形客户端) | 按上表对号入座 | 提供方类型选协议项（OpenAI Compatible / Anthropic / Gemini），而不是找站点名；通用填法见[教程第 4 节](docs/接入第三方工具教程-2026-09-26.md#4-图形客户端) |

Claude Code 环境变量（PowerShell）：

```powershell
[Environment]::SetEnvironmentVariable("ANTHROPIC_BASE_URL", "https://nuoapi.net", "User")
[Environment]::SetEnvironmentVariable("ANTHROPIC_AUTH_TOKEN", "YOUR_NUOAPI_API_KEY", "User")
```

不同操作系统、Docker 与 CI 环境的完整接法（`$env:`/`export`/`~/.bashrc`/Secrets 注入、配置文件路径对照）见 [接入教程第 3 节：通用配置载体](docs/接入第三方工具教程-2026-09-26.md#3-通用配置载体)。

## 多语言调用样例与四协议最小示例

在 [`examples/`](examples/) 中：Python、Node.js、Go（零依赖）、Rust、Java 11+、C#、PHP、curl（[`curl.ps1`](examples/curl.ps1) / [`curl.sh`](examples/curl.sh)）都有最小请求；另有 [`openai_stream.py`](examples/openai_stream.py)（SSE 流式）、[`function_calling.py`](examples/function_calling.py)（工具调用）。

四种协议面孔各发一句 `hello` 的最小脚本（先设 `NUOAPI_API_KEY` 和 `NUOAPI_MODEL`；需要 Python 3.10+）：

```powershell
$env:NUOAPI_API_KEY = "YOUR_NUOAPI_API_KEY"
$env:NUOAPI_MODEL   = "MODEL_NAME_FROM_MODEL_PLAZA"
python examples/openai_compatible.py    # Chat Completions（依赖 openai 包：pip install openai）
python examples/openai_responses.py     # OpenAI Responses，Base URL 仍是 /v1（同上依赖）
python examples/anthropic_messages.py   # Anthropic Messages，x-api-key 鉴权（零第三方依赖）
python examples/gemini_native.py        # Gemini 原生 /v1beta generateContent（零第三方依赖）
```

各示例的依赖归属（哪些零依赖、哪些需要 `pip install openai`）见 [examples/README.md](examples/README.md)。

这些最小样例只证明"协议通了"。**HTTP 200 ≠ 高级能力可用**：工具调用、流式、图片、联网、长上下文要分别核对响应字段与实际结果。

## 模型清单与选型（带取证窗口）

优先用当前 Key 拉取自己分组可见的模型，不要抄旧文档：

```bash
curl -s "https://nuoapi.net/v1/models" \
  -H "Authorization: Bearer YOUR_NUOAPI_API_KEY" \
  | python -c "import sys,json;[print(m['id']) for m in json.load(sys.stdin)['data']]"
```

这条路径零成本，但有四个坑（分组绑定、字段形状也随分组变、`/v1beta/models` 不能当能力清单、列表里有不等于能调）。完整版与解析脚本见[《模型列表：怎么拿、怎么看》](docs/模型列表获取与排错-2026-10-18.md)。

选型表是**取证窗口 2026-09-21 前后**的页面快照，倍率与状态仅作方法示范，下单前以模型广场实时页为准（页面计价约定 `1 CNY = 1 USD` 仅为站内换算）。要自己核对“我这个组到底能用哪些模型、倍率多少”，看[模型广场](https://nuoapi.net/model-plaza)：进页后选「分组」标签筛到你的 Key 所在组，再选「倍率」筛选价格档；不想开浏览器就用上面的 `/v1/models` 拉清单。

| 用途假设 | 当时的模型/分组 | 公开倍率 | 可核验说明 |
|---|---|---|---|
| 脚本调用 | `free` 分组 `grok-4.5` | 0.001 | 分组名为 `free`，不据此推断零费用或稳定性 |
| 日常编码 | `gpt-5.6-luna`（Codex Plus） | 0.088 | 需 Codex Plus 分组 Key；未记录性能比较 |
| 复杂长上下文 | `gpt-6-astra` | 0.300 | 观察到网关侧系统前缀注入（约 11–4,114 token，随分组不同），输入成本会被抬高 |
| 大上下文多模态 | `gemini-3.8-flash` | 0.350 | 需 gemini 分组 Key |
| Claude Kiro / Max | Claude Kiro / Max 分组 | 0.13–1.3 | 仅记录页面快照中的分组与倍率范围；未作性能判定 |

> **上表是 09-21 前后的观察，不要当现价用。** 模型广场的分组、倍率与在架模型每天都在变，且页面还提示"登录后可查看你的专属分组与专属倍率"——**公开倍率不等于你的实付价**。当前的完整清单（14 个分组、每个组可用模型全列）见[《模型广场清单（10-18）》](docs/模型广场清单-2026-10-18.md)。

## 防掺水：模型真伪探针

核心原则：**不要问模型"你是谁"**——网关注入的系统前缀让它答什么身份都行，自述只有参考价值。看它难以伪造的东西。方法学全文见 [MODEL_VERIFICATION_METHODS.md](docs/MODEL_VERIFICATION_METHODS.md)，信号分四档：

| 档 | 信号 | 能否定罪 |
|---|---|---|
| A | 协议字段残留（响应 `id` 前缀、`usage` 命名、枚举值、骨架字段、多跳响应头） | 能，成本≈0 |
| B | 输出分布指纹（37 道窄约束探针，闭集题比 JS 散度、开放题比集中度，置换检验 + Holm 校正，≥2 题显著才定罪） | 能，成本约 $0.02–0.10 |
| C | 能力埋针（长上下文暗号、附件真读、工具链/结构输出、不定时复查） | 能证明"承诺的能力没兑现" |
| D | 模型自述、合规话术、首字延迟 | **不能**，只记录不判定 |

用法（[`examples/model_verify.py`](examples/model_verify.py)，711 行，零第三方依赖）：

```bash
# 离线自测：不发任何请求
python examples/model_verify.py --selftest

# DRY RUN：只打印计划与预估用量（默认）
python examples/model_verify.py --endpoint https://nuoapi.net/v1 \
  --claims openai --model MODEL_NAME_FROM_MODEL_PLAZA

# 确认费用后才真正发起计费请求
python examples/model_verify.py --endpoint https://nuoapi.net/v1 \
  --claims openai --model MODEL_NAME_FROM_MODEL_PLAZA --run
```

输出只有三种结论：**匹配 / 不匹配 / 证据不足**。样本不够、分辨率不足时脚本会显式降级，不会谎报"与基线一致"。基线必须同入口、同模型、同协议族；方法学里记录了旧口径（n=5 + 单题定罪）在自比实验中 37 题误判 21–30 题的回归，旧脚本 [`model_authenticity_check.py`](examples/model_authenticity_check.py) 因此只保留作低判别力反例（现已加 `--run` 计费闸门，默认仅警告退出），不再用于下结论。

**C 段自动化边界**：`model_verify.py` 的 C 段目前只实现长上下文针探；附件真读（PDF/图片暗号）、工具链/结构输出、`web_search` 空结果检测仍是 [方法学第四节](docs/MODEL_VERIFICATION_METHODS.md)里的手工方法，不要因为脚本能跑 `--tier A,B,C` 就以为这些能力已被自动覆盖。

**取证与对账配套工具**（均为零第三方依赖、默认 DRY RUN）：[`examples/evidence_capture.py`](examples/evidence_capture.py) 把一次最小请求固化为 A 级证据包（UTC 毫秒时间戳、全量同名响应头、响应体 SHA-256，`--probe models` 零计费）；[`examples/check_usage.py`](examples/check_usage.py) 只读查询 `/v1/usage` 并做 SPA 兜底与多级兜底解析；[`examples/cost_audit.py`](examples/cost_audit.py) 消费证据包（或两条差分请求）估算系统前缀注入量与缓存读取占比。

写正式取证报告时用 [TEST_REPORT_SPEC.md](docs/TEST_REPORT_SPEC.md) 的六模块结构（元数据与证据分级、路由全图、静默降级、真伪测谎、成本与前缀审计、风险台账）。

## 最小验收与静默降级

每个客户端至少做这五步（详见 [接入教程第 10 节「最小验收流程」](docs/接入第三方工具教程-2026-09-26.md#10-最小验收流程)）：

1. 固定短句测活；2. 无持续重连/超时；3. 控制台调用记录与客户端一致（模型名、时间）；4. 再测真实需要的能力（流式/工具/图片）；5. 留存状态码、错误正文、模型名与时间，分享前抹掉 Key。

特别防两类坑：

- **HTTP 200 静默降级**：附件块被悄悄丢弃、联网检索返回空数组但模型照常作答——用暗号（canary）验证指令是否真被执行。
- **计费陷阱**：`cache_read_input_tokens` 等缓存读取项是**收费的**，对账必须算进去；模型广场"列表里有"不代表当前分组真能调通。

## 常见错误与排错

| 现象 | 先查什么 |
|---|---|
| `401` | Key 是否完整、有无空格/换行、是否被撤销、变量名是否用对 |
| `404` / `model not found` | Base URL 的 `/v1` 该加还是该去；模型名是否来自当前 Key 的列表；Codex 是否选错 `wire_api` |
| `400 platform/protocol 不匹配` | 协议面孔与路径错配，回"四种协议面孔"表对照 |
| `403` / `502` | 当前分组与上游账号池状态，留存错误正文 |
| Codex 一直 `Reconnecting` | `supports_websockets = false` 是否保存、是否彻底重启 |
| 改完环境变量不生效 | Windows 用户级变量不会注入已运行进程，新开终端/重启 GUI |
| 客户端有回复但控制台无记录 | 请求可能走了另一个 Provider/官方账户 |

更多见 [FAQ.md](FAQ.md)。

## 安全收尾

- 测试 Key 用完即撤，或限制额度与权限；Key 只放环境变量/工具凭据存储，绝不进 Git、截图、Issue、CI 日志。
- 仓库只提交 `*.example`；真实 `auth.json`、`.env`、`hermes.yaml`、`openclaw.json` 已在 [.gitignore](.gitignore) 中排除。提交前可跑 `python -m unittest discover -s tests` 自检死链与凭据。
- Key 一旦泄露立即作废重建，不要只改本地文件。

## 证据纪律

- 对外表述按 A/B/C 分级：A=原始报文/响应体哈希/毫秒时间戳；B=公开接口、前端 bundle 静态解析、DNS/RDAP；C=多现象推断且明确标注"未单点证实"。
- "实测""已验证"只在有 A/B 级支撑时使用，并带上取证窗口日期。
- 判定只用三态：**匹配 / 不匹配 / 证据不足**。不把"没出现某厂商关键词"写成通过，不把跨协议入口的字段差异当成调包证据。
- 结论被推翻时写明撤回，不删除原始记录。

## 许可证

[MIT](LICENSE)。示例代码可自由使用；使用本工具箱不构成任何投资或购买建议。
