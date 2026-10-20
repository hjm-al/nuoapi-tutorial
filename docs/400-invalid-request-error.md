<!-- seo-meta
  title: 400 invalid_request_error：先读 message 再改请求
  description: 400 invalid_request_error 不说明具体原因，必须看响应 message：常见是 /v1 路径重复、协议或模型不匹配、缺字段，以及流式参数混用。
-->

# 400 invalid_request_error：先读响应里的 message

> **法律与第三方商标免责声明**
>
> 1. 本文是独立开发者维护的配置说明，与 OpenAI、Anthropic、Google 或其他模型厂商不存在官方关联、投资、赞助或合作关系。文中商标仅用于说明协议兼容性。
> 2. 本仓库不提供、不代售任何 API 服务或充值通道。
> 3. 使用第三方服务前，请自行核对服务条款、隐私政策、价格和可用性。

地址夹具是 [`nuoapi.net`](https://nuoapi.net)，可用模型和分组以[模型广场](https://nuoapi.net/model-plaza)实时显示为准。

## 症状

客户端只显示 `400 Bad Request` 或 `invalid_request_error`，但响应正文通常还有更具体的 `message`。常见形状是：

```json
{"error":{"type":"invalid_request_error","message":"具体原因","code":null}}
```

`invalid_request_error` 是错误类别，不是根因。只改 Key、重启客户端或重复请求，通常不会让 400 消失。

## 单一解法

把请求缩到最小，并只根据 `message` 一次改一个字段。先固定正确的 Base URL 和协议入口，再补模型、必填字段与可选参数。

检查顺序：

1. OpenAI 兼容入口通常是 `https://nuoapi.net/v1`，不要再拼一次 `/v1`。
2. Claude 与 Gemini 原生入口使用各自路径，不要把不同协议字段混在一起。
3. 模型必须支持当前协议和请求能力。
4. Responses 兼容实现可能要求 `instructions` 等字段。
5. `stream=true` 与只适用于非流式的参数不要混用。

完整错误分层见 [FAQ §6](../FAQ.md#6-返回-400-或-invalid_request_error-怎么办)，协议路径见[协议科普](AI模型API协议科普-2026-10-12.md)。

## 验证步骤

1. 保存脱敏后的状态码、响应正文、客户端版本、模型 ID 和协议。
2. 用最小请求复现；仍失败就只保留鉴权、协议要求的必填字段和短输入。
3. 每次只增加或修改一个字段，观察下一次响应的 `message` 是否变化。
4. 对照控制台调用记录，确认请求确实到达预期模型与协议入口。

## 相关深页

- [接入教程第 11 节：常见错误](接入第三方工具教程-2026-09-26.md#11-常见错误)
- [模型列表与协议路径](模型列表获取与排错-2026-10-18.md)
- [FAQ §20：如何按错误层级排查](../FAQ.md#20-如何按错误层级排查)
