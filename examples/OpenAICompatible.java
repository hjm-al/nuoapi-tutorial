import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

/**
 * Java 11+ 原生 HttpClient 示例 (零第三方依赖)
 */
public class OpenAICompatible {
    /** 手工拼 JSON 时对模型名做最小转义：反斜杠、双引号与换行。 */
    private static String escapeJson(String value) {
        return value
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\r", "\\r")
                .replace("\n", "\\n");
    }

    public static void main(String[] args) throws Exception {
        String apiKey = System.getenv("NUOAPI_API_KEY");
        if (apiKey == null || apiKey.isEmpty()) {
            System.err.println("错误: 请先设置环境变量 NUOAPI_API_KEY 再运行本示例。");
            System.exit(1);
        }

        String model = System.getenv("NUOAPI_MODEL");
        if (model == null || model.isEmpty()) {
            System.err.println("错误: 请先设置环境变量 NUOAPI_MODEL 再运行本示例。");
            System.exit(1);
        }

        String jsonPayload = String.format(
            "{\"model\":\"%s\",\"messages\":[{\"role\":\"user\",\"content\":\"hello\"}]}",
            escapeJson(model)
        );

        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("https://nuoapi.net/v1/chat/completions"))
                .header("Content-Type", "application/json")
                .header("Authorization", "Bearer " + apiKey)
                .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() >= 400) {
            System.err.println("错误: HTTP " + response.statusCode() + ": " + response.body());
            System.exit(1);
        }
        System.out.println(response.body());
    }
}
