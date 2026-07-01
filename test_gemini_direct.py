import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Настраиваем API ключ
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Пробуем разные модели
models = ["gemini-pro", "gemini-1.5-flash", "gemini-1.5-pro"]

for model_name in models:
    try:
        print(f"Пробуем модель: {model_name}")
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Привет! Ответь одним словом: работает?")
        print(f"✅ {model_name} ответил: {response.text}\n")
        break
    except Exception as e:
        print(f"❌ {model_name} не работает: {e}\n")
