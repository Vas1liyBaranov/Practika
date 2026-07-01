import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)

# Список бесплатных моделей, которые точно должны работать
models = [
    "meta-llama/llama-3.2-3b-instruct:free",
    "microsoft/phi-3-mini-128k-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "google/gemini-2.0-flash-lite-preview-02-05:free",
]

for model in models:
    try:
        print(f"Пробуем модель: {model}")
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Привет! Ответь одним словом: работает?"}],
            max_tokens=20,
        )
        print(f"✅ {model} ответил: {resp.choices[0].message.content}\n")
        print("🎉 Успех! Можем использовать эту модель!")
        break
    except Exception as e:
        print(f"❌ {model} не работает: {e}\n")
