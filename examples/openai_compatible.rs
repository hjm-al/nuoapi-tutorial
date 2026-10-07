// 依赖说明 (Cargo.toml):
// [dependencies]
// reqwest = { version = "0.11", features = ["json"] }
// tokio = { version = "1", features = ["full"] }
// serde_json = "1.0"

use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_TYPE};
use serde_json::json;
use std::env;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let api_key = match env::var("NUOAPI_API_KEY") {
        Ok(v) if !v.is_empty() => v,
        _ => {
            eprintln!("错误: 请先设置环境变量 NUOAPI_API_KEY 再运行本示例。");
            std::process::exit(1);
        }
    };
    let model = match env::var("NUOAPI_MODEL") {
        Ok(v) if !v.is_empty() => v,
        _ => {
            eprintln!("错误: 请先设置环境变量 NUOAPI_MODEL 再运行本示例。");
            std::process::exit(1);
        }
    };

    let mut headers = HeaderMap::new();
    headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/json"));
    headers.insert(
        AUTHORIZATION,
        HeaderValue::from_str(&format!("Bearer {}", api_key))?,
    );

    let client = reqwest::Client::new();
    let body = json!({
        "model": model,
        "messages": [{"role": "user", "content": "hello"}]
    });

    let response = client
        .post("https://nuoapi.net/v1/chat/completions")
        .headers(headers)
        .json(&body)
        .send()
        .await?;

    if !response.status().is_success() {
        let status = response.status();
        let error_body = response.text().await?;
        eprintln!("错误: HTTP {}: {}", status, error_body);
        std::process::exit(1);
    }

    let res = response.text().await?;

    println!("{}", res);
    Ok(())
}
