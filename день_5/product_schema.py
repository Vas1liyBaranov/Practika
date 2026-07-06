#Задание №1. Описание Pydantic-схемы "Карточка товара"
from typing import Literal
from pydantic import BaseModel, Field, ValidationError

class ProductCard(BaseModel):
    name: str = Field(min_length=1, description="Название товара")
    price: float = Field(gt=0, description="Цена товара, строго больше 0")
    category: Literal["Электроника", "Дом", "Книги", "Спорт", "Косметика", "Продукты"]
    tags: list[str] = Field(min_length=1, max_length=6)

products_data = [
    {"name": "AirPods Pro 2", "price": 24990, "category": "Электроника", "tags": ["наушники", "bluetooth", "шумоподавление"]},
    {"name": "Набор кастрюль Tefal", "price": 8990, "category": "Дом", "tags": ["кухня", "посуда", "кастрюли"]},
    {"name": "Булгаков М.А. роман «Мастер и Маргарита»", "price": 950, "category": "Книги", "tags": ["Булгаков", "роман", "Мастер", "Маргарита"]},
    {"name": "Гантеля разборная 20 кг", "price": 3500, "category": "Спорт", "tags": ["гантеля", "железо", "тренажер"]},
    {"name": "Dior Sauvage 100 мл", "price": 12500, "category": "Косметика", "tags": ["парфюм", "диор", "мужской"]},
    {"name": "Рис круглозерный 1 кг", "price": 95, "category": "Продукты", "tags": ["рис", "крупа", "круглозерный"]}
]

print("\n" + "Проверка карточек" + "\n")

for product in products_data:
    try:
        item = ProductCard.model_validate(product)
        print(f"{item.name} — {item.price} руб. ({item.category})")
    except ValidationError as e:
        print(f"Ошибка: {e}")

#Задание №2. Специально сломанный код
print("\n" + "Сломанный вход" + "\n")

bad_json = {
    "name": "Смартфон X",
    "price": -100,              # должно быть > 0
    "category": "Электроника",
    "tags": ["гаджет", 123]     # 123 это число, а нужно строка
}
try:
    item = ProductCard.model_validate(bad_json)
    print(f"{item}")
except ValidationError as e:
    print("Ошибка валидации:")
    print(e)

#Задание №3. Сравнение JSON mode и strict schema
print("\n" + "Сравнение JSON mode и strict schema" + "\n")

test_data = [
    {"name": "Ноутбук", "price": 50000, "category": "Электроника", "tags": ["ноутбук", "работа"]},
    {"name": "Книга", "price": 500, "category": "Книги", "tags": ["обучение"]},
    {"name": "Телефон", "price": 30000, "category": "Электроника", "tags": ["связь"]},
    {"name": "Кресло", "price": 12000, "category": "Дом", "tags": ["мебель"]},
    {"name": "Футболка", "price": 1500, "category": "Спорт", "tags": ["одежда"]},
    {"name": "Шампунь", "price": 400, "category": "Косметика", "tags": ["уход"]},
    {"name": "Макароны", "price": 80, "category": "Продукты", "tags": ["еда"]},
    {"name": "Наушники", "price": 3000, "category": "Электроника", "tags": ["аудио"]},
    {"name": "Стул", "price": 8000, "category": "Дом", "tags": ["мебель"]},
    {"name": "Кроссовки", "price": 7000, "category": "Спорт", "tags": ["обувь"]}
]
json_errors = 0
strict_errors = 0

for product in test_data:
    # JSON mode — проверка полей
    if "price" not in product or not isinstance(product["price"], (int, float)):
        json_errors += 1
    if "category" not in product or product["category"] not in ["Электроника", "Дом", "Книги", "Спорт", "Косметика", "Продукты"]:
        json_errors += 1
    if "tags" not in product or not isinstance(product["tags"], list):
        json_errors += 1
    
    # Strict schema — валидация через Pydantic
    try:
        ProductCard.model_validate(product)
    except ValidationError:
        strict_errors += 1

print(f"\n JSON mode ошибок: {json_errors}")
print(f"Strict schema ошибок: {strict_errors}")

print("\nГде ломается JSON mode:")
print("- может пропустить поле")
print("- может вернуть не тот тип (цена строкой)")
print("- категория может выйти за список")
print("- теги могут быть не массивом")
print("\nВЫВОД: Strict schema надёжнее для продакшена")