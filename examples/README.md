<!-- seo-meta
  title: 八语言 OpenAI 兼容 API 调用示例与四协议最小样例
  description: curl、Python、Node、Go、Java、PHP、Rust、C# 的最小请求样例，外加 Responses、Anthropic Messages、Gemini 原生 REST 四种协议对照。
-->

# 配置示例

这些文件只包含占位符，不包含可用凭据。

默认的 OpenAI 示例和 curl 示例只验证最小的 Chat Completions 请求；协议示例另外验证 Responses、Anthropic Messages 和 Gemini 原生 REST 的最小请求。它们都不代表 PDF、音频、联网搜索、视频、Embedding 或其他高级能力可用。高级能力即使返回 HTTP 200，也要检查响应字段是否真的包含预期结果。

使用前：

1. 在 <https://nuoapi.net> 登录并创建 API Key。
2. 将 `YOUR_NUOAPI_API_KEY` 替换为自己的 Key。
3. 从模型广场复制精确的模型名。
4. 不要把替换后的文件提交到公开仓库。

## 依赖归属（运行前看一眼）

| 示例 | 依赖 | 准备动作 |
|---|---|---|
| `anthropic_messages.py`、`gemini_native.py`、`function_calling.py`、`embeddings.py`、`images_generations.py`、`model_verify.py`、`evidence_capture.py`、`check_usage.py`、`cost_audit.py`、`model_authenticity_check.py` | **零第三方依赖**（Python 3.10+ 标准库） | 无 |
| `openai_compatible.py`、`openai_stream.py`、`openai_responses.py` | 官方 Python SDK | `pip install openai` |
| `openai_compatible.mjs` | 官方 Node.js SDK | `npm install openai` |
| `openai_compatible.go` | Go 标准库（零依赖） | 无 |
| `OpenAICompatible.java` | Java 11+ 原生 `HttpClient`（零依赖） | 无 |
| `openai_compatible.cs` | .NET `HttpClient`（零依赖） | 无 |
| `openai_compatible.php` | PHP 原生 cURL 扩展（零 Composer 包） | 无 |
| `openai_compatible.rs` | reqwest + tokio + serde_json | 按文件头部注释准备 Cargo 依赖 |
| `curl.sh` / `curl.ps1` | 系统自带 curl | 无 |

文件说明：

- `quick_setup.ps1`：Windows PowerShell 交互式一键配置脚手架（Codex CLI/桌面端、Claude Code、Claude Desktop Cowork、Gemini CLI、Hermes 养马、OpenClaw 龙虾）。
- `quick_setup.sh`：macOS / Linux / WSL Bash 交互式一键配置脚手架。
- `claude_desktop_config.json.example`：Claude Desktop (Cowork 开发者模式第三方推理及 MCP 工具) 配置模板。
- `hermes.yaml.example`、`hermes.env.example`：Hermes Agent (养马) 模型、工具链与凭据配置模板。
- `openclaw.json.example`：OpenClaw (龙虾) 自主助理标准配置模板。
- `linux_agent.service.example`：Linux Systemd 后台常驻守护进程服务模板（适合 VPS 7x24 小时挂机运行自主智能体）。
- `curl.sh`、`curl.ps1`：curl 请求示例。
- `claude-code.env.example`：Claude Code 环境变量。
- `codex/`：Codex Provider 和 API Key 文件模板。
- `opencode.json.example`：OpenCode 的 OpenAI 兼容 Provider 模板。
- `vscode-chatLanguageModels.json.example`：VS Code 智能体（Copilot Chat / BYOK）Custom Endpoint 配置模板；`apiKey` 用 `${input:...}` 输入变量占位，模型 `url` 填完整请求路径。
- `gemini.env.example`：Gemini CLI 环境变量。
- `openai_compatible.py`：Python OpenAI SDK 最小请求。
- `openai_stream.py`：Python OpenAI SDK 流式 (SSE) 请求。
- `openai_compatible.mjs`：Node.js OpenAI SDK 最小请求。
- `openai_compatible.go`：Go 原生标准库零依赖最小请求。
- `openai_compatible.rs`：Rust reqwest + tokio 最小请求。
- `OpenAICompatible.java`：Java 11+ 原生 HttpClient 零依赖最小请求。
- `openai_compatible.cs`：C# .NET HttpClient 最小请求。
- `openai_compatible.php`：PHP 原生 cURL 零依赖最小请求。
- `openai_responses.py`：Python OpenAI SDK Responses API 请求。
- `function_calling.py`：Python 标准库零依赖实现的 Function Calling (Tool Use) 示例。
- `anthropic_messages.py`：Python 标准库 Anthropic Messages 请求。
- `gemini_native.py`：Python 标准库 Gemini `generateContent` 请求。
- `embeddings.py`：Python 标准库 `/v1/embeddings` 最小请求（默认 DRY RUN）；404 page not found 即路由未挂载。
- `images_generations.py`：Python 标准库图片生成请求（默认 DRY RUN），同时处理 Base64/URL 两种返回，按文件头识别实际格式，PNG 解析实际宽高。
- `evidence_capture.py`：**A 级证据采集器（推荐）**。一次最小请求落盘为证据包：UTC 毫秒时间戳、状态码、全量同名响应头（多跳 `X-Request-Id` 不丢失）、请求体、响应体 SHA-256 与原始响应体；Key 自动掩码，默认 DRY RUN，`--probe models` 为零计费路由取证。
- `check_usage.py`：`GET /v1/usage` 只读查询（默认 DRY RUN）。先校验 Content-Type 防 SPA 假成功，再多级兜底解析 `remaining` / `quota.remaining` / `balance`，缺字段输出"未知"不用 0 填充。
- `cost_audit.py`：账单对账与系统前缀估算（默认 DRY RUN）。离线消费 `evidence_capture.py` 证据包（`--from-bundle`，零新增计费），或实时发短/长两条差分请求；输出缓存读取字段、前缀 token 估算区间（C 级）与倍率口径成本，可另存 CSV。
- `model_authenticity_check.py`：**已降级的 D 档低判别力反例，不要用于真伪结论**——基于模型自述、合规话术诱导与首字延迟的旧测谎脚本，需显式 `--run` 确认才会发起 3 次计费调用，默认仅打印警告并退出 0，其“✅ 通过”只表示“未触发关键词”；保留仅为留存旧口径问题，新排查一律用 `model_verify.py`。
- `model_verify.py`：**三段式模型真伪探针（推荐）**。A 段协议与字段取证（成本≈0，端点随 `--claims` 切换并同步取证口径）、B 段输出分布指纹（37 道探针，闭集题比 Jensen-Shannon 散度、开放题比众数集中度，与基线做置换检验 + Holm 校正，≥2 道显著才定罪）、C 段长上下文埋针（默认不跑）。**默认 DRY RUN，只打印计划与预估用量，加 `--run` 才发起计费请求**；`--selftest` 为离线自测（零请求零计费）。输出三态（匹配 / 不匹配 / 证据不足）。方法学见 [`../docs/MODEL_VERIFICATION_METHODS.md`](../docs/MODEL_VERIFICATION_METHODS.md)。

> `model_authenticity_check.py` 属于低判别力档位（模型自述、合规话术诱导、首字延迟），需显式 `--run` 确认才会发起 3 次计费调用（默认仅警告退出）。它的“✅ 通过”只表示“未触发关键词”，不构成真伪证据；新排查请优先使用 `model_verify.py`。

