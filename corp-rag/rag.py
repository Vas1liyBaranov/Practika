# rag.py - исправленная версия

import time
import re
from typing import Dict, List
from db import add_query, update_query_answer
from vector_store import search
from openai import OpenAI

# Настройка клиента для Ollama
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

LLM_MODEL = "phi3:mini"

def extract_answer_from_text(text: str, question: str) -> str:
    """
    Улучшенное извлечение ответа из формата Q&A с учетом синонимов
    """
    # Нормализуем вопрос
    question_lower = question.lower().strip()
    
    # Словарь синонимов для точного поиска
    synonyms = {
        'начало': ['начинается', 'начать', 'старт', 'во сколько'],
        'рабочий день': ['рабочее время', 'график', 'часы работы', 'работа'],
        'окончание': ['заканчивается', 'конец', 'до скольки'],
        'депозит': ['вклад', 'депозитный'],
        'стажировка': ['стаж', 'практика'],
        'график': ['расписание', 'режим']
    }
    
    # Расширяем вопрос синонимами
    expanded_question = question_lower
    for word, syns in synonyms.items():
        if word in question_lower:
            expanded_question += ' ' + ' '.join(syns)
    
    question_keywords = set(expanded_question.split())
    
    # Разбиваем на строки
    lines = text.split('\n')
    
    # Ищем все Q&A пары
    qa_pairs = []
    current_question = None
    current_answer = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        line_lower = line.lower()
        
        # Проверяем, является ли строка вопросом
        if 'вопрос' in line_lower or '?' in line_lower or 'q:' in line_lower:
            # Если уже был предыдущий вопрос, сохраняем его
            if current_question is not None and current_answer:
                qa_pairs.append({
                    'question': current_question,
                    'answer': ' '.join(current_answer)
                })
                current_answer = []
            
            # Проверяем совпадение с нашим вопросом
            line_keywords = set(line_lower.split())
            overlap = len(question_keywords & line_keywords)
            
            # Также проверяем вхождение ключевых слов
            keyword_match = False
            for kw in question_keywords:
                if kw in line_lower and len(kw) > 2:
                    keyword_match = True
                    break
            
            if overlap >= 1 or keyword_match:
                current_question = line
                # Ищем ответ в следующих строках
                for j in range(i + 1, min(i + 6, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line:
                        continue
                    
                    # Если нашли следующий вопрос - останавливаемся
                    if 'вопрос' in next_line.lower() or '?' in next_line.lower():
                        break
                    
                    # Убираем маркеры ответа
                    cleaned = re.sub(r'^ответ\s*[:;—]\s*', '', next_line, flags=re.IGNORECASE)
                    cleaned = re.sub(r'^ответ\s*', '', cleaned, flags=re.IGNORECASE)
                    cleaned = re.sub(r'^a[:;]\s*', '', cleaned, flags=re.IGNORECASE)
                    
                    if cleaned and len(cleaned) > 3:
                        if 'вопрос' not in cleaned.lower():
                            current_answer.append(cleaned)
                
                # Если нашли ответ - возвращаем сразу
                if current_answer:
                    return ' '.join(current_answer)
    
    # Если не нашли прямой ответ, ищем по всем парам
    if qa_pairs:
        # Ищем наиболее релевантный
        best_score = 0
        best_answer = None
        
        for pair in qa_pairs:
            pair_question = pair['question'].lower()
            pair_keywords = set(pair_question.split())
            overlap = len(question_keywords & pair_keywords)
            score = overlap / len(question_keywords) if question_keywords else 0
            
            if score > best_score:
                best_score = score
                best_answer = pair['answer']
        
        if best_answer and best_score > 0.3:
            return best_answer
    
    return None

def find_best_answer(results: List[Dict], question: str) -> tuple:
    """
    Находит лучший ответ среди результатов
    """
    question_lower = question.lower()
    
    # Специальные правила для разных типов вопросов
    question_types = {
        'начало работы': ['во сколько', 'начало', 'начинается', 'старт', '09:00', '10:00', 'начале'],
        'график': ['график', 'расписание', 'режим', 'часы работы'],
        'депозит': ['депозит', 'вклад'],
        'стажировка': ['стажировка', 'стаж', 'практика'],
        'дом': ['дома', 'удаленно', 'удалённо', 'дистанционно'],
        'гит': ['git', 'ветка', 'коммит'],
        'технологии': ['технологии', 'стек', 'инструменты'],
    }
    
    # Определяем тип вопроса
    question_type = None
    for qtype, keywords in question_types.items():
        if any(kw in question_lower for kw in keywords):
            question_type = qtype
            break
    
    # Ищем среди результатов
    best_match = None
    best_score = -1
    
    for r in results:
        text = r['text'].lower()
        
        # Проверяем, содержит ли текст ответ на нужный тип вопроса
        if question_type == 'начало работы':
            # Ищем упоминание времени начала
            time_patterns = [r'10:00', r'09:00', r'10\s*ч', r'9\s*ч', r'начал']
            if any(re.search(p, text) for p in time_patterns):
                if 'выходные' not in text:  # Исключаем про выходные
                    return r['text'], r
        
        # Стандартный поиск
        if 'вопрос' in text and 'ответ' in text:
            # Извлекаем Q&A пару
            qa_match = re.search(r'вопрос\s*[:;]\s*(.+?)(?:\n|\s*?)(?:ответ|a)\s*[:;]\s*(.+?)(?=\n\s*(?:вопрос|q|$))', 
                                r['text'], re.IGNORECASE | re.DOTALL)
            if qa_match:
                q_text = qa_match.group(1).lower()
                a_text = qa_match.group(2)
                
                # Проверяем релевантность вопроса
                q_keywords = set(question_lower.split())
                q_match_keywords = set(q_text.split())
                overlap = len(q_keywords & q_match_keywords)
                
                if overlap >= 1:
                    return a_text.strip(), r
    
    # Если ничего не нашли, возвращаем первый результат
    if results:
        return results[0]['text'], results[0]
    
    return None, None

def ask(question: str) -> dict:
    """
    Основная функция ответа на вопрос
    """
    start_time = time.time()  # Определяем start_time здесь
    
    # Сначала пробуем быструю версию
    fast_result = ask_fast(question, start_time)
    
    # Проверяем, правильный ли ответ
    question_lower = question.lower()
    answer_lower = fast_result['answer'].lower()
    
    # Если вопрос про начало работы, а ответ про выходные - это неправильно
    if ('начало' in question_lower or 'начинается' in question_lower) and 'выходные' in answer_lower:
        print("⚠️ Неправильный ответ, пробуем LLM...")
        
        # Используем LLM
        results = search(question, top_k=5, score_threshold=0.2)
        if not results:
            return fast_result
        
        context = "\n\n".join([
            f"Документ {i+1} ({r['filename']}):\n{r['text']}"
            for i, r in enumerate(results[:3])
        ])
        
        prompt = f"""Ответь на вопрос, используя ТОЛЬКО информацию из документов.
Если в документах нет точного ответа, скажи "Информация не найдена".

Вопрос: {question}

Документы:
{context}

Краткий ответ:"""
        
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "Ты помощник. Отвечай кратко и только по документам."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150,
                stream=False
            )
            
            answer = response.choices[0].message.content.strip()
            if not answer or len(answer) < 3:
                answer = results[0]['text'][:200]
            
            status = "answered"
            sources = [{
                "filename": r["filename"],
                "page": str(r.get("page", 1)),
                "excerpt": r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"],
                "score": r["score"]
            } for r in results[:3]]
            
            latency_ms = int((time.time() - start_time) * 1000)
            query_id = add_query(question, status="processing")
            update_query_answer(query_id, answer, status, latency_ms, sources)
            
            return {
                "query_id": query_id,
                "question": question,
                "answer": answer,
                "status": status,
                "sources": sources,
                "latency_ms": latency_ms
            }
            
        except Exception as e:
            print(f"Ошибка LLM: {e}")
            return fast_result
    
    return fast_result

def ask_fast(question: str, start_time: float = None) -> dict:
    """
    Быстрая версия - только извлечение из Q&A, без LLM
    """
    if start_time is None:
        start_time = time.time()
    
    query_id = add_query(question, status="processing")
    
    # Ищем документы
    results = search(question, top_k=5, score_threshold=0.2)
    
    if not results:
        answer = "Информация не найдена."
        status = "not_found"
        sources = []
    else:
        # Ищем ответ в Q&A формате по всем документам
        answer = None
        source_doc = None
        
        # Сначала пробуем извлечь через extract_answer_from_text
        for r in results:
            extracted = extract_answer_from_text(r['text'], question)
            if extracted:
                answer = extracted
                source_doc = r
                print(f"✅ Найден Q&A ответ в {r['filename']}")
                break
        
        # Если не нашли, пробуем find_best_answer
        if not answer:
            best_answer, best_doc = find_best_answer(results, question)
            if best_answer:
                answer = best_answer
                source_doc = best_doc
                print(f"✅ Найден лучший ответ в {best_doc['filename']}")
        
        # Если всё еще не нашли - берем первый результат
        if not answer:
            answer = results[0]['text']
            if len(answer) > 200:
                sentences = re.split(r'[.!?]\s+', answer)
                if len(sentences) > 2:
                    answer = '. '.join(sentences[:2]) + '.'
                if len(answer) > 200:
                    answer = answer[:200] + '...'
            print(f"ℹ️ Взят первый результат из {results[0]['filename']}")
            source_doc = results[0]
        
        status = "answered"
        sources = [{
            "filename": r["filename"],
            "page": str(r.get("page", 1)),
            "excerpt": r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"],
            "score": r["score"]
        } for r in results[:3]]
    
    latency_ms = int((time.time() - start_time) * 1000)
    update_query_answer(query_id, answer, status, latency_ms, sources)
    
    return {
        "query_id": query_id,
        "question": question,
        "answer": answer,
        "status": status,
        "sources": sources,
        "latency_ms": latency_ms
    }