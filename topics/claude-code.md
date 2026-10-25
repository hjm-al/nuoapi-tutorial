<!-- seo-meta
  title: NuoAPI Claude Code 配置指南：解决 404 与根路径映射
  description: Claude Code 返回 404 page not found 时，ANTHROPIC_BASE_URL 保持站点根路径，不要再加 /v1。Key 写入 ANTHROPIC_AUTH_TOKEN，新开终端后用一次最短请求核对。
-->

# Claude Code 配置指南：解决 404 与根路径映射

直接结论：`ANTHROPIC_BASE_URL` 只填站点根地址。Claude Code 会自己接上 `/v1/messages`；Base URL 里再写 `/v1`，路径就会多一段，返回纯文本 `404 page not found`。

> **法律与第三方商标免责声明**
>
> 1. 本文是独立开发者维护的配置说明，与 Anthropic 或其他模型厂商不存在官方关联、投资、赞助或合作关系。文中商标仅用于协议兼容性说明。
> 2. 本仓库不提供、不代售任何 API 服务或充值通道。
> 3. 使用第三方服务前，请自行核对服务条款、隐私政策、价格和可用性。

地址夹具是 [`nuoapi.net`](https://nuoapi.net)。模型 ID 从当前 Key 的列表照抄，实时分组见[模型广场](https://nuoapi.net/model-plaza)。

## 30 秒判断

响应体是纯文本 `404 page not found`，不是 JSON，也不是 `401`。这是根路径被多加了 `/v1`，不是 Key 失效。

变量名同时要核对：Key 放在 `ANTHROPIC_AUTH_TOKEN`。写成 `ANTHROPIC_API_KEY` 时，Claude Code 读不到这把 Key。

## 最短修复

**主操作**：保持 Base URL 末尾没有 `/v1`，并确认变量名是 `ANTHROPIC_AUTH_TOKEN`。

```text
ANTHROPIC_BASE_URL=https://nuoapi.net
ANTHROPIC_AUTH_TOKEN=YOUR_NUOAPI_API_KEY
```

当前终端临时生效（PowerShell）：

```powershell
$env:ANTHROPIC_BASE_URL = "https://nuoapi.net"
$env:ANTHROPIC_AUTH_TOKEN = "YOUR_NUOAPI_API_KEY"
```

已打开的终端不会自动读到后来写入系统的环境变量。模板在 [`../examples/claude-code.env.example`](../examples/claude-code.env.example)。VS Code / Cursor 里的 Claude Code 插件不读这两行，见[接入教程第 5.4 节](../docs/接入第三方工具教程-2026-09-26.md#54-claude-code-编辑器插件vs-code--cursor)。

## 成功判据

新开一个终端再启动 Claude Code。发一句固定短句，到控制台核对模型名和时间。若仍是 `404 page not found`，只检查有没有多出来的 `/v1` 和变量名；字段级说明见[不要加 /v1 的短页](../docs/Claude-Code-不要加v1-2026-10-18.md)和 [FAQ §2](../FAQ.md#2-claude-code-的-base-url-要不要加-v1)。

## 相关深页

- [Claude Code 报 404：不要加 /v1](../docs/Claude-Code-不要加v1-2026-10-18.md)
- [Base URL 与完整请求地址](../docs/AI模型API协议科普-2026-10-12.md#7-base-url-与完整请求地址)
- [404 model_not_found：先核对模型 ID](../docs/model_not_found.md)
