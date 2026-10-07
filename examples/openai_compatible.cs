using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;

class OpenAICompatible
{
    // 手工拼 JSON 时对模型名做最小转义：反斜杠、双引号与换行
    static string EscapeJson(string value) =>
        value.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\r", "\\r").Replace("\n", "\\n");

    static async Task Main()
    {
        string apiKey = Environment.GetEnvironmentVariable("NUOAPI_API_KEY");
        if (string.IsNullOrEmpty(apiKey))
        {
            Console.Error.WriteLine("错误: 请先设置环境变量 NUOAPI_API_KEY 再运行本示例。");
            Environment.Exit(1);
        }
        string model = Environment.GetEnvironmentVariable("NUOAPI_MODEL");
        if (string.IsNullOrEmpty(model))
        {
            Console.Error.WriteLine("错误: 请先设置环境变量 NUOAPI_MODEL 再运行本示例。");
            Environment.Exit(1);
        }

        using var client = new HttpClient();
        client.DefaultRequestHeaders.Add("Authorization", $"Bearer {apiKey}");

        string json = $"{{\"model\":\"{EscapeJson(model)}\",\"messages\":[{{\"role\":\"user\",\"content\":\"hello\"}}]}}";
        var content = new StringContent(json, Encoding.UTF8, "application/json");

        var response = await client.PostAsync("https://nuoapi.net/v1/chat/completions", content);
        string result = await response.Content.ReadAsStringAsync();
        if (!response.IsSuccessStatusCode)
        {
            Console.Error.WriteLine($"错误: HTTP {(int)response.StatusCode}: {result}");
            Environment.Exit(1);
        }
        Console.WriteLine(result);
    }
}
