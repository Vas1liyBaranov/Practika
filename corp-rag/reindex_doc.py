# reindex_doc.py - обновленная версия

import os
from parsers import parse_file
from chunking import chunk_document_smart  # Используем новую функцию
from vector_store import upsert_chunks, delete_by_document_id
from db import get_all_documents, update_document_status

def reindex_document(filename_pattern):
    """Переиндексирует документ по части имени"""
    
    docs = get_all_documents()
    
    found = False
    for doc in docs:
        if filename_pattern.lower() in doc['filename'].lower():
            found = True
            print(f"📄 Найден документ: {doc['filename']}")
            print(f"   ID: {doc['id']}")
            print(f"   Статус: {doc['status']}")
            print(f"   Путь: {doc['file_path']}")
            print(f"   Чанков: {doc['chunks_count']}")
            
            if not os.path.exists(doc['file_path']):
                print(f"❌ Файл не найден: {doc['file_path']}")
                continue
            
            print("\n🔄 Переиндексация...")
            
            try:
                # Удаляем старые чанки
                delete_by_document_id(doc['id'])
                print(f"✅ Старые чанки удалены")
                
                # Парсим файл
                file_type, parsed = parse_file(doc['file_path'])
                print(f"✅ Файл распарсен: {file_type}, {len(parsed)} элементов")
                
                # Создаем чанки с умным разбиением
                chunks = chunk_document_smart(parsed)
                print(f"✅ Создано {len(chunks)} чанков")
                
                if chunks:
                    # Показываем первые несколько чанков
                    print("\n📋 Первые 3 чанка:")
                    for i, chunk in enumerate(chunks[:3]):
                        print(f"  Чанк {i+1}: {chunk['text'][:100]}...")
                        if 'депозит' in chunk['text'].lower():
                            print("    ✅ Содержит 'депозит'!")
                    
                    # Загружаем чанки
                    upsert_chunks(doc['id'], doc['filename'], chunks)
                    
                    # Обновляем статус
                    update_document_status(doc['id'], "indexed", chunks_count=len(chunks))
                    print(f"\n✅ Переиндексировано {len(chunks)} чанков")
                else:
                    print("❌ Нет чанков для загрузки")
                    update_document_status(doc['id'], "error", "Нет чанков")
                
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                import traceback
                traceback.print_exc()
                update_document_status(doc['id'], "error", str(e))
            
            break
    
    if not found:
        print(f"❌ Документ с '{filename_pattern}' не найден")
        print("\nДоступные документы:")
        for doc in docs:
            print(f"  - {doc['filename']} (ID: {doc['id']})")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Использование: python reindex_doc.py <часть_имени_файла>")
        sys.exit(1)
    
    reindex_document(sys.argv[1])