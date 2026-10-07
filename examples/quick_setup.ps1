<#
.SYNOPSIS
    NuoAPI 2026 AI 开发者客户端一键交互式配置脚手架 (Windows PowerShell)
.DESCRIPTION
    一键自动配置 Codex CLI & 桌面端、Claude Code、Claude Desktop (Cowork)、
    Gemini CLI、Hermes Agent (养马)、OpenClaw (龙虾) 等开发工具，
    自动关闭 WebSocket 避免重试死循环，备份旧配置，并提供前沿模型测谎校验。
    兼容 Windows PowerShell 5.1+（不使用三元运算符 / ?? / ??= 等 PS7 专属语法）。
#>

param(
    [string]$ApiKey,
    # 不内置任何具体模型名默认值：模型名必须从模型广场 / /v1/models 复制当前 Key 分组可见的精确 ID
    [string]$Model,
    [string]$BaseUrl = "https://nuoapi.net"
)

$ErrorActionPreference = "Stop"

# 脚本所在目录：必须在脚本顶层用 $PSScriptRoot 取值。
# 函数作用域内 $MyInvocation.MyCommand.Path 在 Windows PowerShell 5.1 下为 $null，会导致 Split-Path 崩溃。
$script:ScriptDir = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($script:ScriptDir)) {
    $script:ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
}

# 以无 BOM 的 UTF-8 写文件。
# 注意：PS 5.1 的 Set-Content -Encoding utf8 会写入 EF BB BF BOM，
# 会导致 auth.json 等文件被严格 JSON 解析器拒绝。
function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Content
    )
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

# 覆盖已有配置前统一备份为 "<路径>.bak.<yyyyMMddHHmmss>-<序号>"，同秒内序号递增不覆盖。
function Backup-File {
    param(
        [Parameter(Mandatory = $true)][string]$Path
    )
    if (Test-Path $Path) {
        $stamp = Get-Date -Format "yyyyMMddHHmmss"
        $seq = 1
        $backupPath = "$Path.bak.$stamp-$seq"
        while (Test-Path $backupPath) {
            $seq = $seq + 1
            $backupPath = "$Path.bak.$stamp-$seq"
        }
        Copy-Item $Path $backupPath -Force
        Write-Host "  检测到已有文件，已备份至: $backupPath" -ForegroundColor DarkGray
    }
}

# Key 掩码：长度 >= 10 时输出形如 sk-abc…xyz（sk- 后前 3 字符 + 省略号 + 末 3 字符），否则输出 ***。
# 省略号用 [char]0x2026 运行时拼接，避免脚本文件编码差异导致乱码。
function Get-MaskedKey {
    param(
        [string]$Value
    )
    if ([string]::IsNullOrEmpty($Value) -or $Value.Length -lt 10) {
        return "***"
    }
    $prefix = "sk-"
    if ($Value.StartsWith($prefix)) {
        $front = $Value.Substring($prefix.Length, 3)
    } else {
        $front = $Value.Substring(0, 3)
    }
    $back = $Value.Substring($Value.Length - 3, 3)
    return ($prefix + $front + [char]0x2026 + $back)
}

function Show-Header {
    Clear-Host
    Write-Host "==================================================================" -ForegroundColor Cyan
    Write-Host "  NuoAPI 2026 AI 全栈开发客户端一键配置脚手架 (PowerShell)" -ForegroundColor Cyan
    Write-Host "  网关主地址: $BaseUrl" -ForegroundColor Gray
    Write-Host "  当前选定默认模型: $script:Model" -ForegroundColor DarkGray
    Write-Host "==================================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Ensure-ApiKey {
    if ([string]::IsNullOrWhiteSpace($script:ApiKey)) {
        if (![string]::IsNullOrWhiteSpace($env:NUOAPI_API_KEY)) {
            $script:ApiKey = $env:NUOAPI_API_KEY
            Write-Host "检测到环境变量 NUOAPI_API_KEY，已自动加载。" -ForegroundColor Green
        } else {
            # 安全输入：-AsSecureString 不回显，经 BSTR 取出明文后立即清零非托管缓冲
            $secureKey = Read-Host "请输入你的 NuoAPI API Key (sk-...)" -AsSecureString
            $bstr = [IntPtr]::Zero
            try {
                $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureKey)
                $plainKey = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
                if ([string]::IsNullOrWhiteSpace($plainKey)) {
                    Write-Host "错误: API Key 不能为空！" -ForegroundColor Red
                    return $false
                }
                $script:ApiKey = $plainKey
            } finally {
                if ($bstr -ne [IntPtr]::Zero) {
                    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
                }
            }
        }
    }
    return $true
}

function Ensure-Model {
    if ([string]::IsNullOrWhiteSpace($script:Model)) {
        if (![string]::IsNullOrWhiteSpace($env:NUOAPI_MODEL)) {
            $script:Model = $env:NUOAPI_MODEL
            Write-Host "检测到环境变量 NUOAPI_MODEL，已自动加载。" -ForegroundColor Green
        } else {
            $script:Model = Read-Host "请输入模型广场中当前 Key 分组可见的精确模型 ID（不要照抄其他账号）"
            if ([string]::IsNullOrWhiteSpace($script:Model)) {
                Write-Host "错误: 模型名不能为空（请先在模型广场或 /v1/models 查询后重试）！" -ForegroundColor Red
                return $false
            }
        }
    }
    return $true
}

# 1. Codex CLI & 桌面端
function Setup-Codex {
    Write-Host "`n[1/7] 开始配置 OpenAI Codex (CLI 与 桌面端共享底层配置)..." -ForegroundColor Yellow
    $codexDir = Join-Path $env:USERPROFILE ".codex"
    if (!(Test-Path $codexDir)) {
        New-Item -ItemType Directory -Path $codexDir -Force | Out-Null
        Write-Host "  创建目录: $codexDir" -ForegroundColor Gray
    }

    # 1. 备份旧 config.toml
    $configFile = Join-Path $codexDir "config.toml"
    Backup-File -Path $configFile

    # 2. 写入正确关闭 WebSocket 的 config.toml
    $configContent = @"
model_provider = "nuoapi"
model = "$script:Model"
model_reasoning_effort = "high"
network_access = "enabled"

[model_providers.nuoapi]
name = "nuoapi"
base_url = "$script:BaseUrl/v1"
wire_api = "responses"
requires_openai_auth = true
# 关键防护：关闭无效的 WebSocket 握手，杜绝终端无限 Reconnecting 卡死
supports_websockets = false
"@
    Write-Utf8NoBom -Path $configFile -Content $configContent
    Write-Host "  已写入: $configFile (已强制 supports_websockets = false)" -ForegroundColor Green

    # 3. 写入 auth.json（覆盖前同样备份）
    $authFile = Join-Path $codexDir "auth.json"
    Backup-File -Path $authFile
    $authContent = @{ OPENAI_API_KEY = $script:ApiKey } | ConvertTo-Json
    Write-Utf8NoBom -Path $authFile -Content $authContent
    Write-Host "  已写入: $authFile" -ForegroundColor Green

    Write-Host "  Codex 配置成功！" -ForegroundColor Cyan
    Write-Host "  - CLI 使用: 直接在项目终端中执行 'codex' 或 'codex --yolo'" -ForegroundColor Gray
    Write-Host "  - 桌面端使用: 启动 Codex 桌面版，将自动读取此配置（若在 CC-Switch 切换需重启桌面端）" -ForegroundColor Gray
}

# 2. Claude Code CLI
function Setup-ClaudeCode {
    Write-Host "`n[2/7] 开始配置 Claude Code CLI 环境变量..." -ForegroundColor Yellow

    # 设置当前会话
    $env:ANTHROPIC_BASE_URL = $script:BaseUrl
    $env:ANTHROPIC_AUTH_TOKEN = $script:ApiKey
    $env:ANTHROPIC_MODEL = $script:Model

    # 写入用户级环境变量（持久化）
    [Environment]::SetEnvironmentVariable("ANTHROPIC_BASE_URL", $script:BaseUrl, "User")
    [Environment]::SetEnvironmentVariable("ANTHROPIC_AUTH_TOKEN", $script:ApiKey, "User")
    [Environment]::SetEnvironmentVariable("ANTHROPIC_MODEL", $script:Model, "User")

    Write-Host "  当前终端环境变量已注入。" -ForegroundColor Green
    Write-Host "  用户系统环境变量已持久化保存 (ANTHROPIC_BASE_URL=$script:BaseUrl)" -ForegroundColor Green
    Write-Host "  关键避坑提醒：Claude Code 的 Base URL 严禁加 /v1，当前已正确设置为站点根地址。" -ForegroundColor Yellow
    Write-Host "  新开终端执行 'claude' 或 'claude --dangerously-skip-permissions' 即可体验。" -ForegroundColor Cyan
}

# 3. Claude Desktop / Cowork
function Setup-ClaudeDesktop {
    Write-Host "`n[3/7] 开始配置 Claude Desktop (Cowork 模式 / 开发者模式第三方推理)..." -ForegroundColor Yellow
    $claudeAppDir = Join-Path $env:APPDATA "Claude"
    if (!(Test-Path $claudeAppDir)) {
        New-Item -ItemType Directory -Path $claudeAppDir -Force | Out-Null
    }

    $claudeConfig = Join-Path $claudeAppDir "claude_desktop_config.json"
    Backup-File -Path $claudeConfig

    # 预写入基础第三方推理结构
    $desktopConfigObj = @{
        inference = @{
            provider = "third_party"
            base_url = $script:BaseUrl
            api_key = $script:ApiKey
        }
    }
    $desktopJson = $desktopConfigObj | ConvertTo-Json -Depth 5
    Write-Utf8NoBom -Path $claudeConfig -Content $desktopJson
    Write-Host "  已写入基础桌面端配置文件: $claudeConfig" -ForegroundColor Green

    $maskedKey = Get-MaskedKey -Value $script:ApiKey
    Write-Host "`n  【Claude Desktop 图形界面开发者模式启用步骤】:" -ForegroundColor Cyan
    Write-Host "  1. 打开 Claude Desktop 应用，切换到 Cowork 模式（若已登录个人账号，请先退出并停留在登录页）；" -ForegroundColor White
    Write-Host "  2. 点击左上角菜单 ☰ -> Help -> Troubleshooting -> Enable Developer Mode；" -ForegroundColor White
    Write-Host "  3. 顶栏出现 Developer 菜单 -> 点击 Developer -> Configure third-party inference；" -ForegroundColor White
    Write-Host "  4. 弹窗中填入以下两项：" -ForegroundColor White
    Write-Host "     - API Key : $maskedKey" -ForegroundColor Yellow
    Write-Host "       请填写你刚才输入的同一把 Key（不再回显）" -ForegroundColor Yellow
    Write-Host "     - Base URL: $script:BaseUrl" -ForegroundColor Yellow
    Write-Host "  5. 点击保存后发送「你好」测试连通性！" -ForegroundColor Green
}

# 4. Gemini CLI
function Setup-GeminiCLI {
    Write-Host "`n[4/7] 开始配置 Gemini CLI..." -ForegroundColor Yellow
    $geminiDir = Join-Path $env:USERPROFILE ".gemini"
    if (!(Test-Path $geminiDir)) {
        New-Item -ItemType Directory -Path $geminiDir -Force | Out-Null
    }
    $envFile = Join-Path $geminiDir ".env"
    Backup-File -Path $envFile
    $envContent = @"
GOOGLE_GEMINI_BASE_URL=$script:BaseUrl
GEMINI_API_KEY=$script:ApiKey
GEMINI_MODEL=$script:Model
"@
    Write-Utf8NoBom -Path $envFile -Content $envContent
    Write-Host "  已写入: $envFile" -ForegroundColor Green
    Write-Host "  Gemini CLI 配置完成！终端运行 'gemini' 即可启动。" -ForegroundColor Cyan
}

# 5. Hermes Agent (养马)
function Setup-HermesAgent {
    Write-Host "`n[5/7] 开始配置 Hermes Agent (养马 · Nous Research 本地自主智能体)..." -ForegroundColor Yellow
    $hermesDir = Join-Path $env:USERPROFILE ".hermes"
    if (!(Test-Path $hermesDir)) {
        New-Item -ItemType Directory -Path $hermesDir -Force | Out-Null
        Write-Host "  创建目录: $hermesDir" -ForegroundColor Gray
    }

    # 1. 写入 config.yaml（覆盖前备份）
    $configFile = Join-Path $hermesDir "config.yaml"
    Backup-File -Path $configFile
    $yamlContent = @"
model:
  provider: custom
  base_url: "$script:BaseUrl/v1"
  default: "$script:Model"
  temperature: 0.7
  timeout: 120

agent:
  persistent_memory: true
  auto_learn_skills: true
  max_iterations: 30

toolsets:
  - filesystem
  - terminal
  - web_search
  - browser
"@
    Write-Utf8NoBom -Path $configFile -Content $yamlContent
    Write-Host "  已写入模型与工具链配置: $configFile" -ForegroundColor Green

    # 2. 写入 .env 凭证（覆盖前备份）
    $envFile = Join-Path $hermesDir ".env"
    Backup-File -Path $envFile
    $envContent = @"
OPENAI_BASE_URL=$script:BaseUrl/v1
OPENAI_API_KEY=$script:ApiKey
HERMES_MODEL=$script:Model
"@
    Write-Utf8NoBom -Path $envFile -Content $envContent
    Write-Host "  已写入环境变量凭证: $envFile" -ForegroundColor Green

    # 检查 Hermes CLI 是否已安装
    $hermesCmd = Get-Command hermes -ErrorAction SilentlyContinue
    if ($hermesCmd) {
        Write-Host "  检测到系统已安装 Hermes Agent: $($hermesCmd.Source)" -ForegroundColor Green
    } else {
        Write-Host "  提示: 本机暂未检测到 hermes 命令。" -ForegroundColor Yellow
        $installNow = Read-Host "  是否立即执行官方一键安装脚本？(y/n)"
        if ($installNow -eq "y" -or $installNow -eq "Y") {
            # 不再 Invoke-Expression 远程脚本直执：先下载到临时文件，展示来源 URL，二次显式 y 确认后才本地执行
            $installUrl = "https://hermes-agent.nousresearch.com/install.ps1"
            $tempScript = Join-Path ([IO.Path]::GetTempPath()) ("hermes-install-" + (Get-Date -Format "yyyyMMddHHmmss") + ".ps1")
            Write-Host "  安装脚本来源 URL: $installUrl" -ForegroundColor Cyan
            $confirmDownload = Read-Host "  将先把脚本下载到本地临时文件并再次向你确认，是否继续？(y/n)"
            if ($confirmDownload -ne "y" -and $confirmDownload -ne "Y") {
                Write-Host "  已取消。后续可手动执行: iex (irm $installUrl)" -ForegroundColor DarkGray
            } else {
                Write-Host "  正在下载到临时文件: $tempScript" -ForegroundColor Cyan
                try {
                    Invoke-WebRequest -Uri $installUrl -UseBasicParsing -OutFile $tempScript
                    Write-Host "  下载完成。来源 URL: $installUrl" -ForegroundColor Gray
                    Write-Host "  本地临时文件: $tempScript （执行前可自行打开检查）" -ForegroundColor Gray
                    $confirmExec = Read-Host "  确认现在执行该本地安装脚本？(y/n)"
                    if ($confirmExec -ne "y" -and $confirmExec -ne "Y") {
                        Write-Host "  已取消执行。" -ForegroundColor DarkGray
                    } else {
                        $global:LASTEXITCODE = 0
                        & $tempScript
                        if ($global:LASTEXITCODE -ne 0) {
                            throw "安装脚本以非零退出码结束: $global:LASTEXITCODE"
                        }
                        Write-Host "  Hermes Agent 安装指令已执行完成！" -ForegroundColor Green
                    }
                } catch {
                    # 失败不得吞掉：明确打印错误并中止本步，不打印成功提示
                    Write-Host "  Hermes Agent 自动安装失败（错误未被忽略，请排查后重试）: $_" -ForegroundColor Red
                    Write-Host "  手动安装备用命令: iex (irm $installUrl)" -ForegroundColor DarkGray
                } finally {
                    if (Test-Path $tempScript) {
                        Remove-Item $tempScript -Force -ErrorAction SilentlyContinue
                    }
                }
            }
        } else {
            Write-Host "  后续安装命令: iex (irm https://hermes-agent.nousresearch.com/install.ps1)" -ForegroundColor DarkGray
        }
    }
    Write-Host "  配置就绪！在终端运行 'hermes' 即可唤醒本地自主智能体。" -ForegroundColor Cyan
}

# 6. OpenClaw (龙虾)
function Setup-OpenClaw {
    Write-Host "`n[6/7] 开始配置 OpenClaw (龙虾 · 本地优先自主助理与自动化平台)..." -ForegroundColor Yellow
    $openclawDir = Join-Path $env:USERPROFILE ".openclaw"
    if (!(Test-Path $openclawDir)) {
        New-Item -ItemType Directory -Path $openclawDir -Force | Out-Null
        Write-Host "  创建目录: $openclawDir" -ForegroundColor Gray
    }

    # 写入 openclaw.json（覆盖前备份）
    $configFile = Join-Path $openclawDir "openclaw.json"
    Backup-File -Path $configFile
    $openclawConfig = @{
        "$schema" = "https://openclaw.ai/schema/config.json"
        version = "2.0"
        models = @{
            providers = @{
                nuoapi = @{
                    baseUrl = "$script:BaseUrl/v1"
                    apiKey = $script:ApiKey
                    apiType = "openai"
                }
            }
            default = $script:Model
        }
        agent = @{
            name = "OpenClaw-Worker"
            workspace = "./workspace"
            permissions = @{
                allowTerminal = $true
                allowFileSystem = $true
                allowBrowser = $true
            }
        }
        ui = @{
            theme = "dark"
            port = 3000
        }
    }
    $jsonContent = $openclawConfig | ConvertTo-Json -Depth 6
    Write-Utf8NoBom -Path $configFile -Content $jsonContent
    Write-Host "  已写入标准配置文件: $configFile" -ForegroundColor Green

    # 检查 openclaw 是否已安装
    $openclawCmd = Get-Command openclaw -ErrorAction SilentlyContinue
    if ($openclawCmd) {
        Write-Host "  检测到系统已安装 OpenClaw: $($openclawCmd.Source)" -ForegroundColor Green
    } else {
        Write-Host "  提示: 本机暂未检测到 openclaw 命令。" -ForegroundColor Yellow
        $installNow = Read-Host "  是否尝试通过 npm 全局安装 openclaw？(y/n)"
        if ($installNow -eq "y" -or $installNow -eq "Y") {
            try {
                npm install -g openclaw@latest
                if ($global:LASTEXITCODE -ne 0) {
                    Write-Host "  npm 安装失败（退出码 $global:LASTEXITCODE），请检查 Node.js 环境。" -ForegroundColor Red
                    Write-Host "  备用官方脚本: curl -fsSL https://openclaw.ai/install.sh | bash (或使用 WSL)" -ForegroundColor DarkGray
                    return
                }
                Write-Host "  OpenClaw npm 安装完成！" -ForegroundColor Green
            } catch {
                Write-Host "  npm 安装失败，请检查 Node.js 环境: $_" -ForegroundColor Red
                Write-Host "  备用官方脚本: curl -fsSL https://openclaw.ai/install.sh | bash (或使用 WSL)" -ForegroundColor DarkGray
                return
            }
        } else {
            Write-Host "  安装命令: npm install -g openclaw@latest" -ForegroundColor DarkGray
        }
    }
    Write-Host "  配置就绪！在终端运行 'openclaw' 或 'openclaw onboard' 启动控制台。" -ForegroundColor Cyan
}

# 探活测试
function Run-HelloTest {
    Write-Host "`n[探活测试] 正在向 NuoAPI 网关发送联通性最小探针..." -ForegroundColor Yellow
    try {
        $body = @{
            model = $script:Model
            messages = @(@{ role = "user"; content = "你好，只回复连接成功四个字" })
            max_tokens = 32
        } | ConvertTo-Json

        $resp = Invoke-RestMethod -Uri "$script:BaseUrl/v1/chat/completions" `
            -Method Post `
            -Headers @{ Authorization = "Bearer $script:ApiKey" } `
            -ContentType "application/json" `
            -Body $body

        $reply = $resp.choices[0].message.content.Trim()
        Write-Host "  网关响应成功！" -ForegroundColor Green
        Write-Host "  模型 [$($script:Model)] 回复: $reply" -ForegroundColor White
    } catch {
        Write-Host "  连接失败: $_" -ForegroundColor Red
        Write-Host "  排查建议：检查 Key 是否正确，或当前 Key 分组是否包含模型 $script:Model" -ForegroundColor Yellow
    }
}

# 真伪探针（model_verify.py：先 DRY RUN，确认后才发 1 次极短计费请求）
function Run-ModelVerify {
    Write-Host "`n[真伪探针] 运行三段式探针 model_verify.py（A 段字段取证，近零成本）..." -ForegroundColor Yellow
    $verifyScript = Join-Path $script:ScriptDir "model_verify.py"
    if (Test-Path $verifyScript) {
        $env:NUOAPI_API_KEY = $script:ApiKey
        $env:NUOAPI_MODEL = $script:Model
        $env:NUOAPI_BASE_URL = "$script:BaseUrl/v1"
        # 先 DRY RUN：只打印计划与预估用量，不产生任何计费请求
        python $verifyScript --tier A
        if ($global:LASTEXITCODE -ne 0) {
            Write-Host "  model_verify.py DRY RUN 失败（退出码 $global:LASTEXITCODE），已中止，不会发起任何计费请求。" -ForegroundColor Red
            return
        }
        $confirmRun = Read-Host "  DRY RUN 已打印计划。确认后才会发起 1 次极短计费请求（A 段），是否继续？(y/n)"
        if ($confirmRun -eq "y" -or $confirmRun -eq "Y") {
            python $verifyScript --tier A --run
            if ($global:LASTEXITCODE -ne 0) {
                Write-Host "  model_verify.py 计费探针执行失败（退出码 $global:LASTEXITCODE）。" -ForegroundColor Red
            }
        } else {
            Write-Host "  已取消计费请求。旧脚本 model_authenticity_check.py 属 D 档低判别力反例，不要再用于下结论。" -ForegroundColor DarkGray
        }
    } else {
        Write-Host "  未找到探针脚本: $verifyScript" -ForegroundColor Red
    }
}

# ----------------- 主程序逻辑 -----------------
Show-Header

if (!(Ensure-ApiKey)) { exit 1 }
if (!(Ensure-Model)) { exit 1 }

# 输入校验：在写任何配置/凭证文件之前拒绝非法值，
# 防止模型名/BaseUrl 中的引号、空白等字符破坏 TOML/YAML/JSON 插值。
if ($script:ApiKey -notmatch '^sk-[A-Za-z0-9._-]{6,}$') {
    Write-Host "错误: API Key 格式不合法（应为 sk- 开头，其后至少 6 个字母/数字或 ._- 字符），已退出且未写入任何文件。" -ForegroundColor Red
    exit 1
}
if ($script:Model -notmatch '^[A-Za-z0-9._:/\-]{1,128}$') {
    Write-Host "错误: 模型名不合法（仅允许 1-128 位字母数字及 ._ : / - 字符，不得含引号或空白），已退出且未写入任何文件。" -ForegroundColor Red
    exit 1
}
if ($script:BaseUrl -notmatch '^https://' -or $script:BaseUrl -match '\s' -or $script:BaseUrl -match '["'']') {
    Write-Host "错误: BaseUrl 必须以 https:// 开头，且不能包含空白或引号字符，已退出且未写入任何文件。" -ForegroundColor Red
    exit 1
}

$maskedKey = Get-MaskedKey -Value $script:ApiKey
Write-Host "已加载 API Key: $maskedKey" -ForegroundColor Green

while ($true) {
    Write-Host "`n请选择需要配置的工具或操作：" -ForegroundColor White
    Write-Host "  [1] 一键配置 Codex (CLI 终端 & 桌面端共享配置 · 强制关闭 WebSocket)" -ForegroundColor White
    Write-Host "  [2] 一键配置 Claude Code CLI (根域名自动对齐与环境变量持久化)" -ForegroundColor White
    Write-Host "  [3] 一键预配 Claude Desktop (Cowork 模式 / 开发者模式第三方推理)" -ForegroundColor White
    Write-Host "  [4] 一键配置 Gemini CLI" -ForegroundColor White
    Write-Host "  [5] 一键配置 Hermes Agent (养马 · Nous Research 本地自主智能体)" -ForegroundColor White
    Write-Host "  [6] 一键配置 OpenClaw (龙虾 · 本地优先自主助理)" -ForegroundColor White
    Write-Host "  [7] 全部一键配置 (Codex + Claude + Gemini + Hermes + OpenClaw)" -ForegroundColor Green
    Write-Host "  [8] 发送最小探活请求 (验证 Key 与模型连通性)" -ForegroundColor White
    Write-Host "  [9] 运行模型真伪探针 model_verify.py (A 段字段取证，先 DRY RUN 后确认计费)" -ForegroundColor Yellow
    Write-Host "  [0] 退出脚本" -ForegroundColor Gray
    Write-Host ""
    $choice = Read-Host "请输入选项数字 [0-9]"

    switch ($choice) {
        "1" { Setup-Codex }
        "2" { Setup-ClaudeCode }
        "3" { Setup-ClaudeDesktop }
        "4" { Setup-GeminiCLI }
        "5" { Setup-HermesAgent }
        "6" { Setup-OpenClaw }
        "7" {
            Setup-Codex
            Setup-ClaudeCode
            Setup-ClaudeDesktop
            Setup-GeminiCLI
            Setup-HermesAgent
            Setup-OpenClaw
            Run-HelloTest
        }
        "8" { Run-HelloTest }
        "9" { Run-ModelVerify }
        "0" { Write-Host "已退出。" -ForegroundColor Gray; break }
        default { Write-Host "无效选项，请重新输入。" -ForegroundColor Red }
    }

    Write-Host ""
    Write-Host "--------------------------------------------------" -ForegroundColor DarkGray
    $again = Read-Host "是否继续执行其他操作？(y/n)"
    if ($again -ne "y" -and $again -ne "Y") {
        Write-Host "配置结束。祝编码愉快！" -ForegroundColor Cyan
        break
    }
    Show-Header
}
