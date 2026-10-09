
import streamlit as st
from pypdf import PdfReader


def extract_text_from_pdf(uploaded_file):
    """อ่านข้อความจากไฟล์ PDF ที่ผู้ใช้อัปโหลด"""
    try:
        reader = PdfReader(uploaded_file)
        pages = []

        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                pages.append(text)

        result = "\n".join(pages).strip()

        if not result:
            raise ValueError(
                "ไม่พบข้อความใน PDF "
                "ไฟล์อาจเป็นภาพสแกนที่ต้องใช้ OCR"
            )

        return result

    except Exception as e:
        st.error(f"อ่าน PDF ไม่สำเร็จ: {e}")
        raise
