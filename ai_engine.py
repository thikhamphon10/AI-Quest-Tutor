
import json
import os
import time

import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel


MODEL = "gemini-3.8-flash"
MAX_CHARS = 30000
MAX_ATTEMPTS = 3

REWARD = {
    "easy": (15, 10),
    "medium": (20, 15),
    "hard": (30, 25),
}


class AIError(Exception):
    pass


class QuestionSchema(BaseModel):
    question: str
    choices: list[str]
    correct_answer: str
    explanation: str
    topic: str
    difficulty: str


def _get_api_key():
    """อ่าน API Key จาก Environment หรือ Streamlit Secrets"""
    key = os.getenv("GEMINI_API_KEY")

    if not key:
        try:
            key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            key = None

    if not key or not str(key).strip():
        raise AIError(
            "ไม่พบ GEMINI_API_KEY กรุณาตั้งค่าใน "
            "Streamlit Community Cloud > Settings > Secrets"
        )

    return str(key).strip()


def _call(prompt: str, schema=None) -> str:
    """เรียก Gemini พร้อมลองใหม่เมื่อเกิดข้อผิดพลาดชั่วคราว"""

    try:
        key = _get_api_key()
    except AIError:
        raise

    config_args = {
        "response_mime_type": (
            "application/json" if schema else "text/plain"
        ),
    }

    if schema is not None:
        config_args["response_schema"] = schema

    try:
        config = types.GenerateContentConfig(**config_args)
    except Exception as e:
        raise AIError(
            f"ตั้งค่า Gemini ไม่สำเร็จ: "
            f"{type(e).__name__}: {str(e)[:300]}"
        ) from e

    last_error = None

    for attempt in range(MAX_ATTEMPTS):
        try:
            # สร้าง Client ใหม่สำหรับแต่ละคำขอ
            with genai.Client(api_key=key) as client:
                response = client.models.generate_content(
                    model=MODEL,
                    contents=prompt,
                    config=config,
                )

            if not response.text:
                raise AIError(
                    "Gemini ส่งคำตอบว่างกลับมา กรุณาลองใหม่"
                )

            return response.text

        except AIError:
            raise

        except Exception as e:
            last_error = e
            message = str(e).upper()

            temporary_error = any(
                marker in message
                for marker in (
                    "503",
                    "UNAVAILABLE",
                    "429",
                    "RESOURCE_EXHAUSTED",
                    "500",
                    "502",
                    "504",
                    "INTERNAL",
                    "TIMEOUT",
                )
            )

            if not temporary_error or attempt == MAX_ATTEMPTS - 1:
                break

            # รอ 2 วินาที แล้ว 4 วินาที ก่อนลองอีกครั้ง
            time.sleep(2 ** (attempt + 1))

    raise AIError(
        f"เรียก Gemini ไม่สำเร็จ: "
        f"{type(last_error).__name__}: {str(last_error)[:300]}"
    ) from last_error


def _normalize(items, focus=None):
    out = []

    for i, item in enumerate(items):
        try:
            choices = [
                str(choice).strip()
                for choice in item["choices"]
            ]

            answer = (
                str(item["correct_answer"])
                .strip()
                .upper()[:1]
            )

            difficulty = str(
                item.get("difficulty", "medium")
            ).lower()

            if len(choices) != 4:
                continue

            if answer not in ("A", "B", "C", "D"):
                continue

            if difficulty not in REWARD:
                difficulty = "medium"

            topic = str(item["topic"]).strip()

            if focus:
                topic = focus[i % len(focus)]

            damage, xp = REWARD[difficulty]

            out.append({
                "question": str(item["question"]),
                "choices": choices,
                "correct_answer": answer,
                "explanation": str(item["explanation"]),
                "topic": topic,
                "difficulty": difficulty,
                "damage": damage,
                "xp": xp,
            })

        except (KeyError, TypeError, AttributeError):
            continue

    if not out:
        raise AIError(
            "AI สร้างคำถามไม่สำเร็จ "
            "ลองใหม่หรือใช้เนื้อหาที่ยาวขึ้น"
        )

    return out


def generate_questions(
    material: str,
    n: int = 10,
    focus_topics=None,
):
    """สร้างคำถามสำหรับ Battle, Speed Run และ Weakness Training"""

    if not material or not material.strip():
        raise AIError("กรุณาใส่เนื้อหาบทเรียนก่อนสร้างคำถาม")

    if focus_topics:
        focus = (
            "สร้างคำถามเฉพาะหัวข้อเหล่านี้เท่านั้น: "
            f"{', '.join(focus_topics)} "
            "และใส่ topic ให้ตรงกับชื่อหัวข้อเหล่านี้ทุกตัวอักษร "
            "สร้างคำถามใหม่ที่หลากหลาย"
        )
    else:
        focus = (
            "แยกหัวข้อสำคัญของเนื้อหา กระจายคำถามให้ครอบคลุม "
            "และตั้งชื่อ topic สั้น ๆ 1-4 คำ"
        )

    prompt = f"""คุณคือติวเตอร์ที่สร้างข้อสอบปรนัยจากเนื้อหาที่ผู้ใช้ให้มา

กติกา:
- สร้างคำถามปรนัย {n} ข้อ จากเนื้อหาด้านล่างเท่านั้น
- ห้ามใช้ข้อมูลนอกเนื้อหา
- choices ต้องมี 4 ตัวเลือก เป็นข้อความล้วน ไม่ต้องใส่ A/B/C/D นำหน้า
- correct_answer เป็น A, B, C หรือ D
- difficulty เป็น easy, medium หรือ hard
- explanation อธิบายสั้น ๆ โดยอิงเนื้อหา
- ใช้ภาษาเดียวกับเนื้อหา
- {focus}

เนื้อหา:
\"\"\"{material[:MAX_CHARS]}\"\"\"
"""

    raw = _call(prompt, schema=list[QuestionSchema])

    try:
        items = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        raise AIError(
            "AI ตอบกลับในรูปแบบที่อ่านไม่ได้ กรุณาลองใหม่"
        )

    return _normalize(items, focus_topics)


def recommend(report) -> str:
    """สร้างคำแนะนำการทบทวนจากผลคะแนนแต่ละหัวข้อ"""

    if not report:
        return (
            "ยังมีข้อมูลไม่เพียงพอ "
            "ลองเล่นเกมเพิ่มอีกสักรอบ"
        )

    summary = "\n".join(
        f"- {row['topic']}: {row['accuracy']:.0%} "
        f"({row['correct']}/{row['total']})"
        for row in report
    )

    prompt = (
        "นักเรียนได้ผลตามหัวข้อดังนี้:\n"
        + summary
        + "\n\nเขียนคำแนะนำการทบทวนสั้น ๆ 2-3 ประโยค "
        "เป็นภาษาไทย ให้กำลังใจ และบอกว่าควรกลับไปทบทวนหัวข้อไหนก่อน"
    )

    return _call(prompt).strip()
