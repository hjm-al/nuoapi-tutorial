# 安全策略

## 报告安全问题

- **不要在公开 Issue、PR、讨论或截图里粘贴任何真实 API Key、请求头或账单明细。**
- 请通过 GitHub 仓库的 **Private vulnerability reporting**（仓库页 → Security → Report a vulnerability）私下报告；我们会在确认后跟进修复与披露。
- 本项目为独立维护的研究/脚手架项目，**没有奖金（no bounty）计划**，但会在致谢中记录负责任的报告（经你同意后）。

## 你的 Key 一旦疑似泄露（处置顺序不能反）

1. **立刻在中转站控制台撤销/作废该 Key 并重建**——只删除本地文件不算处置，Key 在撤销前始终有效。
2. 检查控制台调用记录：泄露时间窗之后是否出现非本人请求、异常模型或异常用量。
3. 轮换所有存过该 Key 的位置：CI Secrets、环境变量、客户端配置文件、共享脚本。
4. 复盘泄露面：截图、shell history、公开 Issue、前端代码、日志聚合、共享屏幕录像都可能是出口。

## 本仓库的凭据设计

- 仓库内只允许 `*.example` 占位文件，占位符统一为 `YOUR_NUOAPI_API_KEY` 一类不含真实凭据的字符串。
- 真实凭据文件（`.env`、`auth.json`、`hermes.yaml`、`openclaw.json`、证据目录 `evidence/`、产物目录 `outputs/`）均在 [.gitignore](.gitignore) 中排除。
- CI 会运行凭据扫描契约测试（`tests/test_docs_security_and_credentials.py`），发现未掩码的高熵 `sk-...` 即失败。
- 所有产生计费请求的脚本默认 **DRY RUN**，Key 只从环境变量读取，输出与证据落盘前自动掩码。

## 范围说明

本仓库**不提供、不代售任何 API 服务**。`nuoapi.net` 等第三方中转站自身的安全问题（账号体系、数据留存、上游风控）不在本项目处置范围，请向对应服务方报告。
