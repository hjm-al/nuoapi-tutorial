package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"time"
)

func main() {
	apiKey := os.Getenv("NUOAPI_API_KEY")
	if apiKey == "" {
		log.Fatal("错误: 请先设置环境变量 NUOAPI_API_KEY 再运行本示例。")
	}
	model := os.Getenv("NUOAPI_MODEL")
	if model == "" {
		log.Fatal("错误: 请先设置环境变量 NUOAPI_MODEL 再运行本示例。")
	}

	payload := map[string]interface{}{
		"model": model,
		"messages": []map[string]string{
			{"role": "user", "content": "hello"},
		},
	}
	body, err := json.Marshal(payload)
	if err != nil {
		panic(err)
	}

	req, err := http.NewRequest("POST", "https://nuoapi.net/v1/chat/completions", bytes.NewBuffer(body))
	if err != nil {
		panic(err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)

	// 显式超时：DefaultClient 没有超时，网络异常时可能永久挂起
	client := &http.Client{Timeout: 60 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		panic(err)
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		fmt.Fprintf(os.Stderr, "错误: HTTP %d: %s\n", resp.StatusCode, string(respBody))
		os.Exit(1)
	}
	fmt.Println(string(respBody))
}
