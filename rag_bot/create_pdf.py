from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

c = canvas.Canvas("document.pdf", pagesize=A4)

texts = [
    ("Торговый центр 'Мега'", 800),
    ("Адрес: Москва, ул. Торговая, д. 1", 780),
    ("Телефон: +7 (495) 123-45-67", 760),
    ("График работы: 10:00 - 22:00", 740),
    ("Количество этажей: 3", 720),
]

for text, y in texts:
    c.drawString(100, y, text)

c.save()
print("PDF создан: document.pdf")