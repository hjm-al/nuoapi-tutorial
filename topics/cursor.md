<!-- seo-meta
  title: NuoAPI Cursor 接入教程：3分钟配置自定义 API Key
  description: Cursor 自定义 API Key 只改四项：Provider 选 OpenAI Compatible，Base URL 填到 /v1，Key 与模型 ID 分开粘贴。模型 ID 从当前分组复制，不要沿用旧截图。
-->

# Cursor 接入教程：配置自定义 API Key

> **法律与第三方商标免责声明**
>
> 1. 本文是独立开发者维护的配置说明，与 Cursor、OpenAI 或其他模型厂商不存在官方关联、投资、赞助或合作关系。文中商标仅用于说明兼容性。
> 2. 本仓库不提供、不代售任何 API 服务或充值通道。
> 3. 使用第三方服务前，请自行核对服务条款、隐私政策、价格和可用性。

这一页只解决 Cursor 的自定义 API Key。地址夹具是 [`nuoapi.net`](https://nuoapi.net)，当前模型 ID 以[模型广场](https://nuoapi.net/model-plaza)和控制台实时显示为准。

## 症状

Override Base URL 打开后仍提示模型无法识别、模型不存在，或列表里的模型全部不可用。常见原因是 Provider 仍指向内置官方服务、Base URL 多拼或少拼了 `/v1`，以及模型 ID 来自旧截图。

## 单一解法

**主操作**：在 Cursor 里只填下面四项，不要改其他客户端的环境变量。

1. 打开 `Settings` → `Models`。
2. 打开 OpenAI API Key，并启用 Override OpenAI Base URL。
3. Base URL 填 `https://nuoapi.net/v1`。末尾保留这一个 `/v1`，不要再写成 `/v1/chat/completions`。
4. API Key 粘贴当前 Key；添加模型时，从当前分组清单逐字符复制模型 ID。

Provider 若能选协议，选 `OpenAI Compatible`，不要选名为 OpenAI 的内置账号。Roo Code、Cline 也用这四项，但菜单不在 Cursor 里，见[同主题的 Base URL 短页](../docs/Cursor-Roo-Code-Base-URL.md)。

## 验证步骤

先确认当前 Key 的清单里真有这个模型 ID：

```bash
curl -sS https://nuoapi.net/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

再在 Cursor 里发一句固定短句。控制台应出现对应时间、模型 ID 和调用类型。编辑器有回复但控制台没有记录时，先检查是否仍走内置模型。

## 相关深页

- [Cursor / Roo Code：Base URL 与模型 ID](../docs/Cursor-Roo-Code-Base-URL.md)
- [接入教程 §7.1](../docs/接入第三方工具教程-2026-09-26.md#71-cursorroo-codecline-与-continue)
- [FAQ §27](../FAQ.md#27-如何在-cursor-或-roo-code-cline-中配置-nuoapi)
