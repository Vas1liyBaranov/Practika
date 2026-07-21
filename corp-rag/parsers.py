import os
import fitz  # PyMuPDF для PDF
from docx import Document  # python-docx для DOCX

def parse_pdf(file_path: str) -> list[dict]:
    """
    Извлекает текст из PDF постранично.
    Возвращает список: [{"page": 1, "text": "..."}, ...]
    """
    doc = fitz.open(file_path)
    result = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            result.append({
                "page": page_num + 1,
                "text": text.strip()
            })
    doc.close()
    return result

def parse_docx(file_path: str) -> list[dict]:
    """
    Извлекает текст из DOCX по параграфам.
    Возвращает список: [{"section": "параграф 1", "text": "..."}, ...]
    """
    doc = Document(file_path)
    result = []
    for i, para in enumerate(doc.paragraphs):
        if para.text.strip():
            result.append({
                "section": f"параграф {i+1}",
                "text": para.text.strip()
            })
    return result

def parse_txt(file_path: str) -> list[dict]:
    """
    Извлекает текст из TXT или MD.
    Возвращает: [{"page": 1, "text": "..."}]
    """
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return [{"page": 1, "text": text.strip()}]

def parse_file(file_path: str) -> tuple[str, list[dict]]:
    """
    Определяет тип файла по расширению и вызывает нужный парсер.
    Возвращает: (file_type, parsed_content)
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        return "pdf", parse_pdf(file_path)
    elif ext == ".docx":
        return "docx", parse_docx(file_path)
    elif ext in (".txt", ".md"):
        return "text", parse_txt(file_path)
    else:
        raise ValueError(f"Неподдерживаемый формат: {ext}")
