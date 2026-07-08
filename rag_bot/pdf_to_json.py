import os
import json
import base64
import fitz
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
    timeout=90,
    max_retries=2,
)

VISION_MODEL = "google/gemma-4-26b-a4b-it:free"

def pdf_pages_to_images(pdf_path, max_pages=3):
    doc = fitz.open(pdf_path)
    images = []
    for page_index in range(min(len(doc), max_pages)):
        page = doc[page_index]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        image_bytes = pix.tobytes("png")
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        images.append(f"data:image/png;base64,{image_base64}")
    return images


def clean_json_text(text):
    text = text.strip()
    if text.startswith("```json"):
        text = text.replace("```json", "", 1).strip()
    if text.startswith("```"):
        text = text.replace("```", "", 1).strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text


def extract_pdf_to_json(pdf_path):
    images = pdf_pages_to_images(pdf_path)
    content = [
        {
            "type": "text",
            "text": """
Извлеки данные из PDF в JSON.

Верни только JSON без markdown.

Формат:
{
  "title": "",
  "summary": "",
  "fields": {
    "organization": "",
    "address": "",
    "phone": "",
    "date": ""
  },
  "tables": [
    {
      "title": "",
      "columns": [],
      "rows": []
    }
  ]
}

Если поля нет в документе, ставь null.
"""
        }
    ]

    for image in images:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": image
            }
        })

    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
        temperature=0,
        max_tokens=1500,
    )

    text = response.choices[0].message.content
    text = clean_json_text(text)

    return json.loads(text)


def main():
    pdf_path = "document.pdf"

    result = extract_pdf_to_json(pdf_path)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()