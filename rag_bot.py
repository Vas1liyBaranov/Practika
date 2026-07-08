import os
import json
import hashlib
import time
from openai import OpenAI
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

load_dotenv()

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
    timeout=60,
    max_retries=3,
)

qdrant = QdrantClient(":memory:")

COLLECTION = "docs"
EMBED_MODEL = "text-embedding-ada-002"
VECTOR_SIZE = 1536


def embed(texts: list[str]) -> list[list[float]]:
    try:
        resp = client.embeddings.create(
            model=EMBED_MODEL,
            input=texts
        )
        return [item.embedding for item in resp.data]
    except Exception as e:
        print(f"❌ Ошибка эмбеддинга: {e}")
        time.sleep(3)
        raise


def load_docs(folder: str) -> list[tuple[str, str]]:
    docs = []
    for filename in os.listdir(folder):
        if filename.endswith((".txt", ".md")):
            path = os.path.join(folder, filename)
            with open(path, "r", encoding="utf-8") as file:
                docs.append((filename, file.read()))
    return docs


def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def index_docs(docs: list[tuple[str, str]]):
    if not docs:
        raise ValueError("Папка docs пустая")

    if qdrant.collection_exists(COLLECTION):
        qdrant.delete_collection(COLLECTION)

    qdrant.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE
        )
    )

    all_chunks = []
    for filename, content in docs:
        for i, chunk in enumerate(chunk_text(content)):
            all_chunks.append({
                "source": filename,
                "chunk_id": i,
                "text": chunk,
            })

    print(f"  Создание {len(all_chunks)} эмбеддингов...")
    vectors = embed([item["text"] for item in all_chunks])

    points = []
    for item, vector in zip(all_chunks, vectors):
        raw_id = f"{item['source']}_{item['chunk_id']}"
        point_id = int(hashlib.md5(raw_id.encode()).hexdigest()[:16], 16)
        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload=item
            )
        )

    qdrant.upsert(collection_name=COLLECTION, points=points)
    print(f"✅ Загружено {len(points)} кусков из {len(docs)} документов")


def search(query: str, top_k: int = 3) -> list[dict]:
    query_vector = embed([query])[0]
    results = qdrant.query_points(
        collection_name=COLLECTION,
        query=query_vector,
        limit=top_k
    ).points
    return [
        {"source": r.payload["source"], "text": r.payload["text"], "score": r.score}
        for r in results
    ]


def answer(query: str, retries: int = 3) -> dict:
    results = search(query)

    if not results or results[0]["score"] < 0.35:
        return {
            "answer": "Я не знаю. В документах нет информации по этому вопросу.",
            "sources": [],
            "score": 0,
        }

    context = "\n\n".join(f"[{r['source']}] {r['text']}" for r in results)

    prompt = f"""
Ты помощник по документам.

Отвечай только по тексту из блока "Документы".
Если ответа нет в документах, скажи: "Я не знаю. В документах нет информации по этому вопросу."
В конце укажи источник.

Документы:
{context}

Вопрос:
{query}
"""

    for attempt in range(retries):
        try:
            resp = client.chat.completions.create(
                model="google/gemma-4-26b-a4b-it:free",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300,
            )
            
            return {
                "answer": resp.choices[0].message.content,
                "sources": list(dict.fromkeys(r["source"] for r in results)),
                "score": results[0]["score"],
            }
        except Exception as e:
            print(f"  ⚠️ Попытка {attempt+1}/{retries} не удалась: {str(e)[:80]}")
            if attempt < retries - 1:
                time.sleep(5)
            else:
                return {
                    "answer": f"❌ Ошибка: {str(e)[:100]}",
                    "sources": [],
                    "score": 0,
                }


if __name__ == "__main__":
    docs = load_docs("docs")

    for name, content in docs:
        print(f"{name}: {len(content)} символов")

    index_docs(docs)

    questions = [
        "Сколько стоит аренда на 1 этаже?",
        "Какой телефон у управляющей компании?",
        "Когда открылся торговый центр?",
        "Есть ли кинотеатр?",
        "Сколько стоит аренда на 5 этаже?",
        "Какой адрес?",
    ]

    for question in questions:
        print(f"\n❓ {question}")
        result = answer(question)
        print(f"📌 {result['answer']}")
        if result["sources"]:
            print(f"📁 Источник: {', '.join(result['sources'])}")
            print(f"📊 Score: {result['score']:.3f}")
