# chunking.py - исправленная версия с правильным разбиением на чанки

import re
from typing import List, Dict

def chunk_document(parsed_content, chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
    """
    Разбивает документ на чанки с перекрытием
    
    Args:
        parsed_content: список элементов (текст или словари)
        chunk_size: максимальный размер чанка в символах
        overlap: перекрытие между чанками
    
    Returns:
        Список чанков с метаданными
    """
    chunks = []
    
    # Собираем весь текст
    full_text = ""
    if isinstance(parsed_content, list):
        for item in parsed_content:
            if isinstance(item, dict):
                full_text += item.get('text', '') + "\n"
            elif isinstance(item, str):
                full_text += item + "\n"
    elif isinstance(parsed_content, str):
        full_text = parsed_content
    else:
        full_text = str(parsed_content)
    
    # Разбиваем на предложения
    sentences = re.split(r'(?<=[.!?])\s+', full_text)
    
    # Если текст маленький, возвращаем один чанк
    if len(full_text) <= chunk_size:
        chunks.append({
            "chunk_index": 0,
            "text": full_text.strip(),
            "page": 1,
            "section": ""
        })
        return chunks
    
    # Разбиваем на чанки с перекрытием
    current_chunk = []
    current_size = 0
    chunk_index = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        sentence_len = len(sentence)
        
        # Если предложение слишком большое, разбиваем его
        if sentence_len > chunk_size:
            # Разбиваем по словам
            words = sentence.split()
            temp_chunk = []
            temp_size = 0
            
            for word in words:
                if temp_size + len(word) + 1 > chunk_size:
                    if temp_chunk:
                        chunks.append({
                            "chunk_index": chunk_index,
                            "text": ' '.join(temp_chunk).strip(),
                            "page": 1,
                            "section": ""
                        })
                        chunk_index += 1
                        # Сохраняем последние слова для перекрытия
                        overlap_words = temp_chunk[-min(overlap // 10, len(temp_chunk)):]
                        temp_chunk = overlap_words.copy()
                        temp_size = sum(len(w) + 1 for w in temp_chunk)
                    
                    temp_chunk.append(word)
                    temp_size += len(word) + 1
                else:
                    temp_chunk.append(word)
                    temp_size += len(word) + 1
            
            if temp_chunk:
                chunks.append({
                    "chunk_index": chunk_index,
                    "text": ' '.join(temp_chunk).strip(),
                    "page": 1,
                    "section": ""
                })
                chunk_index += 1
            continue
        
        # Добавляем предложение к текущему чанку
        if current_size + sentence_len + 1 > chunk_size and current_chunk:
            # Сохраняем текущий чанк
            chunks.append({
                "chunk_index": chunk_index,
                "text": ' '.join(current_chunk).strip(),
                "page": 1,
                "section": ""
            })
            chunk_index += 1
            
            # Сохраняем последние предложения для перекрытия
            overlap_sentences = []
            overlap_size = 0
            for s in reversed(current_chunk):
                if overlap_size + len(s) + 1 <= overlap:
                    overlap_sentences.insert(0, s)
                    overlap_size += len(s) + 1
                else:
                    break
            
            current_chunk = overlap_sentences
            current_size = overlap_size
        
        current_chunk.append(sentence)
        current_size += sentence_len + 1
    
    # Добавляем последний чанк
    if current_chunk:
        chunks.append({
            "chunk_index": chunk_index,
            "text": ' '.join(current_chunk).strip(),
            "page": 1,
            "section": ""
        })
    
    return chunks

def chunk_by_qa_pairs(text: str) -> List[Dict]:
    """
    Специальное разбиение для Q&A документов - каждый Q&A пара становится отдельным чанком
    """
    chunks = []
    
    # Ищем Q&A пары
    qa_pattern = re.compile(
        r'(?:Вопрос|Q)\s*[:;]\s*(.+?)(?:\n|\s*?)(?:Ответ|A)\s*[:;]\s*(.+?)(?=\n\s*(?:Вопрос|Q|$))',
        re.IGNORECASE | re.DOTALL
    )
    
    matches = list(qa_pattern.finditer(text))
    
    if matches:
        for i, match in enumerate(matches):
            question = match.group(1).strip()
            answer = match.group(2).strip()
            
            chunk_text = f"Вопрос: {question}\nОтвет: {answer}"
            
            chunks.append({
                "chunk_index": i,
                "text": chunk_text,
                "page": 1,
                "section": "Q&A",
                "question": question,
                "answer": answer
            })
        
        return chunks
    
    # Если нет Q&A, используем обычное разбиение
    return chunk_document([text])

def chunk_document_smart(parsed_content) -> List[Dict]:
    """
    Умное разбиение документов с учетом формата
    """
    # Собираем текст
    full_text = ""
    if isinstance(parsed_content, list):
        for item in parsed_content:
            if isinstance(item, dict):
                full_text += item.get('text', '') + "\n"
            elif isinstance(item, str):
                full_text += item + "\n"
    elif isinstance(parsed_content, str):
        full_text = parsed_content
    else:
        full_text = str(parsed_content)
    
    # Проверяем, есть ли Q&A формат
    if 'Вопрос:' in full_text and 'Ответ:' in full_text:
        print("📋 Обнаружен Q&A формат, разбиение по парам")
        return chunk_by_qa_pairs(full_text)
    
    # Иначе обычное разбиение
    print("📄 Обычный формат, разбиение по размеру")
    return chunk_document([full_text], chunk_size=800, overlap=100)

# Для обратной совместимости
def chunk_document(parsed_content) -> List[Dict]:
    return chunk_document_smart(parsed_content)