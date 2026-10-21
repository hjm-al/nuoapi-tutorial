<!-- seo-meta
  title: Gemini CLI 报 platform is not gemini：根地址怎么填
  description: Gemini CLI 报 platform is not gemini 时，先核对 GOOGLE_GEMINI_BASE_URL：变量只填根地址，不要加 /v1beta；确认精确模型 ID 后重启验证。
-->

# Gemini CLI：platform is not gemini

直接结论：`GOOGLE_GEMINI_BASE_URL` 只填站点根地址，不要带 `/v1` 或 `/v1beta`；模型 ID 必须从当前分组逐字符复制。

> **法律与第三方商标免责声明**
>
> 1. 本文是独立开发者维护的配置说明，与 OpenAI、Anthropic、Google 或其他模型厂商不存在官方关联、投资、赞助或合作关系。文中商标仅用于协议兼容性说明。
> 2. 本仓库不提供、不代售任何 API 服务或充值通道。
> 3. 使用第三方服务前，请自行核对服务条款、隐私政策、价格和可用性。

地址夹具是 [`nuoapi.net`](https://nuoapi.net)。模型名从当前 Key 的列表照抄，页面快照见[模型广场清单（10-18）](模型广场清单-2026-10-18.md)；实时分组见[模型广场](https://nuoapi.net/model-plaza)。

CLI 还没装时，先看[接入教程第 2 节](接入第三方工具教程-2026-09-26.md#2-命令行客户端先安装-nodejs-与-cli)。协议为什么填根地址、不填 `/v1beta`，见[协议科普第 6 节](AI模型API协议科普-2026-10-12.md#6-gemini-原生协议)。

## 30 秒判断

两条不要混：

- 返回 `400 platform is not gemini`：请求没走 Gemini 这条协议入口，先改地址，不要先当成 Key 无效。
- CLI 没有任何响应，或路径异常：`GOOGLE_GEMINI_BASE_URL` 被写成了 `https://nuoapi.net/v1beta`。这个变量要填根地址，客户端自己再拼 `/v1beta`。

若正文是 `API_KEY_INVALID` 或 `API key not valid`，那是 Key 没被接受，和上面两条不是同一件事。分层排错见 [FAQ §20](../FAQ.md#20-如何按错误层级排查)。

## 最短修复

**主操作**：把 `~/.gemini/.env` 的 Base URL 改为根地址，并保持模型 ID 与当前分组完全一致。

`~/.gemini/.env`：

```env
GOOGLE_GEMINI_BASE_URL=https://nuoapi.net
GEMINI_API_KEY=YOUR_NUOAPI_API_KEY
GEMINI_MODEL=MODEL_NAME_FROM_MODEL_PLAZA
```

不要在 `GOOGLE_GEMINI_BASE_URL` 后面加 `/v1` 或 `/v1beta`。`GEMINI_MODEL` 与模型广场上的名字逐字符一致，包含日期后缀。模板：[`../examples/gemini.env.example`](../examples/gemini.env.example)。

## 成功判据

保存后退出 Gemini CLI，新开终端再启动。发一句固定短句，到控制台核对模型名和时间。

仍无响应时的短答见 [FAQ §9](../FAQ.md#9-gemini-cli-配置后没有响应怎么办)。
