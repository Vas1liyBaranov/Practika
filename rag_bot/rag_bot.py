import os
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
    max_retries=2,)

qdrant = QdrantClient(":memory:")
COLLECTION = "docs"
EMBED_MODEL = "text-embedding-ada-002"
VECTOR_SIZE = 1536
CHAT_MODEL = "google/gemma-4-26b-a4b-it:free"

def embed(texts):
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=texts,)
    return [item.embedding for item in response.data]

def load_docs(folder):
    docs = []
    for filename in os.listdir(folder):
        if filename.endswith((".txt", ".md")):
            path = os.path.join(folder, filename)
            with open(path, "r", encoding="utf-8") as file:
                docs.append((filename, file.read()))
    return docs

def chunk_text(text, chunk_size=300, overlap=50):
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i:i + chunk_size]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks

def index_docs(docs):
    if not docs:
        raise ValueError("Папка docs пустая")
    if qdrant.collection_exists(COLLECTION):
        qdrant.delete_collection(COLLECTION)
    qdrant.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,),)
    chunks = []
    for filename, content in docs:
        for chunk_id, chunk in enumerate(chunk_text(content)):
            chunks.append({
                "source": filename,
                "chunk_id": chunk_id,
                "text": chunk,})

    print(f"Создание эмбеддингов: {len(chunks)}")
    vectors = embed([chunk["text"] for chunk in chunks])
    points = []
    for chunk, vector in zip(chunks, vectors):
        raw_id = f"{chunk['source']}_{chunk['chunk_id']}"
        point_id = int(hashlib.md5(raw_id.encode()).hexdigest()[:16], 16)
        points.append(
            PointStruct(id=point_id, vector=vector, payload=chunk,))
    qdrant.upsert(collection_name=COLLECTION, points=points,)
    print(f"Загружено кусков: {len(points)}")
    print(f"Документов: {len(docs)}")

def search(query, top_k=3):
    query_vector = embed([query])[0]
    results = qdrant.query_points(collection_name=COLLECTION, query=query_vector, limit=top_k, ).points
    return [
        {
            "source": item.payload["source"],
            "chunk_id": item.payload["chunk_id"],
            "text": item.payload["text"],
            "score": item.score,
        }
        for item in results
    ]
def ask_llm(prompt, retries=2):
    last_error = None
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=CHAT_MODEL,
                messages=[ {"role": "user", "content": prompt} ],
                temperature=0.1,
                max_tokens=300,)

            return response.choices[0].message.content
        except Exception as error:
            last_error = error
            print(f"Попытка {attempt + 1}/{retries}: {str(error)[:180]}")
            if attempt < retries - 1:
                time.sleep(5)
    return f"Не удалось получить ответ от модели. Ошибка: {str(last_error)[:200]}"

def answer(query):
    results = search(query)
    if not results or results[0]["score"] < 0.35:
        return {
            "answer": "Я не знаю. В документах нет информации по этому вопросу.",
            "sources": [],
            "score": 0,
        }

    context = "\n\n".join(
        f"[{item['source']}, chunk {item['chunk_id']}]\n{item['text']}"
        for item in results
    )
    prompt = f"""
Ты помощник по документам.

Отвечай только по информации из блока "Документы".
Если ответа нет в документах, скажи: "Я не знаю. В документах нет информации по этому вопросу."
Ответ должен быть кратким.
В конце укажи источник.

Документы:
{context}

Вопрос:
{query}
"""
    text = ask_llm(prompt)
    return {
        "answer": text,
        "sources": list(dict.fromkeys(item["source"] for item in results)),
        "score": results[0]["score"],
    }
def main():
    docs = load_docs("docs")
    print("Загрузка документов")
    for filename, content in docs:
        print(f"{filename}: {len(content)} символов")
    index_docs(docs)
    questions = [
        "Сколько стоит аренда на 1 этаже?",
        "Какой телефон у управляющей компании?",
        "Когда открылся торговый центр?",
        "Есть ли кинотеатр?",
        "Сколько стоит аренда на 5 этаже?",
        "Какой адрес?",
    ]
    print("\nТестовые вопросы")

    for question in questions:
        print(f"\nВопрос: {question}")
        result = answer(question)
        print(f"Ответ: {result['answer']}")
        if result["sources"]:
            print(f"Источник: {', '.join(result['sources'])}")
            print(f"Score: {result['score']:.3f}")
            
if __name__ == "__main__":
    main()
