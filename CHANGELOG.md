# 变更记录

本项目按窗口迭代：每次对外数据变化都带**取证窗口日期**，因为中转站的分组、倍率与在架模型随时会变，不带日期的结论一律不可引用。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

## [1.0.0] - 2026-10-18

首个对外版本。取证窗口：**2026-09-21 01:30 UTC**（协议与端点）、**2026-10-12**（模型广场第一份快照）、**2026-10-18**（模型广场第二份快照）。

### 新增

- **多页文档站**：`h5/build_site.py` 把 README / FAQ / examples / `docs/*.md` 各构建成独立页面，生成 `sitemap.xml`、`robots.txt`、`canonical`、Open Graph 与 `FAQPage` 结构化数据；`h5/theme.py` 与单文件页共用样式，两套产物外观不漂移。
- **文档级 SEO 元数据**：Markdown 头部可用 `<!-- seo-meta -->` 注释声明 `title` / `description`，构建器据此生成搜索结果里显示的标题与摘要。
- **社交预览图**：`docs/og-image.png`（1200×630），构建时拷进站点根目录，配合 `summary_large_image` 卡片。
- **Pages 自动部署**：`.github/workflows/pages.yml`，push 到 `main` 即构建并部署，`SITE_URL` 可用仓库变量覆盖。
- **协议科普**：`docs/AI模型API协议科普-2026-10-12.md`，四种协议面孔的报文差异与地址拼接规则。
- **模型广场清单（两份窗口）**：`docs/模型广场清单-2026-10-12.md`（13 分组 / 145 行，含逐行实付与官方价）与 `docs/模型广场清单-2026-10-18.md`（14 分组 / 144 行，按分组列全部可用模型），各配 `xlsx` 明细。
- **接入教程重构**：`docs/接入第三方工具教程-2026-09-26.md` 改为按工具类型组织，覆盖 21 类工具，并明确标注哪些接不了中转站。
- **VS Code 智能体模板**：`examples/vscode-chatLanguageModels.json.example`。

### 变更

- 对外链接统一使用规范页，不再携带站内自用的 `?embedded=1` 参数。
- 页脚与正文的实例链接只做"实例/地址夹具"式说明，不写推荐措辞。

### 契约测试

- 新增 `tests/test_site_build.py`：页面数、sitemap 条目、站内死链、canonical、`FAQPage` 可解析、Pages workflow 形态、`h5/index.html` 未过期，以及外链配额（首页 ≤3、子页 ≤2）、追踪参数禁用、标题/摘要显示宽度、FAQ 标题须含报错原文。

### 说明

- 本仓库**不提供、不代售任何 API 服务**，与 NuoAPI 及任何模型厂商无官方关联。
- 所有示例只含占位符；产生计费的脚本默认 DRY RUN。
- 页面上的价格、倍率与模型清单属**页面声明（B 级证据）**，不代表调用结果或结算价。
