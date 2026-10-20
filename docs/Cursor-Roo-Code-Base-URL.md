<!-- seo-meta
  title: Cursor / Roo Code Base URL：模型无法识别怎么填
  description: Cursor 与 Roo Code 接 OpenAI 兼容网关时，Base URL 指向 /v1，模型 ID 从当前分组清单复制；先验证清单，避免硬编码旧模型名。
-->

# Cursor / Roo Code：Base URL 与模型 ID 怎么填

> **法律与第三方商标免责声明**
>
> 1. 本文是独立开发者维护的配置说明，与 Cursor、Roo Code、OpenAI 或其他模型厂商不存在官方关联、投资、赞助或合作关系。文中商标仅用于说明兼容性。
> 2. 本仓库不提供、不代售任何 API 服务或充值通道。
> 3. 使用第三方服务前，请自行核对服务条款、隐私政策、价格和可用性。

地址夹具是 [`nuoapi.net`](https://nuoapi.net)，当前模型 ID 与分组以[模型广场](https://nuoapi.net/model-plaza)和控制台实时显示为准。

## 症状

配置后出现“模型无法识别”“模型不存在”“请求失败”或所有模型都显示不可用，常见原因是：

- Base URL 填了完整路径，或重复拼接 `/v1`。
- Provider 选成内置官方服务，而不是 OpenAI Compatible。
- 模型 ID 来自旧截图或示例，当前 Key 的分组并不包含它。

## 单一解法

Cursor 和 Roo Code 都按 OpenAI 兼容入口配置：Base URL 使用 `https://nuoapi.net/v1`，模型 ID 从当前分组逐字符复制。不要硬编码本文写作窗口里的旧模型名。

Cursor：

1. 打开 `Settings` → `Models`。
2. 启用 OpenAI API Key / Override Base URL。
3. Base URL 填 `https://nuoapi.net/v1`。
4. 添加模型时粘贴当前清单中的完整 ID。

Roo Code / Cline：

1. Provider 选择 `OpenAI Compatible`。
2. Base URL 填 `https://nuoapi.net/v1`。
3. API Key 和当前分组可用的模型 ID 分开填写。

## 验证步骤

先确认清单中包含目标模型：

```bash
curl -sS https://nuoapi.net/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

再发一条最小对话请求。成功后检查控制台是否出现对应时间、模型和调用类型；如果 IDE 有回复但控制台无记录，先检查是否仍在使用内置模型或另一个 Provider。

## 相关深页

- [接入教程 §7.1：Cursor、Roo Code、Cline 与 Continue](接入第三方工具教程-2026-09-26.md#71-cursorroo-codecline-与-continue)
- [FAQ §27：在 Cursor 或 Roo Code 中配置](../FAQ.md#27-如何在-cursor-或-roo-code-cline-中配置-nuoapi)
- [模型列表与排错](模型列表获取与排错-2026-10-18.md)
