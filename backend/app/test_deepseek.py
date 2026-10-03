import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL")
)

response = client.chat.completions.create(
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-flash"),
    messages=[
        {"role": "user", "content": "请用一句话回答：Transformer 是什么？"}
    ],
    max_tokens=100
)

print("DeepSeek 回复：")
print(response.choices[0].message.content)