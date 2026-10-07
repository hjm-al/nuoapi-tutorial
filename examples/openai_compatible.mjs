import OpenAI from "openai";

const apiKey = process.env.NUOAPI_API_KEY;
if (!apiKey) {
  throw new Error("Set NUOAPI_API_KEY before running this example.");
}

const client = new OpenAI({
  apiKey,
  baseURL: "https://nuoapi.net/v1",
});

const model = process.env.NUOAPI_MODEL || "MODEL_NAME_FROM_MODEL_PLAZA";
const response = await client.chat.completions.create({
  model,
  messages: [{ role: "user", content: "hello" }],
});

console.log(response.choices[0].message.content);
