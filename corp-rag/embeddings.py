# embeddings.py - исправленная версия

import os
import numpy as np
from openai import OpenAI
from typing import List
import re
import time

# Настройка клиента для Ollama
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",  # Ollama не требует ключ
)

# Используем модель для эмбеддингов
EMBEDDING_MODEL = "nomic-embed-text"  # У вас уже установлена
VECTOR_SIZE = 768  # Размер вектора для nomic-embed-text

# Кэш для эмбеддингов
_embedding_cache = {}
_embedding_cache_size = 0
MAX_CACHE_SIZE = 1000

def normalize_embedding(embedding: List[float]) -> List[float]:
    """Нормализует эмбеддинг для лучшего сравнения"""
    try:
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return embedding
        return (np.array(embedding) / norm).tolist()
    except:
        return embedding

def get_embedding(text: str) -> List[float]:
    """Получает эмбеддинг с кэшированием"""
    global _embedding_cache_size
    
    # Очищаем текст
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return [0.0] * VECTOR_SIZE
    
    # Проверяем кэш
    cache_key = hash(text)
    if cache_key in _embedding_cache:
        return _embedding_cache[cache_key]
    
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        embedding = response.data[0].embedding
        embedding = normalize_embedding(embedding)
        
        # Сохраняем в кэш
        if _embedding_cache_size < MAX_CACHE_SIZE:
            _embedding_cache[cache_key] = embedding
            _embedding_cache_size += 1
        
        return embedding
    except Exception as e:
        print(f"Ошибка получения эмбеддинга: {e}")
        return [0.0] * VECTOR_SIZE

def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Получает эмбеддинги для батча текстов"""
    if not texts:
        return []
    
    cleaned_texts = [re.sub(r'\s+', ' ', t).strip() for t in texts]
    
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=cleaned_texts
        )
        
        embeddings = []
        for data in response.data:
            embedding = normalize_embedding(data.embedding)
            embeddings.append(embedding)
        
        return embeddings
    except Exception as e:
        print(f"Ошибка батч-обработки: {e}")
        # Fallback: по одному
        embeddings = []
        for text in cleaned_texts:
            embedding = get_embedding(text)
            embeddings.append(embedding)
        return embeddings

def clear_cache():
    """Очищает кэш эмбеддингов"""
    global _embedding_cache, _embedding_cache_size
    _embedding_cache = {}
    _embedding_cache_size = 0
    print("Кэш эмбеддингов очищен")

def test_embeddings():
    """Тестирует качество эмбеддингов"""
    from vector_store import cosine_similarity
    
    test_pairs = [
        ("React фреймворк для фронтенда", "Next.js фреймворк для React"),
        ("React фреймворк для фронтенда", "Python язык программирования"),
        ("Git контроль версий", "Система контроля версий Git"),
        ("Git контроль версий", "Docker контейнеризация"),
        ("Какие технологии для фронтенда?", "React, Next.js, TypeScript, Tailwind CSS"),
        ("Какие технологии для фронтенда?", "Python, Django, PostgreSQL"),
    ]
    
    print("Тестирование качества эмбеддингов с моделью nomic-embed-text:")
    print("-" * 60)
    
    for text1, text2 in test_pairs:
        emb1 = get_embedding(text1)
        emb2 = get_embedding(text2)
        sim = cosine_similarity(emb1, emb2)
        print(f"'{text1[:35]}...' vs '{text2[:35]}...'")
        print(f"  Сходство: {sim:.3f}")
        print()

if __name__ == "__main__":
    test_embeddings()