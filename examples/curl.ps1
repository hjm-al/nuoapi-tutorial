param(
    # 也可通过 -ApiKey / -Model 显式传入；未传时从环境变量读取，不再内置占位模型名
    [string]$ApiKey = $env:NUOAPI_API_KEY,
    [string]$Model = $env:NUOAPI_MODEL
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    [Console]::Error.WriteLine("错误: 未提供 API Key。请先设置环境变量 NUOAPI_API_KEY，或通过 -ApiKey 传入。")
    exit 1
}

if ([string]::IsNullOrWhiteSpace($Model)) {
    [Console]::Error.WriteLine("错误: 未提供模型名。请先设置环境变量 NUOAPI_MODEL（模型广场中当前 Key 分组可见的精确模型 ID），或通过 -Model 传入。")
    exit 1
}

$body = @{
    model = $Model
    messages = @(
        @{
            role = "user"
            content = "hello"
        }
    )
} | ConvertTo-Json -Depth 4

# HTTP 非成功状态（含 4xx/5xx）或网络错误，都必须以非零退出码结束
try {
    $response = Invoke-WebRequest `
        -Uri "https://nuoapi.net/v1/chat/completions" `
        -Method Post `
        -Headers @{ Authorization = "Bearer $ApiKey" } `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing
} catch {
    [Console]::Error.WriteLine("HTTP 请求失败: $($_.Exception.Message)")
    exit 1
}

if ([int]$response.StatusCode -lt 200 -or [int]$response.StatusCode -ge 300) {
    [Console]::Error.WriteLine("HTTP 非成功状态: $($response.StatusCode) $($response.StatusDescription)")
    exit 1
}

Write-Output $response.Content
