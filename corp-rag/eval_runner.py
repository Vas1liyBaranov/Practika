import json
import time
from rag import ask
from db import get_all_documents

def run_eval():
    print("="*60)
    print("ЗАПУСК EVAL-НАБОРА")
    print("="*60)
    
    # Загружаем вопросы
    with open("eval/questions.jsonl", "r", encoding="utf-8") as f:
        questions = [json.loads(line) for line in f if line.strip()]
    
    print(f"Всего вопросов: {len(questions)}")
    
    results = []
    covered = 0
    not_found = 0
    ambiguous = 0
    citation_count = 0
    
    for q in questions:
        print(f"\n❓ {q['id']}: {q['question']}")
        print(f"   Ожидается: {q['expected']}")
        
        start = time.time()
        answer = ask(q['question'])
        elapsed = time.time() - start
        
        has_source = len(answer.get('sources', [])) > 0
        
        # Проверка
        if q['expected'] == 'covered':
            if has_source:
                covered += 1
                citation_count += 1
                status = "✅ OK (есть источник)"
            else:
                status = "❌ ОШИБКА (нет источника)"
        elif q['expected'] == 'not_found':
            if not has_source and "не найдена" in answer['answer']:
                not_found += 1
                status = "✅ OK (честный отказ)"
            else:
                status = "❌ ОШИБКА (должен быть отказ)"
        else:
            ambiguous += 1
            status = "⚠️ Смешанный"
        
        print(f"   Результат: {status}")
        print(f"   Время: {elapsed:.2f} сек")
        print(f"   Источники: {len(answer.get('sources', []))}")
        
        results.append({
            "id": q['id'],
            "question": q['question'],
            "expected": q['expected'],
            "status": status,
            "sources": len(answer.get('sources', [])),
            "time": elapsed,
            "answer": answer.get('answer', '')[:200]
        })
    
    # --- ОТЧЁТ ---
    total = len(questions)
    print("\n" + "="*60)
    print("ОТЧЁТ ПО EVAL-НАБОРУ")
    print("="*60)
    print(f"Всего вопросов: {total}")
    print(f"✅ Покрытых с источниками: {covered}")
    print(f"✅ Честных отказов: {not_found}")
    print(f"⚠️ Смешанных/неоднозначных: {ambiguous}")
    
    citation_rate = covered / total if total > 0 else 0
    print(f"\n📊 Полнота цитирования: {citation_rate:.1%}")
    
    # Сохраняем отчёт
    report = {
        "total": total,
        "covered": covered,
        "not_found": not_found,
        "ambiguous": ambiguous,
        "citation_rate": citation_rate,
        "results": results
    }
    
    with open("reports/eval-results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n📁 Отчёт сохранён в reports/eval-results.json")
    
    return report

if __name__ == "__main__":
    run_eval()
