#!/usr/bin/env bash
# ==============================================================================
# NuoAPI 2026 AI 开发工具一键全栈配置脚手架 (Linux / macOS / WSL)
# 支持: Codex CLI & 桌面端、Claude Code、Claude Desktop、Gemini CLI、
#       Hermes Agent (养马)、OpenClaw (龙虾)、Linux Systemd 守护进程与测谎探针
# ==============================================================================

set -e

# ANSI 颜色定义
C_RESET="\033[0m"
C_CYAN="\033[1;36m"
C_GREEN="\033[1;32m"
C_YELLOW="\033[1;33m"
C_RED="\033[1;31m"
C_GRAY="\033[0;90m"
C_WHITE="\033[1;37m"

BASE_URL="https://nuoapi.net"
# 不内置任何具体模型名默认值：模型名必须从模型广场 / /v1/models 复制当前 Key 分组可见的精确 ID
MODEL="${NUOAPI_MODEL:-}"
API_KEY="${NUOAPI_API_KEY:-}"

# 掩码后的 Key，供所有屏幕输出使用（禁止直接 echo/printf 裸 $API_KEY）
MASKED_KEY=""

# 解析命令行参数
CLI_KEY_WARNED=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        -k|--api-key)
            if [ $# -lt 2 ]; then
                echo "错误: $1 需要一个参数值（API Key）" >&2
                exit 2
            fi
            API_KEY="$2"
            if [ "$CLI_KEY_WARNED" -eq 0 ]; then
                echo -e "${C_YELLOW}警告: 命令行参数会进入 shell history，建议改用环境变量/交互输入。${C_RESET}" >&2
                CLI_KEY_WARNED=1
            fi
            shift 2
            ;;
        -m|--model)
            if [ $# -lt 2 ]; then
                echo "错误: $1 需要一个参数值（模型 ID）" >&2
                exit 2
            fi
            MODEL="$2"
            shift 2
            ;;
        -b|--base-url)
            if [ $# -lt 2 ]; then
                echo "错误: $1 需要一个参数值（Base URL）" >&2
                exit 2
            fi
            BASE_URL="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# curl HTTP 失败语义：7.76+ 用 --fail-with-body（错误时仍保留响应体），旧版降级 -f -S
if command -v curl >/dev/null 2>&1 && curl --help all 2>/dev/null | grep -q -- '--fail-with-body'; then
    CURL_FAIL_OPTS=(--fail-with-body)
else
    CURL_FAIL_OPTS=(-f -S)
fi

# ------------------------------------------------------------------------------
# 通用辅助函数
# ------------------------------------------------------------------------------

# backup_file <路径>：目标已存在时复制为 "<路径>.bak.<时间戳>.<PID>"，防同秒覆盖
backup_file() {
    local target="$1"
    if [ -f "$target" ]; then
        local backup="${target}.bak.$(date +%Y%m%d%H%M%S).$$"
        cp -p "$target" "$backup"
        echo -e "${C_GRAY}  已备份原文件: $backup${C_RESET}"
    fi
}

# ensure_secure_dir <路径>：目录不存在才创建并 chmod 700；已存在的目录不递归改权限
ensure_secure_dir() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        chmod 700 "$dir"
    fi
}

# mask_key <key>：长度>=10 输出 前6…末3，否则 ***
mask_key() {
    local key="$1"
    if [ "${#key}" -ge 10 ]; then
        printf '%s…%s' "${key:0:6}" "${key: -3}"
    else
        printf '%s' '***'
    fi
}

# strip_nuoapi_rc_blocks <rc文件>：剔除新旧 NuoAPI 导出块并裁掉尾部空行，结果输出到 stdout
strip_nuoapi_rc_blocks() {
    awk '
        $0=="# NuoAPI Claude Code Config begin" { skip=1; next }
        $0=="# NuoAPI Claude Code Config end"   { skip=0; next }
        $0=="# NuoAPI Claude Code Config"       { legacy=1; next }
        legacy && /^export ANTHROPIC_MODEL=/    { legacy=0; next }
        skip || legacy { next }
        { buf[++n]=$0 }
        END {
            while (n > 0 && buf[n] == "") n--
            for (i = 1; i <= n; i++) print buf[i]
        }
    ' "$1"
}

# run_remote_installer <URL> <取消时的手动安装提示>
# 先展示 URL、要求用户显式输入 y，再下载到临时文件执行；失败如实返回非零
run_remote_installer() {
    local url="$1"
    local manual_hint="$2"
    local tmp_file confirm rc

    echo -e "${C_WHITE}  即将从以下地址下载并执行官方安装脚本:${C_RESET}"
    echo -e "${C_YELLOW}  URL: $url${C_RESET}"
    echo -en "${C_WHITE}  确认执行请输入 y，其他输入取消: ${C_RESET}"
    read -r confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo -e "${C_GRAY}  已取消。$manual_hint${C_RESET}"
        return 0
    fi

    tmp_file="$(mktemp)"
    if ! curl -fsSL "$url" -o "$tmp_file"; then
        echo -e "${C_RED}  下载安装脚本失败: $url${C_RESET}" >&2
        rm -f "$tmp_file"
        return 1
    fi

    rc=0
    bash "$tmp_file" || rc=$?
    rm -f "$tmp_file"
    if [ "$rc" -ne 0 ]; then
        echo -e "${C_RED}  安装脚本执行失败，退出码: $rc${C_RESET}" >&2
        return "$rc"
    fi
    return 0
}

# 注入防护：写入任何文件前强制字符白名单校验，不匹配直接报错退出
validate_inputs() {
    local key_re='^sk-[A-Za-z0-9._-]{6,}$'
    local model_re='^[A-Za-z0-9._:/\-]{1,128}$'
    local url_re="^https://[A-Za-z0-9._~:/?#@!\$&'()*+,;=%-]+\$"
    local invalid=0

    if [[ ! "$API_KEY" =~ $key_re ]]; then
        echo -e "${C_RED}错误: API Key 格式非法（应以 sk- 开头，后跟至少 6 位字母/数字/._- 字符）。${C_RESET}" >&2
        invalid=1
    fi
    if [[ ! "$MODEL" =~ $model_re ]]; then
        echo -e "${C_RED}错误: 模型 ID 格式非法（仅允许 1-128 位字母数字及 . _ : / - 字符）。${C_RESET}" >&2
        invalid=1
    fi
    if [[ "$BASE_URL" =~ [[:space:]] ]] || [[ ! "$BASE_URL" =~ $url_re ]]; then
        echo -e "${C_RED}错误: Base URL 格式非法（必须是 https:// 开头且不含空白的合法 URL）。${C_RESET}" >&2
        invalid=1
    fi

    if [ "$invalid" -ne 0 ]; then
        exit 1
    fi
}

show_header() {
    clear 2>/dev/null || true
    echo -e "${C_CYAN}==================================================================${C_RESET}"
    echo -e "${C_CYAN}  NuoAPI 2026 AI 开发客户端一键全栈配置脚手架 (Linux / macOS / WSL)${C_RESET}"
    echo -e "${C_GRAY}  网关主地址: ${BASE_URL}${C_RESET}"
    echo -e "${C_GRAY}  默认模型:   ${MODEL}${C_RESET}"
    echo -e "${C_CYAN}==================================================================${C_RESET}"
    echo ""
}

ensure_api_key() {
    if [ -z "$API_KEY" ]; then
        if [ -n "$NUOAPI_API_KEY" ]; then
            API_KEY="$NUOAPI_API_KEY"
            echo -e "${C_GREEN}检测到环境变量 NUOAPI_API_KEY，已自动加载。${C_RESET}"
        else
            echo -en "${C_WHITE}请输入你的 NuoAPI API Key (sk-...): ${C_RESET}"
            read -rs API_KEY
            echo ""
            if [ -z "$API_KEY" ]; then
                echo -e "${C_RED}错误: API Key 不能为空！${C_RESET}"
                return 1
            fi
        fi
    fi
    return 0
}

ensure_model() {
    if [ -z "$MODEL" ]; then
        echo -en "${C_WHITE}请输入模型广场中当前 Key 分组可见的精确模型 ID（不要照抄其他账号）: ${C_RESET}"
        read -r MODEL
        if [ -z "$MODEL" ]; then
            echo -e "${C_RED}错误: 模型名不能为空（请先在模型广场或 /v1/models 查询后重试）。${C_RESET}"
            return 1
        fi
    fi
    return 0
}

# 1. Codex CLI & 桌面端
setup_codex() {
    echo ""
    echo -e "${C_YELLOW}[1/7] 开始配置 OpenAI Codex (CLI 终端与桌面端共享底层)...${C_RESET}"
    CODEX_DIR="$HOME/.codex"
    ensure_secure_dir "$CODEX_DIR"

    CONFIG_FILE="$CODEX_DIR/config.toml"
    if [ -f "$CONFIG_FILE" ]; then
        backup_file "$CONFIG_FILE"
        echo -e "${C_GRAY}  检测到已有配置，已创建备份。${C_RESET}"
    fi

    cat <<EOF > "$CONFIG_FILE"
model_provider = "nuoapi"
model = "$MODEL"
model_reasoning_effort = "high"
network_access = "enabled"

[model_providers.nuoapi]
name = "nuoapi"
base_url = "$BASE_URL/v1"
wire_api = "responses"
requires_openai_auth = true
# 关键防护：关闭无效的 WebSocket 握手，杜绝终端无限 Reconnecting 卡死
supports_websockets = false
EOF

    AUTH_FILE="$CODEX_DIR/auth.json"
    backup_file "$AUTH_FILE"
    cat <<EOF > "$AUTH_FILE"
{
  "OPENAI_API_KEY": "$API_KEY"
}
EOF
    chmod 600 "$AUTH_FILE"
    echo -e "${C_GREEN}  已写入: $CONFIG_FILE (已强制 supports_websockets = false)${C_RESET}"
    echo -e "${C_GREEN}  已写入: $AUTH_FILE (权限 600)${C_RESET}"
    echo -e "${C_CYAN}  Codex 配置成功！终端执行 'codex' 或 'codex --yolo' 即可启动。${C_RESET}"
}

# 2. Claude Code CLI
setup_claude_code() {
    echo ""
    echo -e "${C_YELLOW}[2/7] 开始配置 Claude Code CLI 环境变量...${C_RESET}"

    # 按当前运行 shell 选择 rc 文件，不能仅因 .zshrc 存在就改动它
    local rc_file bash_profile
    if [ -n "$ZSH_VERSION" ]; then
        rc_file="$HOME/.zshrc"
    else
        rc_file="$HOME/.bashrc"
    fi

    # HOME 通常必然存在；mkdir -p 仅为极端环境兜底，已存在的目录不改动权限
    mkdir -p "$(dirname "$rc_file")"

    # 改 rc 前先备份（文件不存在则无需备份）
    backup_file "$rc_file"

    # 用标记块定位旧块（同时兼容早期无 begin/end 标记的版本），grep/awk 到 mktemp 再 mv，
    # 规避 GNU/BSD sed -i 行为差异；多次运行不产生重复 export 块
    local tmp_rc
    tmp_rc="$(mktemp)"
    if [ -f "$rc_file" ]; then
        strip_nuoapi_rc_blocks "$rc_file" > "$tmp_rc"
    fi
    cat >> "$tmp_rc" <<EOF

# NuoAPI Claude Code Config begin
export ANTHROPIC_BASE_URL="$BASE_URL"
export ANTHROPIC_AUTH_TOKEN="$API_KEY"
export ANTHROPIC_MODEL="$MODEL"
# NuoAPI Claude Code Config end
EOF
    mv "$tmp_rc" "$rc_file"

    # macOS 的 bash 是登录 shell：保证 ~/.bash_profile 存在且幂等 source ~/.bashrc
    if [ "$(uname)" = "Darwin" ] && [ -z "$ZSH_VERSION" ]; then
        bash_profile="$HOME/.bash_profile"
        if [ ! -f "$bash_profile" ]; then
            cat > "$bash_profile" <<'EOF'
# NuoAPI bashrc bridge
[ -f ~/.bashrc ] && . ~/.bashrc
EOF
        elif ! grep -qF "NuoAPI bashrc bridge" "$bash_profile"; then
            backup_file "$bash_profile"
            cat >> "$bash_profile" <<'EOF'

# NuoAPI bashrc bridge
[ -f ~/.bashrc ] && . ~/.bashrc
EOF
        fi
    fi

    export ANTHROPIC_BASE_URL="$BASE_URL"
    export ANTHROPIC_AUTH_TOKEN="$API_KEY"
    export ANTHROPIC_MODEL="$MODEL"

    echo -e "${C_GREEN}  已将环境变量写入: $rc_file${C_RESET}"
    echo -e "${C_GREEN}  当前终端会话已即时生效 (ANTHROPIC_BASE_URL=$BASE_URL)${C_RESET}"
    echo -e "${C_YELLOW}  核心避坑提醒：Claude Code 的 Base URL 严禁加 /v1，当前已对齐站点根地址。${C_RESET}"
    echo -e "${C_CYAN}  新开终端执行 'claude' 即可体验。${C_RESET}"
}

# 3. Claude Desktop / Cowork
setup_claude_desktop() {
    echo ""
    echo -e "${C_YELLOW}[3/7] 开始配置 Claude Desktop (Cowork 模式 / 开发者模式第三方推理)...${C_RESET}"
    if [ "$(uname)" = "Darwin" ]; then
        CLAUDE_DIR="$HOME/Library/Application Support/Claude"
    else
        CLAUDE_DIR="$HOME/.config/Claude"
    fi
    ensure_secure_dir "$CLAUDE_DIR"

    CONFIG_FILE="$CLAUDE_DIR/claude_desktop_config.json"
    if [ -f "$CONFIG_FILE" ]; then
        backup_file "$CONFIG_FILE"
        echo -e "${C_GRAY}  检测到已有桌面端配置，已创建备份。${C_RESET}"
    fi

    cat <<EOF > "$CONFIG_FILE"
{
  "inference": {
    "provider": "third_party",
    "base_url": "$BASE_URL",
    "api_key": "$API_KEY"
  }
}
EOF
    chmod 600 "$CONFIG_FILE"
    echo -e "${C_GREEN}  已写入底层配置文件: $CONFIG_FILE (权限 600)${C_RESET}"
    echo -e "${C_CYAN}  【Claude Desktop 开发者模式操作步骤】:${C_RESET}"
    echo -e "${C_WHITE}  1. 打开应用，停留在登录页面（若已登录请点击头像退出登录）；${C_RESET}"
    echo -e "${C_WHITE}  2. 点击 Help -> Troubleshooting -> Enable Developer Mode；${C_RESET}"
    echo -e "${C_WHITE}  3. 顶栏出现 Developer 菜单 -> 点击 Developer -> Configure third-party inference；${C_RESET}"
    echo -e "${C_WHITE}  4. 填写 Base URL: ${C_YELLOW}$BASE_URL${C_RESET} | API Key: ${C_YELLOW}$MASKED_KEY${C_RESET}"
}

# 4. Gemini CLI
setup_gemini() {
    echo ""
    echo -e "${C_YELLOW}[4/7] 开始配置 Gemini CLI...${C_RESET}"
    GEMINI_DIR="$HOME/.gemini"
    ensure_secure_dir "$GEMINI_DIR"

    GEMINI_ENV="$GEMINI_DIR/.env"
    backup_file "$GEMINI_ENV"
    cat <<EOF > "$GEMINI_ENV"
GOOGLE_GEMINI_BASE_URL=$BASE_URL
GEMINI_API_KEY=$API_KEY
GEMINI_MODEL=$MODEL
EOF
    chmod 600 "$GEMINI_ENV"
    echo -e "${C_GREEN}  已写入: $GEMINI_ENV (权限 600)${C_RESET}"
    echo -e "${C_CYAN}  Gemini CLI 配置完成！终端运行 'gemini' 即可启动。${C_RESET}"
}

# 5. Hermes Agent (养马)
setup_hermes() {
    echo ""
    echo -e "${C_YELLOW}[5/7] 开始配置 Hermes Agent (养马 · Nous Research 本地自主智能体)...${C_RESET}"
    HERMES_DIR="$HOME/.hermes"
    ensure_secure_dir "$HERMES_DIR"

    HERMES_CONFIG="$HERMES_DIR/config.yaml"
    HERMES_ENV="$HERMES_DIR/.env"
    backup_file "$HERMES_CONFIG"
    backup_file "$HERMES_ENV"

    cat <<EOF > "$HERMES_CONFIG"
model:
  provider: custom
  base_url: "$BASE_URL/v1"
  default: "$MODEL"
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
EOF
    chmod 600 "$HERMES_CONFIG"

    cat <<EOF > "$HERMES_ENV"
OPENAI_BASE_URL=$BASE_URL/v1
OPENAI_API_KEY=$API_KEY
HERMES_MODEL=$MODEL
EOF
    chmod 600 "$HERMES_ENV"
    echo -e "${C_GREEN}  已写入: $HERMES_CONFIG 和 $HERMES_ENV (权限 600)${C_RESET}"

    if command -v hermes &> /dev/null; then
        echo -e "${C_GREEN}  检测到系统已就绪 hermes 命令: $(command -v hermes)${C_RESET}"
    else
        echo -e "${C_YELLOW}  提示: 系统未检测到 hermes 命令。${C_RESET}"
        if run_remote_installer \
            "https://hermes-agent.nousresearch.com/install.sh" \
            "后续可手动执行: curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash"; then
            echo -e "${C_GREEN}  Hermes Agent 官方安装脚本执行完毕。${C_RESET}"
        else
            return 1
        fi
    fi
    echo -e "${C_CYAN}  配置就绪！在终端运行 'hermes' 即可唤醒自主智能体。${C_RESET}"
}

# 6. OpenClaw (龙虾)
setup_openclaw() {
    echo ""
    echo -e "${C_YELLOW}[6/7] 开始配置 OpenClaw (龙虾 · 本地优先自主助理与自动化平台)...${C_RESET}"
    OPENCLAW_DIR="$HOME/.openclaw"
    ensure_secure_dir "$OPENCLAW_DIR"

    OPENCLAW_CONFIG="$OPENCLAW_DIR/openclaw.json"
    backup_file "$OPENCLAW_CONFIG"
    cat <<EOF > "$OPENCLAW_CONFIG"
{
  "\$schema": "https://openclaw.ai/schema/config.json",
  "version": "2.0",
  "models": {
    "providers": {
      "nuoapi": {
        "baseUrl": "$BASE_URL/v1",
        "apiKey": "$API_KEY",
        "apiType": "openai"
      }
    },
    "default": "$MODEL"
  },
  "agent": {
    "name": "OpenClaw-Worker",
    "workspace": "./workspace",
    "permissions": {
      "allowTerminal": true,
      "allowFileSystem": true,
      "allowBrowser": true
    }
  },
  "ui": {
    "theme": "dark",
    "port": 3000
  }
}
EOF
    chmod 600 "$OPENCLAW_CONFIG"
    echo -e "${C_GREEN}  已写入标准配置文件: $OPENCLAW_CONFIG (权限 600)${C_RESET}"

    if command -v openclaw &> /dev/null; then
        echo -e "${C_GREEN}  检测到系统已就绪 openclaw 命令: $(command -v openclaw)${C_RESET}"
    else
        echo -e "${C_YELLOW}  提示: 系统未检测到 openclaw 命令。${C_RESET}"
        if run_remote_installer \
            "https://openclaw.ai/install.sh" \
            "后续可手动执行: curl -fsSL https://openclaw.ai/install.sh | bash 或 npm i -g openclaw@latest"; then
            :
        else
            return 1
        fi
    fi
    echo -e "${C_CYAN}  配置就绪！终端运行 'openclaw' 即可启动 Control UI (端口 3000)。${C_RESET}"
}

# 7. Linux Systemd 守护进程服务生成
setup_systemd_service() {
    echo ""
    echo -e "${C_YELLOW}[Linux 守护进程] 生成 Systemd 后台服务文件...${C_RESET}"
    SERVICE_FILE="/tmp/hermes-agent.service"
    CURRENT_USER="$(whoami)"
    USER_HOME="$HOME"

    cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=Hermes Autonomous AI Agent Service (NuoAPI Backend)
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$USER_HOME
EnvironmentFile=$USER_HOME/.hermes/.env
Environment=NODE_ENV=production
Environment=OPENAI_BASE_URL=$BASE_URL/v1
ExecStart=$(which hermes 2>/dev/null || echo "/usr/local/bin/hermes") daemon
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

    echo -e "${C_GREEN}  已生成 Systemd 模板文件: $SERVICE_FILE${C_RESET}"
    echo -e "${C_WHITE}  如需在 Linux VPS 7x24 小时开机自启后台运行，请执行以下命令：${C_RESET}"
    echo -e "${C_CYAN}  sudo cp $SERVICE_FILE /etc/systemd/system/hermes-agent.service${C_RESET}"
    echo -e "${C_CYAN}  sudo systemctl daemon-reload${C_RESET}"
    echo -e "${C_CYAN}  sudo systemctl enable --now hermes-agent${C_RESET}"
    echo -e "${C_CYAN}  sudo systemctl status hermes-agent${C_RESET}"
}

run_hello() {
    echo ""
    echo -e "${C_YELLOW}[探活测试] 正在向 NuoAPI 网关发送联通性最小探针...${C_RESET}"
    if ! RESPONSE=$(curl -sS "${CURL_FAIL_OPTS[@]}" -X POST "$BASE_URL/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $API_KEY" \
        -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"你好，只回复连接成功四个字\"}],\"max_tokens\":32}" 2>&1); then
        echo -e "${C_RED}  探活请求失败（curl 非零退出），接口原始响应:${C_RESET}"
        echo -e "${C_WHITE}  $RESPONSE${C_RESET}"
        return 1
    fi

    if echo "$RESPONSE" | grep -q "连接成功"; then
        echo -e "${C_GREEN}  网关响应成功！模型 [$MODEL] 回复正常。${C_RESET}"
    else
        echo -e "${C_WHITE}  接口原始响应: $RESPONSE${C_RESET}"
    fi
}

run_model_verify() {
    echo ""
    echo -e "${C_YELLOW}[真伪探针] 运行三段式探针 model_verify.py（A 段字段取证，近零成本）...${C_RESET}"
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    VERIFY_SCRIPT="$SCRIPT_DIR/model_verify.py"
    if [ ! -f "$VERIFY_SCRIPT" ]; then
        echo -e "${C_RED}  未找到探针脚本: $VERIFY_SCRIPT${C_RESET}"
        return
    fi
    export NUOAPI_API_KEY="$API_KEY"
    export NUOAPI_MODEL="$MODEL"
    export NUOAPI_BASE_URL="$BASE_URL/v1"
    # 先跑 DRY RUN：只打印计划与预估用量，不产生任何计费请求
    python3 "$VERIFY_SCRIPT" --tier A
    echo -en "${C_WHITE}  DRY RUN 已打印计划。确认后才会发起 1 次极短计费请求（A 段），是否继续？(y/n): ${C_RESET}"
    read -r CONFIRM_RUN
    if [ "$CONFIRM_RUN" = "y" ] || [ "$CONFIRM_RUN" = "Y" ]; then
        python3 "$VERIFY_SCRIPT" --tier A --run
    else
        echo -e "${C_GRAY}  已取消计费请求。旧脚本 model_authenticity_check.py 属 D 档低判别力反例，不要再用于下结论。${C_RESET}"
    fi
}

# ----------------- 主程序逻辑 -----------------
show_header

if ! ensure_api_key; then
    exit 1
fi

if ! ensure_model; then
    exit 1
fi

# 写入任何文件 / 发起请求前做字符白名单校验
validate_inputs

# 此后屏幕上需要出现 Key 的地方一律使用掩码
MASKED_KEY="$(mask_key "$API_KEY")"

while true; do
    echo ""
    echo -e "${C_WHITE}请选择需要配置的工具或操作：${C_RESET}"
    echo -e "  [1] 一键配置 Codex (CLI 终端 & 桌面端共享配置 · 强制关闭 WebSocket)"
    echo -e "  [2] 一键配置 Claude Code CLI (根域名自动对齐与环境变量持久化)"
    echo -e "  [3] 一键预配 Claude Desktop (Cowork 模式 / 开发者模式第三方推理)"
    echo -e "  [4] 一键配置 Gemini CLI"
    echo -e "  [5] 一键配置 Hermes Agent (养马 · Nous Research 本地自主智能体)"
    echo -e "  [6] 一键配置 OpenClaw (龙虾 · 本地优先自主助理)"
    echo -e "  [7] 全部一键配置 (Codex + Claude + Gemini + Hermes + OpenClaw)"
    echo -e "  [8] 生成 Linux Systemd 守护进程服务 (VPS 7x24 小时后台运行)"
    echo -e "  [9] 发送最小探活请求 (验证 Key 与模型连通性)"
    echo -e "  [10] 运行模型真伪探针 model_verify.py (A 段字段取证，先 DRY RUN 后确认计费)"
    echo -e "  [0] 退出脚本"
    echo ""
    echo -en "${C_WHITE}请输入选项数字 [0-10]: ${C_RESET}"
    read -r CHOICE

    case "$CHOICE" in
        1) setup_codex ;;
        2) setup_claude_code ;;
        3) setup_claude_desktop ;;
        4) setup_gemini ;;
        5) setup_hermes ;;
        6) setup_openclaw ;;
        7)
            setup_codex
            setup_claude_code
            setup_claude_desktop
            setup_gemini
            setup_hermes
            setup_openclaw
            run_hello
            ;;
        8) setup_systemd_service ;;
        9) run_hello ;;
        10) run_model_verify ;;
        0) echo -e "${C_GRAY}已退出。${C_RESET}"; break ;;
        *) echo -e "${C_RED}无效选项，请重新输入。${C_RESET}" ;;
    esac

    echo ""
    echo -e "${C_GRAY}--------------------------------------------------${C_RESET}"
    echo -en "${C_WHITE}是否继续执行其他操作？(y/n): ${C_RESET}"
    read -r AGAIN
    if [[ ! "$AGAIN" =~ ^[Yy]$ ]]; then
        echo -e "${C_CYAN}配置结束。祝 Linux / macOS 编码愉快！${C_RESET}"
        break
    fi
    show_header
done
