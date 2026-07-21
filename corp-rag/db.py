import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import threading

DB_PATH = "storage/app.db"
_db_lock = threading.Lock()

def init_db():
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                uploaded_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'uploaded',
                error TEXT,
                chunks_count INTEGER DEFAULT 0,
                file_path TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT,
                status TEXT NOT NULL DEFAULT 'processing',
                latency_ms INTEGER,
                created_at TEXT NOT NULL,
                sources_json TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS query_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER NOT NULL,
                document_id INTEGER,
                filename TEXT NOT NULL,
                page TEXT,
                section TEXT,
                excerpt TEXT,
                score REAL,
                FOREIGN KEY (query_id) REFERENCES queries(id) ON DELETE CASCADE,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK (rating IN (1, 0)),
                created_at TEXT NOT NULL,
                FOREIGN KEY (query_id) REFERENCES queries(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        conn.close()
        print("База данных инициализирована")

# === ДОКУМЕНТЫ ===

def add_document(filename: str, file_type: str, file_path: str) -> int:
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute("INSERT INTO documents (filename, file_type, uploaded_at, status, file_path) VALUES (?, ?, ?, 'uploaded', ?)", (filename, file_type, now, file_path))
        doc_id = c.lastrowid
        conn.commit()
        conn.close()
        return doc_id

def update_document_status(doc_id: int, status: str, error: str = None, chunks_count: int = None):
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if chunks_count is not None:
            c.execute("UPDATE documents SET status = ?, error = ?, chunks_count = ? WHERE id = ?", (status, error, chunks_count, doc_id))
        else:
            c.execute("UPDATE documents SET status = ?, error = ? WHERE id = ?", (status, error, doc_id))
        conn.commit()
        conn.close()

def get_all_documents():
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, filename, file_type, uploaded_at, status, error, chunks_count, file_path FROM documents ORDER BY uploaded_at DESC")
        rows = c.fetchall()
        conn.close()
        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "filename": row[1],
                "file_type": row[2],
                "uploaded_at": row[3],
                "status": row[4],
                "error": row[5],
                "chunks_count": row[6],
                "file_path": row[7]
            })
        return result

def get_document(doc_id: int):
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, filename, file_type, uploaded_at, status, error, chunks_count, file_path FROM documents WHERE id = ?", (doc_id,))
        row = c.fetchone()
        conn.close()
        if row is None:
            return None
        return {
            "id": row[0],
            "filename": row[1],
            "file_type": row[2],
            "uploaded_at": row[3],
            "status": row[4],
            "error": row[5],
            "chunks_count": row[6],
            "file_path": row[7]
        }

def delete_document(doc_id: int) -> bool:
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        deleted = c.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

# === ЗАПРОСЫ ===

def add_query(question: str, status: str = 'processing') -> int:
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute("INSERT INTO queries (question, status, created_at) VALUES (?, ?, ?)", (question, status, now))
        qid = c.lastrowid
        conn.commit()
        conn.close()
        return qid

def update_query_answer(query_id: int, answer: str, status: str, latency_ms: int, sources: List[Dict]):
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        sources_json = json.dumps(sources, ensure_ascii=False)
        c.execute("UPDATE queries SET answer = ?, status = ?, latency_ms = ?, sources_json = ? WHERE id = ?", (answer, status, latency_ms, sources_json, query_id))
        for src in sources:
            c.execute("""
                INSERT INTO query_sources (query_id, document_id, filename, page, section, excerpt, score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (query_id, src.get('document_id'), src.get('filename', ''), src.get('page', ''), src.get('section', ''), src.get('excerpt', ''), src.get('score', 0.0)))
        conn.commit()
        conn.close()

def get_all_queries():
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, question, answer, status, latency_ms, created_at, sources_json FROM queries ORDER BY created_at DESC")
        rows = c.fetchall()
        conn.close()
        result = []
        for row in rows:
            sources = json.loads(row[6]) if row[6] else []
            result.append({
                "id": row[0],
                "question": row[1],
                "answer": row[2],
                "status": row[3],
                "latency_ms": row[4],
                "created_at": row[5],
                "sources": sources
            })
        return result

# === ОБРАТНАЯ СВЯЗЬ ===

def add_feedback(query_id: int, rating: int):
    with _db_lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute("INSERT INTO feedback (query_id, rating, created_at) VALUES (?, ?, ?)", (query_id, rating, now))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    init_db()
