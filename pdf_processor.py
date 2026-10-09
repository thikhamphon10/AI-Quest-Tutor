import pypdf
import io

def extract_text_from_pdf(pdf_file) -> str:
    """
    ดึงข้อความทั้งหมดออกจากไฟล์ PDF
    รองรับทั้งการรับไฟล์ผ่าน st.file_uploader (BytesIO) และ file path
    """
    text = ""
    try:
        # หากไฟล์ส่งมาจาก Streamlit file_uploader จะเป็น BytesIO หรือ UploadedFile
        if hasattr(pdf_file, "read"):
            pdf_bytes = pdf_file.read()
            # Reset pointer ของไฟล์เพื่อความปลอดภัยหากต้องนำไปใช้อื่นๆ
            if hasattr(pdf_file, "seek"):
                pdf_file.seek(0)
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        else:
            reader = pypdf.PdfReader(pdf_file)

        # วนลูปอ่านข้อความจากทุกหน้า
        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- หน้า {page_idx + 1} ---\n" + page_text

    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการอ่านไฟล์ PDF: {str(e)}")
        return ""

    return text.strip()
