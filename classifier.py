import os
import json
import time
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Ticket(BaseModel):
    category: str
    sentiment: str
    priority: int

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)

def classify(text):
    prompt = f"""
Ты классификатор обращений в службу поддержки.

Категории: ремонт, финансы, персонал, обслуживание, другое.
Тональность: positive, neutral, negative.
Приоритет: 1-5 (1 - срочно, 5 - не срочно).

Примеры:
"Спасибо за помощь!" → {{"category": "обслуживание", "sentiment": "positive", "priority": 5}}
"Сломался лифт" → {{"category": "ремонт", "sentiment": "negative", "priority": 1}}
"Когда будет договор?" → {{"category": "финансы", "sentiment": "neutral", "priority": 3}}

Верни ТОЛЬКО JSON без маркеров для:
{text}
"""

    try:
        resp = client.chat.completions.create(
            model="google/gemma-4-26b-a4b-it:free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=150
        )
        
        raw = resp.choices[0].message.content
        print("Ответ модели:", raw)
        
        start = raw.find('{')
        end = raw.rfind('}') + 1
        if start != -1 and end != 0:
            json_str = raw[start:end]
            data = json.loads(json_str)
            return Ticket(**data)
        
    except Exception as e:
        print("Ошибка:", e)
    
    return Ticket(category="другое", sentiment="neutral", priority=5)


texts = [
    "Спасибо за помощь!",
    "Сломался лифт, люди застряли",
    "Когда будет договор аренды?",
    "Карта не проходит оплату",
    "В магазине грязно",
    "Какой график работы?",
    "Спасибо, заменили лампы",
    "Нужна консультация по аренде",
    "Почему такой высокий счёт?"
]

print("Классификация обращений")
print("-" * 40)

for text in texts:
    print(f"\nТекст: {text}")
    result = classify(text)
    print(f"   Категория: {result.category}")
    print(f"   Тональность: {result.sentiment}")
    print(f"   Приоритет: {result.priority}")
    time.sleep(3)