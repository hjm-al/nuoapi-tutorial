# 变更记录

本项目按窗口迭代：每次对外数据变化都带**取证窗口日期**，因为中转站的分组、倍率与在架模型随时会变，不带日期的结论一律不可引用。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 新增

- 四语言 README 的首标题把 `NuoAPI` 设为指向规范模型广场的真实链接，首屏实例入口可直接点击。
- 四语言 README 在第一步操作前增加本地化的六项报错速查，覆盖 Gemini CLI、Codex、Claude Code、401、400 与 `model_not_found`。
- 新增 `h5/submit_indexnow.py` 与 Pages 部署后通知任务；支持零网络请求的 dry-run、URL 去重与同站过滤，并把 HTTP 状态和 URL 数量写入 Actions Summary。

### 变更

- 中文 README 注册步骤中的自动链接改为行内代码，确保首页正文的真实实例锚点不超过 3 处。
- 索引通知失败只产生警告，不回滚已经完成的 GitHub Pages 部署；IndexNow 提交不代表已被搜索引擎收录。

## [1.0.0] - 2026-10-20

首个对外版本。取证窗口：**2026-09-21 01:30 UTC**（协议与端点）、**2026-10-12**（模型广场第一份快照）、**2026-10-18**（模型广场第二份快照）。

### 新增

- **33 页多语言文档站**：`h5/build_site.py` 把四语言首页、FAQ、examples 与 `docs/*.md` 构建成 33 个独立页面；每页生成自指 `canonical`、正确 `<html lang>`、真实 `hreflang` 组与语言切换入口，首页另带 `x-default`。输出 `sitemap.xml`、`robots.txt`、`llms.txt` 与 Open Graph；`h5/theme.py` 与单文件页共用样式，两套产物外观不漂移。
- **多语言首页与报错页**：新增 `README.en.md`、`README.ja.md`、`README.zh-Hant.md`，并翻译 Gemini CLI、Codex、Claude Code 三条报错短页；完整 FAQ 与深度文档保留中文。
- **五个高意图报错页**：`401 invalid_api_key`、`404 model_not_found`、`400 invalid_request_error`、Cursor / Roo Code Base URL、WSL `\r: command not found`。每题按症状、单一解法、验证与相关深页组织。
- **结构化搜索数据**：报错页输出 `TechArticle`，FAQ 输出 `FAQPage`，四语言首页输出 `WebApplication`；标题与摘要使用 Markdown 内不可见的 `seo-meta`，不改变正文 H1。
- **文档级 SEO 元数据**：Markdown 头部可用 `<!-- seo-meta -->` 注释声明 `title` / `description`，构建器据此生成搜索结果里显示的标题与摘要。
- **社交预览图**：`docs/og-image.png`（1200×630），构建时拷进站点根目录，配合 `summary_large_image` 卡片。
- **Pages 自动部署与站点验证**：`.github/workflows/pages.yml` 在 push 到 `main` 后构建部署；`SITE_URL`、`GOOGLE_SITE_VERIFICATION`、`BING_SITE_VERIFICATION` 可用仓库变量覆盖或注入验证标签。
- **协议科普**：`docs/AI模型API协议科普-2026-10-12.md`，四种协议面孔的报文差异与地址拼接规则。
- **模型广场清单（两份窗口）**：`docs/模型广场清单-2026-10-12.md`（13 分组 / 145 行，含逐行实付与官方价）与 `docs/模型广场清单-2026-10-18.md`（14 分组 / 144 行，按分组列全部可用模型），各配 `xlsx` 明细。
- **接入教程重构**：`docs/接入第三方工具教程-2026-09-26.md` 改为按工具类型组织，覆盖 21 类工具，并明确标注哪些接不了中转站。
- **VS Code 智能体模板**：`examples/vscode-chatLanguageModels.json.example`。
- **不花钱的入口**：README 先给出 `--selftest`、不带 `--run` 的探针与零计费 `/v1/models`，并回答 Key 是否上传、何时计费、三态结论怎么读。
- **助手技能**：`skills/nuoapi-setup/SKILL.md` 提供配置与 DRY RUN 入口；只在用户点名时使用，脚本结论原样转述。

### 变更

- 对外链接统一使用规范页，不再携带站内自用的 `?embedded=1` 参数。
- 页脚与正文的实例链接只做"实例/地址夹具"式说明，不写推荐措辞。
- `docs/模型广场清单-2026-10-12.md` 降为历史窗口；抄模型名改指向 10-18，正文价格表原样保留，不写涨跌。
- 删掉 MiniMax CLI（`mmx-cli`）「不能接中转站」一节和 README 对应行；能接自定义端点的仍是 MiniMax Code（`mcode`）。
- 方法学补上两处容易误判：模型自述发布日证明不了身份；公开谜题答对或答错都不能单独当作降智证据。

### 契约测试

- 固定 33 个页面与 33 个唯一 sitemap URL，核验自指 canonical、`<html lang>`、hreflang 对称性、未翻译页不伪造互链，以及首页 `x-default`。
- 核验 TechArticle / FAQPage / WebApplication 可解析，Google 与 Bing 验证标签受环境变量控制，中文单文件抽屉只列中文 docs。
- 核验站内死链与 HTML 锚点、四语言外链配额（首页 ≤3、子页 ≤2）、UTM/ref/aff 禁用、SEO 标题摘要宽度、凭据泄露与四语言免责声明。

### 说明

- 本仓库**不提供、不代售任何 API 服务**，与 NuoAPI 及任何模型厂商无官方关联。
- 所有示例只含占位符；产生计费的脚本默认 DRY RUN。
- 页面上的价格、倍率与模型清单属**页面声明（B 级证据）**，不代表调用结果或结算价。
