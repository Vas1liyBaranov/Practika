import os
import sqlite3
from db import init_db, add_document, update_document_status, get_all_documents, delete_document
from parsers import parse_file
from chunking import chunk_document
from vector_store import init_collection, upsert_chunks, delete_by_document_id
from embeddings import clear_cache

def reindex_all():
    print("Переиндексация документов с моделью nomic-embed-text...")
    print("=" * 60)
    
    # Очищаем кэш эмбеддингов
    clear_cache()
    
    # Инициализируем базу
    init_db()
    init_collection()
    
    # Получаем все документы
    docs = get_all_documents()
    print(f"Найдено документов: {len(docs)}")
    
    if not docs:
        print("Нет документов для индексации!")
        print("Загрузите документы через веб-интерфейс и запустите снова.")
        return
    
    for doc in docs:
        print(f"\nОбработка: {doc['filename']}")
        print(f"   ID: {doc['id']}, статус: {doc['status']}")
        
        # Удаляем старые чанки
        delete_by_document_id(doc['id'])
        
        # Проверяем, существует ли файл
        if not os.path.exists(doc['file_path']):
            print(f"  Файл не найден: {doc['file_path']}")
            continue
        
        try:
            # Парсим файл
            print(f"  Чтение файла...")
            file_type, parsed = parse_file(doc['file_path'])
            print(f"  Тип: {file_type}, размер: {len(parsed)} символов")
            
            # Разбиваем на чанки
            chunks = chunk_document(parsed)
            print(f"  Создано {len(chunks)} чанков")
            
            if not chunks:
                print(f"  Нет чанков для индексации")
                continue
            
            # Индексируем
            print(f"  Индексация с nomic-embed-text...")
            upsert_chunks(doc['id'], doc['filename'], chunks)
            update_document_status(doc['id'], "indexed", chunks_count=len(chunks))
            
            print(f"  {doc['filename']} проиндексирован ({len(chunks)} чанков)")
            
        except Exception as e:
            print(f"  Ошибка: {e}")
            update_document_status(doc['id'], "error", str(e))
    
    # Проверяем результат
    print("\n" + "=" * 60)
    conn = sqlite3.connect('storage/app.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM vector_chunks')
    count = cursor.fetchone()[0]
    print(f"Всего чанков в базе: {count}")
    conn.close()
    
    print("\nПереиндексация завершена!")

if __name__ == "__main__":
    reindex_all()
