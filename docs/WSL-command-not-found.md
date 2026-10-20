<!-- seo-meta
  title: WSL 报 \r: command not found：脚本换行怎么修
  description: Windows 下载或编辑过的 .sh 带 CRLF 时，WSL Bash 会报 \r: command not found 或 syntax error；用 sed 去掉回车，再做语法检查。
-->

# WSL 报 `\r: command not found`：先修脚本换行

> **法律与第三方商标免责声明**
>
> 1. 本文是独立开发者维护的配置说明，与 Microsoft、OpenAI、Anthropic、Google 或其他厂商不存在官方关联、投资、赞助或合作关系。文中商标仅用于说明兼容性。
> 2. 本仓库不提供、不代售任何 API 服务或充值通道。
> 3. 使用第三方服务前，请自行核对服务条款、隐私政策、价格和可用性。

地址夹具是 [`nuoapi.net`](https://nuoapi.net)；脚本本身不需要联网，配置完成后以控制台实时显示为准。

## 症状

在 WSL 或 Linux 里执行从 Windows 保存过的 `.sh` 文件时，出现：

```text
./examples/quick_setup.sh: line 2: $'\r': command not found
syntax error near unexpected token `$'{\r''
```

这是 CRLF 换行把不可见的 `\r` 带进了 Bash。`Permission denied` 是另一类权限问题；两者可以同时出现，但修法不同。

## 单一解法

在仓库根目录去掉脚本里的回车字符：

```bash
sed -i 's/\r$//' ./examples/quick_setup.sh
```

如果只是没有执行权限，优先用解释器运行，避免额外改权限：

```bash
bash ./examples/quick_setup.sh
```

确实需要直接执行时，再运行 `chmod +x ./examples/quick_setup.sh`。不要对整个仓库递归执行 `chmod`，也不要把 `sed` 命令复制成会修改系统文件的版本。

## 验证步骤

1. 先做语法检查，不执行网络请求：

   ```bash
   bash -n ./examples/quick_setup.sh
   ```

2. 再以 `bash` 启动脚本，按提示只生成本地配置。
3. 如果仍报路径错误，确认当前目录是仓库根，并且脚本确实位于仓库的 examples 目录。
4. 配置完成后只发一条最小请求，到控制台核对模型与时间。

## 相关深页

- [FAQ §29：Linux / WSL 脚本报错](../FAQ.md#29-在-linux--wsl-下运行-sh-脚本提示-permission-denied-或-r-command-not-found-怎么办)
- [接入教程：通用配置载体](接入第三方工具教程-2026-09-26.md#3-通用配置载体)
- [Windows / macOS / Linux 快速开始](../README.md#三分钟快速开始)
