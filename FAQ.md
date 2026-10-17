<!-- seo-meta
  title: AI 中转站 FAQ 与报错排查：platform is not gemini、model_not_found
  description: 接入第三方 AI API 中转站时的 30 个真实报错与问法，每条给出原因和可直接照抄的改法，按 Ctrl+F 搜报错原文即可定位。
-->

# NuoAPI FAQ 与排错

接入第三方 AI API 中转站（OpenAI / Claude / Gemini 兼容网关）时的 30 个常见问题，标题都是用户真实会搜的问法。**按 Ctrl+F 直接搜报错原文**（如 `model_not_found`、`platform is not gemini`）即可定位。

## 1. OpenAI 兼容客户端的 Base URL 是什么？

通常使用：

```text
https://nuoapi.net/v1
```

Codex、OpenAI SDK、Cherry Studio、LobeChat 和其他 OpenAI 兼容客户端通常需要 `/v1`。如果客户端要求完整 endpoint，请按客户端文档补充路径。

填错 Base URL 的典型表现：请求落到未注册路径，返回纯文本 `404 page not found`；或客户端直接报连接失败、`fetch failed`。客户端自己会在 Base URL 后面拼接 `/chat/completions` 等路径，所以这里填的是前缀，不是完整请求地址。

## 2. Claude Code 的 Base URL 要不要加 `/v1`？

通常不要加：

```text
https://nuoapi.net
```

同时检查：

```text
ANTHROPIC_BASE_URL=https://nuoapi.net
ANTHROPIC_AUTH_TOKEN=YOUR_NUOAPI_API_KEY
```

修改环境变量后重新打开终端或重启 Claude Code。

误加 `/v1` 时，请求实际落在 `/v1/messages`，常见表现是 404（网关返回纯文本 `404 page not found`），而不是 Key 错误。

## 3. 返回 401 Unauthorized 怎么办？

按顺序检查：

1. API Key 是否复制完整。
2. 是否包含前后空格、换行或引号。
3. Key 是否已撤销、过期或属于另一个账号。
4. 环境变量或配置文件是否被当前客户端读取。
5. 是否把 Claude 的 Token 错放进了 Codex 配置，或反过来。

不同环节返回的原文不一样，可据此判断卡在哪：请求没带凭据时，网关返回 `401 {"code":"API_KEY_REQUIRED"}`；Key 无效时常见 `invalid_api_key` 一类错误码，若上游透传 OpenAI 报错还会看到 `Incorrect API key provided` 字样。

不要把完整 Key 发给他人排查。必要时撤销旧 Key 后创建测试 Key。

## 4. Codex 一直显示 `Reconnecting` 或尝试 `wss://.../v1/responses` 怎么办？

这通常表示客户端先尝试了 WebSocket，而当前接口只需要标准 HTTP。检查 `~/.codex/config.toml` 的 Provider 配置包含：

```toml
base_url = "https://nuoapi.net/v1"
wire_api = "responses"
supports_websockets = false
```

保存后完全退出并重启 Codex。不要只在 `.env` 中添加代理变量，因为那不会必然关闭客户端的 WebSocket 尝试。

排查时对照日志原文：正常情况下日志不应再出现 `wss://nuoapi.net/v1/responses`；若仍有 `WebSocket connection ... failed`、`stream error` 或反复 `connecting to wss://...`，说明 `supports_websockets = false` 没被读到（配置文件路径不对或没彻底重启），回到第 11 节检查配置位置。

## 5. 返回 404 或 model not found 怎么办？

这通常不是余额问题，而是以下字段不匹配：

- 模型名拼写、大小写或后缀。
- API Key 所属分组。
- 当前渠道状态。
- Base URL 协议路径。

注意对照报错原文：网关自身的响应是 `404 model_not_found`（模型不在当前 Key 的分组）；若上游透传 OpenAI 报错，还会看到 `The model 'xxx' does not exist or you do not have access to it` 这类文案，中文客户端可能显示"模型不存在或无访问权限"。两者排法相同。

打开 [模型广场](https://nuoapi.net/model-plaza) 用「分组」筛选到你 Key 所在的组，复制当前账号可见的精确模型名，不要手写猜测。

## 6. 返回 400 或 `invalid_request_error` 怎么办？

先查看响应正文中的具体字段，不要仅根据客户端提示猜原因。这类报错的响应体通常是 `{"error":{"type":"invalid_request_error","message":"...","code":...}}` 的形状（OpenAI 与 Anthropic 协议族都用 `invalid_request_error` 这个 type），客户端界面可能只显示 `400 Bad Request`，真正的原因要看 `message` 原文。常见检查项：

1. Base URL 是否把 `/v1` 重复拼接，或缺少 `/v1`。
2. 模型是否支持当前请求协议（Chat Completions、Responses、Anthropic Messages 等）。
3. 客户端是否发送了服务端要求的字段，例如某些 Responses 兼容实现需要 `instructions`。
4. 是否把流式和非流式参数混用。

如果要反馈问题，请提供脱敏后的状态码、响应正文、客户端版本、模型名和请求协议；不要直接把完整请求头或 API Key 发出来。

## 7. 返回 403、余额不足或模型无权限怎么办？

这通常不是本地安装问题。响应正文里可能出现 `403 Forbidden`、`insufficient balance`（余额不足）、`quota exceeded`（额度超限）、`no permission`（无权限）一类文案，具体字样以实际响应体为准。登录控制台确认余额、Key 所属分组和模型权限；必要时换一个当前分组可见的模型，再用最小 `hello` 请求复现。

## 8. 模型价格如何计算？

模型广场通常按 `$ / 1M token` 展示输入、输出和缓存价格。图片模型按张计费，视频模型按秒计费。长上下文模型可能按不同上下文档位计价，同一模型也可能因分组不同而有不同倍率。

倍率会变：同一模型可能挂在不同倍率组，分组也会上架下架，**任何写进教程的具体倍率都只是那个窗口的值**。当前窗口的完整清单（14 个分组、每个组可用模型全列）见[《模型广场清单（10-18）》](docs/模型广场清单-2026-10-18.md)。

价格不是固定的公共 API 价格表。请以登录后模型广场、订单和用量记录为准。

当前教程沿用页面快照中的 `1 CNY = 1 USD` 展示约定。该约定不代表实际法定汇率。

## 9. Gemini CLI 配置后没有响应怎么办？

检查 `~/.gemini/.env`：

```env
GOOGLE_GEMINI_BASE_URL=https://nuoapi.net
GEMINI_API_KEY=YOUR_NUOAPI_API_KEY
GEMINI_MODEL=MODEL_NAME_FROM_MODEL_PLAZA
```

确认当前分组包含 Gemini 模型，并重新启动 CLI。模型名必须与模型广场完全一致。

两种"有动静但不通"的情况别和"无响应"混淆：报 `400 platform is not gemini` 是协议平台选错（排法见第 20 节）；若上游透传 Google 报错，会看到 `API_KEY_INVALID` 或 `API key not valid` 字样，说明 Key 没被对端接受。另外 Gemini CLI 的 Base URL 填根地址，若误填成 `.../v1beta` 也会异常。

## 10. CC Switch 导入后没有生效怎么办？

1. 在切换 Provider 前确认 Codex、Claude Code、VS Code、Cursor 等客户端已经完全退出。
2. 确认 CC Switch 顶部选中了正确的应用类型，而不是只创建了另一个工具的 Provider。
3. 检查 Claude Code 使用 `https://nuoapi.net`，OpenAI 兼容工具使用 `https://nuoapi.net/v1`。
4. 保存后重新打开客户端；必要时改用手动配置验证 Base URL、Key 和模型。

## 11. Codex 读取不到配置怎么办？

确认文件路径：

- Windows：`%USERPROFILE%\\.codex\\config.toml`
- macOS / Linux / WSL：`~/.codex/config.toml`

同时检查：

- `base_url` 是否为 `https://nuoapi.net/v1`。
- `auth.json` 是否包含 `OPENAI_API_KEY`。
- TOML 和 JSON 是否有语法错误。
- 修改文件后是否重启 Codex 或重新加载 VS Code 窗口。

如果仍然提示 `codex: command not found`，先运行 `codex --version`；这通常是 npm 全局安装路径未加入 PATH，或安装没有成功，不是 API Key 问题。Windows 找不到 `.codex` 时，在资源管理器打开“显示隐藏的项目”，或使用 PowerShell 直接访问 `%USERPROFILE%\\.codex`。

## 12. 客户端能回复，但后台没有调用记录怎么办？

这通常说明客户端仍在使用旧 Provider、官方账号或其他环境变量。退出客户端后检查当前 Provider、配置文件和环境变量，再发送一次唯一的测试消息。只有控制台出现对应记录，才能确认请求命中了 NuoAPI。

## 13. 什么时候使用旧站域名？

旧站 `https://nuoapi.com/docs/` 是教程文档来源，新站 `https://nuoapi.net` 是模型广场、控制台和运营主站。新配置优先使用新站控制台显示的地址；旧文档中的 `.com` 示例不要直接复制到新站账号配置中。

## 14. 网络超时或持续重试怎么办？

先用最小 `hello` 请求测试，再排查本机代理、网络切换和客户端版本。不同客户端的报错原文可以对照：`ETIMEDOUT`、`ECONNRESET`、`socket hang up`、`fetch failed`、`timeout of xxx ms exceeded`、`The operation has timed out`——出现这些字样优先查本机网络与代理，而不是 Key 或模型。若 Codex 特别表现为 WebSocket 重连，按本 FAQ 第 4 节关闭 WebSocket；若仍失败，记录状态码和最后一行错误，不要反复重装客户端。

## 15. 如何安全地提交问题？

提供以下非敏感信息即可：

- 操作系统和客户端版本。
- 使用的模型名和分组名称。
- Base URL 的域名和路径，但不要提供 Token。
- HTTP 状态码和最后一行错误。
- 是否能用最小的 `hello` 请求复现。

提交日志前删除 `Authorization`、`api_key`、`token`、Cookie、邮箱和个人路径。

## 16. NuoAPI 是否是 OpenAI、Anthropic 或 Google 官方服务？

不是。本仓库和 NuoAPI 都是独立第三方内容。OpenAI、Anthropic、Google、xAI、DeepSeek、Alibaba、Moonshot AI 和 MiniMax 等名称仅用于描述兼容的模型或客户端，不表示合作、赞助或官方推荐。

## 17. 应该使用 Chat Completions、Responses 还是 Messages？

按客户端使用的协议选择：普通 OpenAI SDK 通常使用 `/v1/chat/completions`，Codex 通常使用 `/v1/responses`，Claude Code 通常使用 `/v1/messages`。三种入口都曾实测可用，但可用模型仍受 Key 所属分组和上游账号池影响。

## 18. 请求返回 200，为什么能力还是没有生效？

该网关存在静默降级。实测中 PDF 的 `document` 块可能被丢弃，`modalities: ["audio"]` 可能没有 audio 字段，`web_search` 可能执行后返回空结果；`logprobs`、`seed` 和 `n > 1` 也可能被忽略。排查时检查响应中的实际字段，并用带唯一暗号的最小内容探针确认输入确实被处理。

## 19. 模型广场列出了模型，但调用返回 403、502 或 404，怎么办？

模型清单是动态快照，不等于上游账号池始终可用。先用 `GET /v1/models` 确认当前 Key 的清单，再区分错误：`404 model_not_found` 通常是模型不在该分组，`403` 或 `502` 可能是上游账号耗尽或被拒绝。不要为了“试一遍”连续调用多个模型，以免产生无效费用；换当前清单中已确认可用的模型，或稍后重试。

## 20. 如何按错误层级排查？

可以按下面顺序判断：未注册路径通常返回 Gin 的 `404 page not found`；缺少凭据通常是 `401 {"code":"API_KEY_REQUIRED"}`；请求体错误通常是 `400`；Gemini 等平台不匹配可能是 `400 platform is not gemini`；图像模型前缀不符合白名单可能是 `400 requires an image model`；模型不在当前分组通常是 `404 model_not_found`。先确认路径和鉴权，再确认请求体、平台、模型和分组。

## 21. `/v1beta/...:countTokens` 能不能用来免费估算费用？

不要这样使用。实测该路径返回了生成结果并产生计费，动作名中的 `countTokens` 没有兑现“只计数”的语义。成本核对还要查看 `cache_read` 等用量字段，不能只看输入和输出 token。

## 22. 图片生成结果和图像编辑是否适合处理隐私内容？

不建议。实测图片响应 URL 可能指向第三方公开托管，拿到 URL 的人可能可以读取。图像编辑接口的实测 body 也是 JSON 形式，并非官方 multipart 形状；使用前应先确认当前模型和接口返回格式，不要上传密钥、个人证件或其他敏感素材。

## 23. `/v1/models` 和 `/v1beta/models` 应该用哪个？

配置 OpenAI 兼容客户端时使用：

```text
GET https://nuoapi.net/v1/models
Authorization: Bearer YOUR_NUOAPI_API_KEY
```

它按当前 Key 的分组返回模型清单。`/v1beta/models` 是 Gemini 原生接口形状，实测返回的列表不等于网关实际可路由的完整清单，不能用它替代 `/v1/models`。

## 24. `.net` 和 `.com` 的 Key 或余额能通用吗？

不能把它们当成同一实例。实测两套域名的服务实例、Key 识别和模型清单相互独立；新配置优先使用 `https://nuoapi.net` 及控制台当前显示的路径。旧文档中的 `.com` 示例不要直接复制。

## 25. 为不同分组创建多把 Key，是否就能隔离余额？

不要这样假设。报告快照中不同分组的多把 Key 共享统一钱包。预算和实际扣费应以控制台用量记录为准，不能仅按 Key 数量或分组名称估算。

## 26. 如何鉴别中转站是否用低价模型（如豆包 Seed 系列）“偷梁换柱”冒充 GPT-6 或 Claude 5？

在 2026 年的中转市场中，因前沿旗舰模型（如 `gpt-6-astra`、`claude-sonnet-5`、`claude-opus-5`）调用成本高昂，部分中转站会通过 System Prompt 伪装，将后端实际请求偷偷路由到极低成本的国内模型（如字节跳动 `doubao-seed-2-1-turbo`、`deepseek-v4-flash`）以牟取暴利。公开审计中已有约 45.83% 的第三方端点被检出指纹不匹配。

排查按**判别力分档**做，只有前三档能当证据：

1. **协议与字段取证（判别力高、成本≈0）**：读响应 `id` 前缀（`chatcmpl-` / `msg_` 分属不同协议族）、顶层骨架字段（`choices` / `content` / `candidates`）、`usage` 的字段命名、是否透传了非本站体系的计费单位字段、`X-Request-Id` 是否被多跳追加成不同形状（注意：同名响应头要用 `get_all()` 取全量，转成字典只会留下第一个）、标称 JSON 的路径是否返回 HTML。
2. **输出分布指纹（判别力中-高、约 $0.02–0.10）**：37 道“只回一个词/一个数”的探针（含中文题），**闭集题比整份 Jensen-Shannon 散度、开放命名题只比众数集中度**，再与同入口、同模型的历史基线做置换检验 + Holm 校正，且要求 ≥2 道探针同时显著才允许下“不匹配”。合法结论是“统计上不等价”，不是“证明是某模型”。
   > 为什么这么绕：早期版本用“n=5 + 散度>0.35 + 任一道不合格即定罪”，实测发现**同一个模型自采两份分布互比就会误判 21–30/37 道探针“不匹配”**——开放题的 5 次答案天然互不相同，随机性被读成了调包。所以任何 B 段结论都要先确认统计口径达标（脚本 `--selftest` 里带着这条回归）。
3. **能力埋针（判别力中高）**：长上下文针探核对是否真按该长度计费；把暗号写进 PDF/图片上传，看回答里有没有暗号——**状态码 200 不代表附件被读到**。
4. **只能参考、不能判定的三类**：问模型“你是谁”、诱导合规话术、看首字延迟。前两项的答复内容由网关注入的系统前缀决定（实测前缀从约 11 token 到 4,000+ token 不等）；延迟受账号池、缓存与线路支配，一次抖动就能翻转结论。

可直接运行仓库内的 [`examples/model_verify.py`](examples/model_verify.py)：默认 DRY RUN 只打印计划与预估用量（含实际请求端点，端点随 `--claims openai|anthropic|gemini` 切换并同步切换取证口径），加 `--run` 才发起计费请求；先跑 `--selftest` 可在**零请求**的前提下验证统计与取证代码本身。输出三态（匹配 / 不匹配 / 证据不足）。方法学与成本量级见 [`docs/MODEL_VERIFICATION_METHODS.md`](docs/MODEL_VERIFICATION_METHODS.md)。

旧脚本 [`examples/model_authenticity_check.py`](examples/model_authenticity_check.py) 属于第 4 档，默认即产生 3 次计费调用，其“✅ 通过”只表示“没触到关键词”，不要当真伪结论使用。

## 27. 如何在 Cursor 或 Roo Code (Cline) 中配置 NuoAPI？

- **Cursor**：
  进入 `Settings` -> `Models` -> 开启 `OpenAI API Key` -> 点击 `Override Base URL` 填写 `https://nuoapi.net/v1` -> 填入 API Key -> 点击下方 `Add model` 手动输入 `gpt-6-astra` 并保存。
- **Roo Code / Cline**：
  进入插件设置 -> Provider 选择 `OpenAI Compatible` -> Base URL 填 `https://nuoapi.net/v1` -> API Key 粘贴完整 Key -> Model ID 填写 `gpt-6-astra`。

注意：在现代 IDE 中，若遇到模型无法识别，先用 `curl https://nuoapi.net/v1/models` 确认当前 Key 的分组确实包含该模型。

## 28. 遇到 502/403 上游账号池耗尽，如何配置自动化容灾降级？

第三方中转站依赖上游账号池轮询，可能会因官方风控导致某个分组（如 Anthropic 分组）临时熔断。

建议：
1. **多模型降级**：若主力 `gpt-6-astra` 偶尔拥堵，可备用同分组的 `gpt-5.6-luna`；
2. **多 Provider 容灾**：使用 CC Switch 预存 2 套 Provider（NuoAPI + 备用中转/官方 API），故障时一键切换；
3. **网关自动 Failover**：部署 LiteLLM Proxy，利用其 `fallbacks: [{"gpt-6-astra": ["gpt-5.6-luna", "backup-provider"]}]` 实现秒级无感故障转移。

## 29. 在 Linux / WSL 下运行 .sh 脚本提示 Permission denied 或 \r: command not found 怎么办？

这是从 Windows 切换到 Linux 系统的最经典问题：

1. **`bash: ./quick_setup.sh: Permission denied`**：
   - **原因**：Linux 文件系统对未授权的文件默认禁止执行；
   - **解决**：赋予执行权限即可：
     ```bash
     chmod +x ./examples/quick_setup.sh
     ./examples/quick_setup.sh
     ```
   - **免权限方案**：亦可直接用解释器执行：`bash ./examples/quick_setup.sh`。

2. **`\r: command not found` 或 `syntax error near unexpected token`**：
   - **原因**：文件如果在 Windows 下被某些编辑器保存过，换行符会被转为 Windows 的 `CRLF`（含有不可见的 `\r` 回车符），Linux Bash 无法识别；
   - **解决**：在 Linux 终端运行以下命令，一秒剔除 `\r` 回车符：
     ```bash
     sed -i 's/\r$//' ./examples/quick_setup.sh
     ```
   - 本项目发布的代码已默认转换为标准 Linux LF 换行，从 Git 直接拉取或下载即可直接开箱运行。

## 30. 接入时测过了都正常，为什么后面还是会踩坑？该多久复查一次？

三类原因，都不是“再测一次同样的东西”能解决的：

1. **条件触发**：公开审计里出现过“前若干次请求完全正常、之后才开始动手脚”的投递方式（含在工具调用返回值里注入载荷、截取凭据）。验收通过只代表那一批请求干净。
2. **上游账号池会换**：同一模型名背后的账号池、渠道与分组倍率是动态的，昨天能出图不代表今天能出。所以**复查要换信号、不定时抽样**：A 段字段取证可以每次跑（成本≈0），B 段分布指纹在固定基线后按月或每次换分组时比一次（一轮 ≈296 次极短请求，不适合天天跑），C 段能力埋针按月或能力出问题时装上。
3. **账单口径会骗人**：核对成本时必须把缓存读取项（`cached_tokens` / `cache_read_input_tokens`）一起算，只看可见的 `prompt_tokens` 会把网关注入的那段前缀看没。

做法上把它变成习惯：把 `python examples/model_verify.py --tier A --run` 放进每天的定时任务或 CI 步骤（A 段近零成本），B 段只在需要举证或月度复查时跑一轮 `--tier B --run --compare base.json`（≈296 次极短请求，不适合天天跑），C 段按能力问题触发。原始响应体留档，截图不作为证据。




