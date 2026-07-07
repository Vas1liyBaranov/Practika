import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)

# Товары в каталоге
catalog = [
    {"name": "Ноутбук AirBook 14", "category": "Электроника", "price": 79990},
    {"name": "Наушники SoundMini", "category": "Электроника", "price": 3490},
    {"name": "Книга Python Start", "category": "Книги", "price": 1490},
    {"name": "Коврик для йоги Balance", "category": "Спорт", "price": 1290},
]

# Инструменты
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Используй только для точных вычислений, когда все числа есть в запросе. Не используй для поиска товаров.",
            "parameters": {"type": "object","properties": {"expression": {"type": "string"}},"required": ["expression"]}}},
    {
        "type": "function",
        "function": {
            "name": "search_catalog",
            "description": "Используй для поиска товаров, цен, категорий. Если нужна цена для расчёта — сначала вызови этот инструмент.",
            "parameters": {"type": "object", "properties": {"query": {"type": "string"}},"required": ["query"]}}}
]
log = []

# Функции
def calc(expr):
    return eval(expr)

def search(q):
    q = q.lower()
    return [x for x in catalog if q in x["name"].lower() or q in x["category"].lower()]

def ask(user_input):
    msg = [{"role": "user", "content": user_input}]
    res = client.chat.completions.create(model="google/gemma-4-26b-a4b-it:free", messages=msg, tools=tools)
    msg2 = res.choices[0].message
    if msg2.tool_calls:
        for call in msg2.tool_calls:
            args = json.loads(call.function.arguments)
            if call.function.name == "calculate":
                result = calc(args["expression"])
            else:
                result = search(args["query"])
            log.append({"tool": call.function.name, "args": args, "result": result})
            print(f"🔧 Вызван инструмент: {call.function.name}({args}) → Результат: {result}")
            msg.append(msg2)
            msg.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result, ensure_ascii=False)})
        final = client.chat.completions.create(model="google/gemma-4-26b-a4b-it:free", messages=msg)
        return final.choices[0].message.content
    return msg2.content

#Задание №1. Проверка калькулятора
print("\n" + "1. Проверка калькулятора" + "\n")
q = "Сколько будет (1250 * 3 + 499) / 7?"
print(f"Запрос: {q}")
ans = ask(q)
print(f"Ответ модели: {ans}\n")

#Задание №2. 10 запросов
print("\n" + "2. Проверка выбора инструментов (10 запросов)" + "\n")
queries = [
    ("Сколько будет 25 * 17?", "calculate"),
    ("Найди ноутбук в каталоге", "search_catalog"),
    ("Какая цена у SoundMini?", "search_catalog"),
    ("Сколько будет (1990 + 3490) * 2?", "calculate"),
    ("Покажи товары категории Электроника", "search_catalog"),
    ("Найди книгу про Python", "search_catalog"),
    ("Раздели 79990 на 12", "calculate"),
    ("Есть ли товары для спорта?", "search_catalog"),
    ("Сколько стоят два коврика Balance?", "search_catalog, затем calculate"),
    ("Сложи цену наушников и книги Python", "search_catalog, затем calculate")
]
for q, exp in queries:
    print(f"\nЗапрос: {q}")
    print(f"Ожидаемый инструмент: {exp}")
    ans = ask(q)
    print(f"Ответ модели: {ans}")

#Задание №3.  Лог вызовов
print("\n" + "3. Лог вызовов инструментов" + "\n")
for item in log:
    print(f"Инструмент: {item['tool']} | Аргументы: {item['args']} | Результат: {item['result']}")

#Задание №4.  запросы с ошибкой
print("\n" + "4. Запрос, где может быть ошибка" + "\n")

bad = "Сколько стоят два коврика Balance?"
print(f"Запрос: {bad}")
print("Проблема: модель может сразу вызвать calculate, хотя чисел недостаточно.")
print("Решение: сначала нужно вызвать search_catalog, чтобы узнать цену, потом calculate.")
print("Улучшение описания calculate: 'Используй ТОЛЬКО когда все числа явно указаны в запросе'")

# вывод
print("\n" + "5. Вывод" + "\n")
print("""
Tool calling — модель не считает сама, а вызывает функции.
По логу видно, какие инструменты и когда выбрала модель.
Strict schema лучше для продакшена — гарантирует структуру данных.
Главное в задании: смотреть лог вызовов, а не только финальный ответ.
""")
