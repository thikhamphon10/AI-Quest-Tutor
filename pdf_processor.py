import re
from pypdf import PdfReader


def clean_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text(file) -> str:
    try:
        reader = PdfReader(file)
        raw = "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception:
        raise ValueError("อ่านไฟล์ PDF ไม่ได้ ไฟล์อาจเสียหรือมีรหัสผ่าน ลองไฟล์อื่นหรือใช้ Paste Notes แทน")
    text = clean_text(raw)
    if len(text) < 50:
        raise ValueError("PDF นี้ไม่มีข้อความที่อ่านได้ (อาจเป็นรูปสแกน) ระบบยังไม่รองรับ OCR ลองวางเนื้อหาแทน")
    return text
