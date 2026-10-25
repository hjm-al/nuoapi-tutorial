<!-- seo-meta
  title: Claude Code 报 404：Base URL 不要加 /v1
  description: Claude Code 报 404 通常不是 Key 失效：ANTHROPIC_BASE_URL 应填站点根地址，不要附加 /v1；确认 ANTHROPIC_AUTH_TOKEN 后重开终端，再用一次最小请求核对成功判据。
-->

# Claude Code 报 404：ANTHROPIC_BASE_URL 不要加 /v1

直接结论：把 `ANTHROPIC_BASE_URL` 设为站点根地址，不要加 `/v1`；Key 放进 `ANTHROPIC_AUTH_TOKEN`，然后新开终端。

> **法律与第三方商标免责声明**
>
> 1. 本文是独立开发者维护的配置说明，与 OpenAI、Anthropic、Google 或其他模型厂商不存在官方关联、投资、赞助或合作关系。文中商标仅用于协议兼容性说明。
> 2. 本仓库不提供、不代售任何 API 服务或充值通道。
> 3. 使用第三方服务前，请自行核对服务条款、隐私政策、价格和可用性。

地址夹具是 [`nuoapi.net`](https://nuoapi.net)。模型名从当前 Key 的列表照抄，页面快照见[模型广场清单（10-18）](模型广场清单-2026-10-18.md)；实时分组见[模型广场](https://nuoapi.net/model-plaza)。

CLI 还没装时，先看[接入教程第 2 节](接入第三方工具教程-2026-09-26.md#2-命令行客户端先安装-nodejs-与-cli)。VS Code / Cursor 插件不读下面这份环境变量，见[接入教程第 5.4 节](接入第三方工具教程-2026-09-26.md#54-claude-code-编辑器插件vs-code--cursor)。

## 30 秒判断

请求返回纯文本 `404 page not found`，而不是 `401`。常见原因是 Base URL 多写了 `/v1`，客户端再拼上 `/v1/messages`，路径对不上。

Key 变量名也容易错：要用 `ANTHROPIC_AUTH_TOKEN`，不是 `ANTHROPIC_API_KEY`。

## 最短修复

**主操作**：把下面两项写进当前终端或系统环境变量，保持 Base URL 末尾没有 `/v1`。

```text
ANTHROPIC_BASE_URL=https://nuoapi.net
ANTHROPIC_AUTH_TOKEN=YOUR_NUOAPI_API_KEY
```

根地址，末尾不要加 `/v1`。当前终端临时生效（PowerShell）：

```powershell
$env:ANTHROPIC_BASE_URL = "https://nuoapi.net"
$env:ANTHROPIC_AUTH_TOKEN = "YOUR_NUOAPI_API_KEY"
```

要写进用户环境、换终端仍在，用系统的环境变量界面或 `setx` 一类入口；已打开的终端不会自动吃到新值。其他系统的写法见[接入教程第 3 节](接入第三方工具教程-2026-09-26.md#3-通用配置载体)。模板：[`../examples/claude-code.env.example`](../examples/claude-code.env.example)。

## 成功判据

新开一个终端，再启动 Claude Code。在旧窗口里 `echo` 到的还是改之前的值。

发一句固定短句，到控制台核对模型名和时间。仍是 404，先核对变量名和有没有多出来的 `/v1`，短答见 [FAQ §2](../FAQ.md#2-claude-code-的-base-url-要不要加-v1)。

## 相关深页

- [Messages 协议为什么由客户端拼接 /v1/messages](AI模型API协议科普-2026-10-12.md#5-messages)
- [Base URL 与完整请求地址怎么区分](AI模型API协议科普-2026-10-12.md#7-base-url-与完整请求地址)
- [404 model_not_found：先核对当前分组的模型 ID](model_not_found.md)
- [Claude Code 根路径专题页](../topics/claude-code.md)
