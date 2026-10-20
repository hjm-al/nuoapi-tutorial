# v1.0.0 - 33 页多语言接入与排错脚手架

这是 `nuoapi-tutorial` 的首个对外版本。它把 AI 客户端接入、协议路径、报错排错与模型核验整理成可离线试跑、可复核证据的公开工具，而不是一份服务推荐页。

在线文档：<https://nonamelia.github.io/nuoapi-tutorial/>

## 本版重点

- **33 页多语言文档站**：四个语言首页、中文 FAQ 与深度文档、5 个高意图报错页，以及 3 条既有报错页的英/日/繁中翻译。
- **正确的多语言搜索元数据**：每页自指 canonical、真实 hreflang 组、首页 `x-default`、正确 `<html lang>` 与语言切换入口；未翻译页面不伪造对应关系。
- **报错长尾可直接落地**：涵盖 `401 invalid_api_key`、`404 model_not_found`、`400 invalid_request_error`、Cursor / Roo Code Base URL 和 WSL `\r: command not found`。
- **结构化数据**：报错页输出 `TechArticle`，FAQ 输出 `FAQPage`，四语言首页输出 `WebApplication`。
- **先看计划，不花钱**：探针默认 DRY RUN；`--selftest` 只在本机运行，不带 `--run` 时不读取 API Key，也不发出请求。
- **面向 GitHub Pages 的发布链路**：生成 `sitemap.xml`、`robots.txt`、`llms.txt`、Open Graph 和社交预览图，并支持从仓库变量注入 Google/Bing 站点验证码。

## 建议的第一步

```bash
python examples/model_verify.py --selftest
python examples/model_verify.py
```

第二条命令不带 `--run` 时只打印计划。看过将发送的请求与预估用量后，再决定是否调用。

## 报错入口

- [401 invalid_api_key](https://nonamelia.github.io/nuoapi-tutorial/docs/401-invalid-api-key.html)
- [404 model_not_found](https://nonamelia.github.io/nuoapi-tutorial/docs/model_not_found.html)
- [400 invalid_request_error](https://nonamelia.github.io/nuoapi-tutorial/docs/400-invalid-request-error.html)
- [Cursor / Roo Code Base URL](https://nonamelia.github.io/nuoapi-tutorial/docs/Cursor-Roo-Code-Base-URL.html)
- [WSL `\r: command not found`](https://nonamelia.github.io/nuoapi-tutorial/docs/WSL-command-not-found.html)

## 取证窗口

- 协议与端点：**2026-09-21 01:30 UTC**
- 模型广场第一份快照：**2026-10-12**
- 模型广场第二份快照：**2026-10-18**

页面上的模型、分组、价格与倍率会变化，引用时应保留取证窗口，并以实例控制台实时显示为准。

## 验证与边界

- 本地契约测试固定 33 个页面和 33 个唯一 sitemap URL，覆盖 canonical、hreflang 对称性、死链、外链配额、追踪参数、标题摘要宽度和凭据泄露。
- 发布候选已通过 `python -m unittest discover -s tests -v` 与规定的 Ubuntu `act` 契约测试矩阵。
- 本仓库不提供、不代售任何 API 服务，与 NuoAPI 及任何模型厂商无官方关联。
- 示例只含占位符，产生计费的脚本默认 DRY RUN。
- 本项目不包含 UTM、ref、aff 或自建追踪脚本，也不以流量承诺替代可验证的搜索与引荐基线。
