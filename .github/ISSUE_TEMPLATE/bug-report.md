---
name: 报错排查
about: 客户端接不上、返回 4xx/5xx、配置不生效
title: "[排错] "
labels: ["bug"]
---

<!-- 提交前请确认：全文没有真实 API Key、Authorization 头、Cookie、账单截图。 -->

## 已脱敏确认

- [ ] 我确认贴出的内容里**没有真实 API Key**（已替换为 `sk-abc…xyz`）
- [ ] 已删除 `Authorization` 头、Cookie、账单截图与个人路径
- [ ] 已搜索 [FAQ](../../FAQ.md) 的 30 条问答

## 环境

| 项 | 值 |
|---|---|
| 客户端/工具 | （例如 Claude Code v1.x / Codex CLI / Cursor / 自写脚本） |
| 操作系统 | |
| 使用的协议 | Chat Completions / Responses / Messages / Gemini 原生 |

## 现象

**报错原文**（不要转述，直接贴响应体，Key 已脱敏）：

```
```

## 已排除

- [ ] Base URL 是否填对（根地址 vs `/v1`，见 [协议科普](../../docs/AI模型API协议科普-2026-10-12.md)）
- [ ] 模型名是否从当前账户列表逐字符复制
- [ ] Key 所属分组是否包含该模型
- [ ] 换一个模型是否同样失败

## 上下文

- 取证窗口（日期）：
- 是否稳定复现：
- 相关配置片段（已脱敏）： 
