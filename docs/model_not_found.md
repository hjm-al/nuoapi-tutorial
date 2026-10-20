<!-- seo-meta
  title: 404 model_not_found：模型名与分组不一致怎么修
  description: 遇到 model_not_found 时，先核对当前 Key 所属分组、完整模型 ID 和协议路径；不要靠拼音猜模型名，也不要连续试错制造无效调用。
-->

# 404 model_not_found：先核对当前分组的模型 ID

> **法律与第三方商标免责声明**
>
> 1. 本文是独立开发者维护的配置说明，与 OpenAI、Anthropic、Google 或其他模型厂商不存在官方关联、投资、赞助或合作关系。文中商标仅用于说明协议兼容性。
> 2. 本仓库不提供、不代售任何 API 服务或充值通道。
> 3. 使用第三方服务前，请自行核对服务条款、隐私政策、价格和可用性。

地址夹具是 [`nuoapi.net`](https://nuoapi.net)，模型名、分组和渠道状态以[模型广场](https://nuoapi.net/model-plaza)及控制台实时显示为准。

## 症状

`404 model_not_found` 表示请求路径已经到达网关，但当前 Key 所属分组里找不到这个模型 ID。常见写法还有：

- `Model "X" is not supported by any configured account in this group`
- `The model 'X' does not exist or you do not have access to it`

这和 `404 page not found` 不是一类。后者通常表示 Base URL 或协议路径没有挂载；前者先查模型名与分组。

## 单一解法

只使用当前 Key 分组清单里的完整模型 ID。不要根据产品介绍手写名字，也不要用旧截图里的模型名直接替换。

先列出当前 Key 可见的模型：

```bash
curl -sS https://nuoapi.net/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

然后在模型广场选择同一分组，逐字符复制模型 ID。大小写、日期后缀、连字符和供应商前缀都算模型名的一部分。当前窗口的静态清单见[模型广场清单（10-18）](模型广场清单-2026-10-18.md)。

## 验证步骤

1. 确认客户端协议与模型族匹配：OpenAI 兼容、Anthropic Messages 或 Gemini 原生入口不要混用。
2. 把请求缩到最小，只保留模型 ID、一条短消息和必要鉴权。
3. 保留状态码、响应正文、模型 ID、协议和取证窗口，再与控制台调用记录对照。
4. 清单中可见但调用仍返回 403/502 时，按渠道或上游账号状态排查；不要连续请求多个模型“试出来”。

## 相关深页

- [FAQ §5：返回 404 或 model not found](../FAQ.md#5-返回-404-或-model-not-found-怎么办)
- [模型列表：怎么拿、怎么看](../docs/模型列表获取与排错-2026-10-18.md)
- [AI 模型 API 协议科普](AI模型API协议科普-2026-10-12.md)
