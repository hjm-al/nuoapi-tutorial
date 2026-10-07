<?php
/**
 * PHP 原生 cURL 示例 (零第三方依赖)
 */

$apiKey = getenv('NUOAPI_API_KEY');
if ($apiKey === false || $apiKey === '') {
    fwrite(STDERR, "错误: 请先设置环境变量 NUOAPI_API_KEY 再运行本示例。\n");
    exit(1);
}
$model = getenv('NUOAPI_MODEL');
if ($model === false || $model === '') {
    fwrite(STDERR, "错误: 请先设置环境变量 NUOAPI_MODEL 再运行本示例。\n");
    exit(1);
}

$ch = curl_init('https://nuoapi.net/v1/chat/completions');
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => [
        'Content-Type: application/json',
        'Authorization: Bearer ' . $apiKey,
    ],
    CURLOPT_POSTFIELDS => json_encode([
        'model' => $model,
        'messages' => [
            ['role' => 'user', 'content' => 'hello']
        ]
    ]),
]);

$response = curl_exec($ch);
if (curl_errno($ch)) {
    fwrite(STDERR, 'Curl error: ' . curl_error($ch) . PHP_EOL);
    curl_close($ch);
    exit(1);
}
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
if ($httpCode >= 400) {
    fwrite(STDERR, "错误: HTTP {$httpCode}: {$response}" . PHP_EOL);
    curl_close($ch);
    exit(1);
}
curl_close($ch);
echo $response . PHP_EOL;
