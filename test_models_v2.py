import os
from openai import OpenAI
from dotenv import load_dotenv
import time

load_dotenv()

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)

# Актуальные бесплатные модели OpenRouter (март 2026)
models = [
    "google/gemini-2.0-flash-thinking-exp:free",
    "google/gemini-2.0-pro-exp:free",
    "google/gemini-2.0-flash-exp:free", 
    "meta-llama/llama-3.1-8b-instruct:free",
    "mistralai/mistral-7b-instruct-v0.3:free",
]

for model in models:
    try:
        print(f"Пробуем модель: {model}")
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Привет! Ответь одним словом: работает?"}],
            max_tokens=20,
            timeout=15,
        )
        print(f"✅ {model} ответил: {resp.choices[0].message.content}")
        print("🎉 Нашли работающую модель!\n")
        break
    except Exception as e:
        print(f"❌ {model} не работает: {str(e)[:100]}...\n")
        time.sleep(2)  # Пауза между запросами

