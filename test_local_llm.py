import os
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

queries = [
    "Расскажи про торговый центр",
    "Сколько будет 25 * 17?",
    "Напиши стих о программировании",
]

for q in queries:
    print(f"\n {q}")
    response = client.chat.completions.create(
        model="qwen2.5:7b",
        messages=[{"role": "user", "content": q}],
        temperature=0.7,
        max_tokens=200,
    )
    print(f" {response.choices[0].message.content}")
