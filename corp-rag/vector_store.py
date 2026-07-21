import sqlite3
import json
import math
from embeddings import get_embedding, get_embeddings_batch

DB_PATH = "storage/app.db"


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_collection():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vector_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            page INTEGER DEFAULT 1,
            section TEXT DEFAULT '',
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            embedding_json TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("Таблица vector_chunks готова")


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

def upsert_chunks(doc_id, filename, chunks):
    if not chunks:
        return
    init_collection()
    delete_by_document_id(doc_id)

    texts = [chunk["text"] for chunk in chunks]
    vectors = get_embeddings_batch(texts)
    conn = get_conn()
    cursor = conn.cursor()

    for i, chunk in enumerate(chunks):
        cursor.execute("""
            INSERT INTO vector_chunks (
                document_id,
                filename,
                page,
                section,
                chunk_index,
                text,
                embedding_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id,
            filename,
            chunk.get("page", 1),
            chunk.get("section", ""),
            chunk.get("chunk_index", i),
            chunk["text"],
            json.dumps(vectors[i]),
        ))

    conn.commit()
    conn.close()
    print(f"Загружено {len(chunks)} чанков для документа {filename}")


def search(query, top_k=4, score_threshold=0.35):
    init_collection()
    query_vector = get_embedding(query)
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            document_id,
            filename,
            page,
            section,
            chunk_index,
            text,
            embedding_json
        FROM vector_chunks
    """)

    rows = cursor.fetchall()
    conn.close()
    scored = []
    for row in rows:
        embedding = json.loads(row[6])
        score = cosine_similarity(query_vector, embedding)

        if score >= score_threshold:
            scored.append({
                "document_id": row[0],
                "filename": row[1],
                "page": row[2],
                "section": row[3],
                "chunk_index": row[4],
                "text": row[5],
                "score": score,
            })

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]

def delete_by_document_id(doc_id):
    init_collection()
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM vector_chunks WHERE document_id = ?",
        (doc_id,)
    )

    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"Удалено чанков документа ID {doc_id}: {deleted}")
