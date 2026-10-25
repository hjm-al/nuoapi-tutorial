<!-- seo-meta
  title: Codex 一直 Reconnecting：关掉 supports_websockets
  description: Codex 一直 Reconnecting 时，先检查 wss 请求与 supports_websockets 配置：关闭 WebSocket、保存并彻底重启，再用固定短句和日志判断是否恢复。
-->

# Codex 一直 Reconnecting：关闭 supports_websockets

直接结论：把 Codex 的 `wire_api` 设为 `responses`，并把 `supports_websockets` 设为 `false`；保存后必须彻底退出再重启。

> **法律与第三方商标免责声明**
>
> 1. 本文是独立开发者维护的配置说明，与 OpenAI、Anthropic、Google 或其他模型厂商不存在官方关联、投资、赞助或合作关系。文中商标仅用于协议兼容性说明。
> 2. 本仓库不提供、不代售任何 API 服务或充值通道。
> 3. 使用第三方服务前，请自行核对服务条款、隐私政策、价格和可用性。

地址夹具是 [`nuoapi.net`](https://nuoapi.net)。模型名从当前 Key 的列表照抄，页面快照见[模型广场清单（10-18）](模型广场清单-2026-10-18.md)；实时分组见[模型广场](https://nuoapi.net/model-plaza)。

CLI 还没装时，先看[接入教程第 2 节](接入第三方工具教程-2026-09-26.md#2-命令行客户端先安装-nodejs-与-cli)。其他客户端仍留在[接入教程](接入第三方工具教程-2026-09-26.md)。

## 30 秒判断

Codex CLI 或桌面端一直显示 `Reconnecting`，或日志里出现下面任一原文：

- `wss://nuoapi.net/v1/responses`
- `WebSocket connection ... failed`
- `stream error`
- 反复 `connecting to wss://...`

这是客户端先去试 WebSocket。当前要走的是 HTTP Responses，不是另一套协议。只在环境变量里加代理，关不掉这次重试。

## 最短修复

**主操作**：编辑 `~/.codex/config.toml`，保留下面这一份 Provider 配置并保存。

`~/.codex/config.toml`（Windows：`%USERPROFILE%\.codex\config.toml`）：

```toml
model_provider = "nuoapi"
model = "MODEL_NAME_FROM_MODEL_PLAZA"

[model_providers.nuoapi]
name = "nuoapi"
base_url = "https://nuoapi.net/v1"
wire_api = "responses"
requires_openai_auth = true
supports_websockets = false
```

Key 不要写进这个 toml。放到同目录的 `auth.json`：

```json
{
  "OPENAI_API_KEY": "YOUR_NUOAPI_API_KEY"
}
```

`base_url` 只到 `/v1`，不要再拼一次 `/v1` 或 `/responses`。桌面端和 CLI 读的是同一对文件。模板：[`../examples/codex/`](../examples/codex/)。

## 成功判据

保存后完全退出 Codex，再打开。不要只关对话页。

然后发一句固定短句（例如 `请只回复：连接成功`），到控制台核对模型名、时间和是否有这条记录。日志里不应再出现 `wss://nuoapi.net/v1/responses`。

还在重连：多半是改错了文件，或进程还拿着旧配置。路径和 `auth.json` 见 [FAQ §11](../FAQ.md#11-codex-读取不到配置怎么办)，同一症状的短答见 [FAQ §4](../FAQ.md#4-codex-一直显示-reconnecting-或尝试-wssv1responses-怎么办)。

## 相关深页

- [Responses 协议路径与 Base URL](AI模型API协议科普-2026-10-12.md#4-responses)
- [如何读取模型列表并核对当前分组](模型列表获取与排错-2026-10-18.md#1-唯一正确的入口)
- [404 model_not_found：先核对模型 ID](model_not_found.md)
