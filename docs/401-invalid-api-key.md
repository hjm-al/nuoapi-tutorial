<!-- seo-meta
  title: 401 invalid_api_key：API Key 失效怎么排查
  description: 遇到 401 API_KEY_REQUIRED、invalid_api_key 或 Incorrect API key 时，先确认客户端读到的变量位置、空白字符和 Key 状态，再重建测试 Key。
-->

# 401 invalid_api_key：先确认客户端读到哪把 Key

直接结论：先确认当前进程实际读到的 Key 是否存在、变量名是否正确、前后是否带空白；仍失败再撤销旧 Key，换一把低额度测试 Key。

> **法律与第三方商标免责声明**
>
> 1. 本文是独立开发者维护的配置说明，与 OpenAI、Anthropic、Google 或其他模型厂商不存在官方关联、投资、赞助或合作关系。文中商标仅用于说明协议兼容性。
> 2. 本仓库不提供、不代售任何 API 服务或充值通道。
> 3. 使用第三方服务前，请自行核对服务条款、隐私政策、价格和可用性。

地址夹具是 [`nuoapi.net`](https://nuoapi.net)，当前 Key 状态和所属分组以[控制台](https://nuoapi.net/model-plaza)实时显示为准。

## 30 秒判断

不同原文指向不同环节：

- `401 {"code":"API_KEY_REQUIRED"}`：请求没有带凭据。
- `invalid_api_key` 或 `Incorrect API key provided`：客户端带了 Key，但服务端不接受。
- 复制配置后突然变成 401，而旧终端仍正常：新进程读到的变量与你以为的不一致。

不要根据客户端只说“Unauthorized”就反复重装。先保留脱敏后的状态码和错误正文，Key 本身不要贴到聊天或 Issue。

## 最短修复

**主操作**：只检查当前客户端进程读到的 Key 状态，不打印 Key 内容；确认变量与空白后仍失败，再换低额度测试 Key。

只检查当前启动客户端的那个进程实际读到了哪把 Key。先核对变量名、作用域、前后空格和换行；确认无误仍失败时，在控制台撤销旧 Key，创建一把低额度测试 Key，再重新启动客户端。

PowerShell 可以只检查“是否存在”，不打印内容：

```powershell
$key = $env:OPENAI_API_KEY
if ([string]::IsNullOrWhiteSpace($key)) { "missing" } else { "set; length=$($key.Length)" }
```

macOS / Linux 同样只检查长度：

```bash
if [ -z "${OPENAI_API_KEY:-}" ]; then echo missing; else echo "set; length=${#OPENAI_API_KEY}"; fi
```

变量名要按客户端区分。例如 Claude Code 使用 `ANTHROPIC_AUTH_TOKEN`，不是把 Codex 的 `OPENAI_API_KEY` 原样换过去。具体环境变量写法见[接入教程第 3 节](接入第三方工具教程-2026-09-26.md#3-通用配置载体)。

## 成功判据

1. 完全退出客户端，不要只关闭对话窗口。
2. 新开终端，重新执行上面的“是否存在”检查。
3. 用新测试 Key 发起一次最小请求；仍失败就记录状态码、错误正文、客户端版本和请求协议，不要附带完整 Key。
4. 到控制台核对调用记录。如果客户端有回复但后台无记录，说明请求走了另一个 Provider 或官方账户。

## 相关深页

- [FAQ §3：返回 401 Unauthorized 怎么办](../FAQ.md#3-返回-401-unauthorized-怎么办)
- [Claude Code：Base URL 不要加 /v1](Claude-Code-不要加v1-2026-10-18.md)
- [Codex：读取不到配置](../FAQ.md#11-codex-读取不到配置怎么办)
