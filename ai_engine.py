import os
import json
import time
import re
from google import genai
from google.genai import types
from google.genai.errors import APIError

# ชื่อโมเดล Gemini: เปลี่ยนได้โดยตั้งค่า GEMINI_MODEL ใน Secrets/Environment (ไม่ต้องแก้โค้ด)
# gemini-2.5-flash ถูกยกเลิกสำหรับผู้ใช้ใหม่แล้ว (404 NOT_FOUND) จึงใช้ gemini-3.8-flash เป็นค่าเริ่มต้น
DEFAULT_MODEL = "gemini-3.8-flash"


def get_model_name() -> str:
    name = os.getenv("GEMINI_MODEL")
    if not name:
        try:
            import streamlit as st
            name = st.secrets.get("GEMINI_MODEL")
        except Exception:
            name = None
    return str(name).strip() if name else DEFAULT_MODEL


# ข้อความข้อผิดพลาดล่าสุดจากการสร้างข้อสอบ (ให้หน้าเว็บแสดงสาเหตุจริง ไม่เหมารวมว่าโควตาเต็ม)
last_error = ""


def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            if "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass
            
    if not api_key:
        raise ValueError("ไม่พบ GEMINI_API_KEY ใน Environment Variables หรือ Streamlit Secrets")
    
    return genai.Client(api_key=api_key)

def clean_json_response(text: str) -> str:
    text = text.strip()
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    return text

def _call_gemini_with_retry(client, prompt: str, max_retries: int = 3) -> str:
    model_name = get_model_name()
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    response_mime_type="application/json"
                )
            )
            return response.text
        except APIError as e:
            error_str = str(e).lower()
            if "404" in error_str or "not_found" in error_str:
                # โมเดลไม่มี/ถูกยกเลิก: ลองซ้ำไม่ช่วย แจ้งวิธีแก้ทันที
                raise Exception(f"ไม่พบโมเดล Gemini ‘{model_name}’ (อาจถูกยกเลิก) กรุณาตั้งค่า GEMINI_MODEL ใน Secrets เป็นโมเดลที่ใช้ได้ เช่น {DEFAULT_MODEL} — รายละเอียด: {str(e)[:150]}")
            if "429" in error_str or "resource_exhausted" in error_str or "quota" in error_str:
                # แจ้ง Error 429 แบบชัดเจนเพื่อหยุด Batch
                raise Exception("QUOTA_EXHAUSTED: โควตาการใช้งาน Gemini API หมดแล้ว กรุณาลองใหม่ในภายหลังหรือใช้ชุดข้อสอบที่บันทึกไว้")
            
            # หากเป็น Error ชั่วคราว (เช่น 503 Server Overloaded) ให้ทำ Exponential Backoff
            if attempt < max_retries - 1:
                sleep_time = (2 ** attempt) + 1
                time.sleep(sleep_time)
            else:
                raise Exception(f"เกิดข้อผิดพลาดในการเชื่อมต่อกับ Gemini API: {str(e)}")
        except Exception as e:
            if "429" in str(e) or "resource_exhausted" in str(e).lower():
                raise Exception("QUOTA_EXHAUSTED: โควตาการใช้งาน Gemini API หมดแล้ว กรุณาลองใหม่ในภายหลังหรือใช้ชุดข้อสอบที่บันทึกไว้")
            raise e

def generate_questions_batch(text_content: str, difficulty: str, batch_size: int = 5, emphasis: str = "") -> list:
    client = get_client()
    emphasis = (emphasis or "").strip()[:200]
    focus_line = f"\n    [หัวข้อที่ต้องเน้นเป็นพิเศษ (เฉพาะส่วนที่มีในเนื้อหา)]: {emphasis}" if emphasis else ""
    
    prompt = f"""
    คุณเป็นอาจารย์ผู้ออกข้อสอบมืออาชีพ ให้สร้างข้อสอบปรนัยจำนวน {batch_size} ข้อ จากเนื้อหาต่อไปนี้
    
    [ระดับความยาก]: {difficulty}{focus_line}
    [เนื้อหา]:
    {text_content[:12000]}
    
    ตอบกลับในรูปแบบ JSON Array เท่านั้น ห้ามใส่ข้อความอื่นนอกเหนือจาก JSON:
    [
      {{
        "question": "คำถาม?",
        "options": ["ตัวเลือก A", "ตัวเลือก B", "ตัวเลือก C", "ตัวเลือก D"],
        "answer": "คำตอบที่ถูกต้องตรงกับ 1 ใน options",
        "explanation": "คำอธิบายเฉลยสั้นๆ",
        "topic": "หัวข้อย่อยของข้อนี้ สั้นๆ 1-4 คำ"
      }}
    ]
    """
    
    raw_response = _call_gemini_with_retry(client, prompt)
    cleaned = clean_json_response(raw_response)
    
    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return data
        return []
    except json.JSONDecodeError:
        return []

def generate_questions_from_text(text_content: str, difficulty: str = "ปานกลาง", total_questions: int = 5, emphasis: str = ""):
    """
    สร้างข้อสอบตามจำนวนที่ต้องการ โดยแบ่งเป็น Batch ละ 5 ข้อ
    ป้องกันปัญหา Timeout/Quota Exhausted และตัดข้อสอบที่ซ้ำออก
    """
    global last_error
    last_error = ""
    all_questions = []
    seen_questions = set()
    
    # แบ่งจำนวนการขอออกเป็น Batch ย่อย ละไม่เกิน 5 ข้อ
    batch_size = 5
    remaining = total_questions
    stalls = 0  # กันวนไม่จบเมื่อ AI ตอบซ้ำจนไม่มีข้อใหม่
    
    while remaining > 0 and stalls < 3:
        current_batch_count = min(batch_size, remaining)
        try:
            batch_result = generate_questions_batch(text_content, difficulty, current_batch_count, emphasis)
            
            if not batch_result:
                break
                
            new_added = 0
            for q in batch_result:
                q_text = q.get("question", "").strip()
                if q_text and q_text not in seen_questions:
                    seen_questions.add(q_text)
                    all_questions.append(q)
                    new_added += 1
            
            # หักลบจำนวนที่สร้างสำเร็จจริง
            remaining -= new_added
            stalls = stalls + 1 if new_added == 0 else 0
            
            # ชะลอการเรียก API เล็กน้อยเพื่อถนอม Rate Limit
            time.sleep(1)
            
        except Exception as e:
            last_error = str(e)
            if "QUOTA_EXHAUSTED" in str(e):
                # หากโควตาหมด ให้คืนค่าเท่าที่สร้างได้จริงทันที
                print("Gemini Quota Exhausted: Returning generated questions so far.")
                break
            else:
                # กรณี Error อื่นๆ ให้หยุดแล้วส่งคืนข้อสอบที่สร้างได้ก่อนหน้า
                break
                
    return all_questions[:total_questions]
