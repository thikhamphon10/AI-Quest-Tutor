import json
import os

from google import genai
from google.genai import types
from pydantic import BaseModel

MODEL = "gemini-2.5-flash"
MAX_CHARS = 30000
REWARD = {"easy": (15, 10), "medium": (20, 15), "hard": (30, 25)}  # (damage, xp)


class AIError(Exception):
    pass


class QuestionSchema(BaseModel):
    question: str
    choices: list[str]
    correct_answer: str
    explanation: str
    topic: str
    difficulty: str


def _client():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise AIError("ยังไม่ได้ตั้งค่า GEMINI_API_KEY — ใส่ใน Replit Secrets (หรือ environment variable) แล้วรันใหม่")
    return genai.Client(api_key=key)


def _call(prompt: str, schema=None) -> str:
    try:
        cfg = types.GenerateContentConfig(
            temperature=0.6,
            response_mime_type="application/json" if schema else "text/plain",
            response_schema=schema,
        )
        return _client().models.generate_content(model=MODEL, contents=prompt, config=cfg).text
    except AIError:
        raise
    except Exception as e:
        raise AIError(f"เรียก Gemini ไม่สำเร็จ ({type(e).__name__}) ตรวจ API Key / อินเทอร์เน็ต แล้วลองใหม่")


def _normalize(items, focus=None):
    out = []
    for i, it in enumerate(items):
        try:
            choices = [str(c).strip() for c in it["choices"]]
            ans = str(it["correct_answer"]).strip().upper()[:1]
            diff = str(it.get("difficulty", "medium")).lower()
            if len(choices) != 4 or ans not in ("A", "B", "C", "D"):
                continue
            if diff not in REWARD:
                diff = "medium"
            topic = str(it["topic"]).strip()
            if focus and topic not in focus:
                topic = focus[i % len(focus)]
            dmg, xp = REWARD[diff]
            out.append({
                "question": it["question"], "choices": choices, "correct_answer": ans,
                "explanation": it["explanation"], "topic": topic, "difficulty": diff,
                "damage": dmg, "xp": xp,
            })
        except (KeyError, TypeError, AttributeError):
            continue
    if not out:
        raise AIError("AI สร้างคำถามไม่สำเร็จ ลองกดอีกครั้ง หรือใช้เนื้อหาที่ยาวขึ้น")
    return out


def generate_questions(material: str, n: int = 10, focus_topics=None):
    """ใช้ร่วมกันทั้ง Battle / Speed Run / Weakness Training"""
    if focus_topics:
        focus = (f"สร้างคำถามเฉพาะหัวข้อเหล่านี้เท่านั้น: {', '.join(focus_topics)} "
                 "และใส่ topic ให้ตรงกับชื่อหัวข้อเหล่านี้ทุกตัวอักษร ทำข้อใหม่ที่หลากหลาย")
    else:
        focus = "แยกหัวข้อสำคัญของเนื้อหา แล้วกระจายคำถามให้ครอบคลุม ตั้งชื่อ topic สั้น ๆ (1-4 คำ)"
    prompt = f"""คุณคือติวเตอร์ที่สร้างข้อสอบปรนัยจากเนื้อหาที่ผู้ใช้ให้มา
กติกา:
- สร้างคำถามปรนัย {n} ข้อ จากเนื้อหาด้านล่างเท่านั้น ห้ามใช้ข้อมูลนอกเนื้อหา
- choices ต้องมี 4 ตัวเลือก เป็นข้อความล้วน ไม่ต้องใส่ A/B/C/D นำหน้า
- correct_answer เป็น A, B, C หรือ D
- difficulty เป็น easy, medium หรือ hard
- explanation อธิบายสั้น ๆ โดยอิงเนื้อหา
- ใช้ภาษาเดียวกับเนื้อหา
- {focus}

เนื้อหา:
\"\"\"{material[:MAX_CHARS]}\"\"\""""
    raw = _call(prompt, schema=list[QuestionSchema])
    try:
        items = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        raise AIError("AI ตอบกลับในรูปแบบที่อ่านไม่ได้ ลองกดอีกครั้ง")
    return _normalize(items, focus_topics)


def recommend(report) -> str:
    """AI Recommendation จากผลรายหัวข้อ"""
    if not report:
        return "ยังไม่มีข้อมูลเพียงพอ ลองเล่นเกมเพิ่มอีกสักรอบ"
    summary = "\n".join(f"- {r['topic']}: {r['accuracy']:.0%} ({r['correct']}/{r['total']})" for r in report)
    prompt = ("นักเรียนได้ผลตามหัวข้อดังนี้:\n" + summary +
              "\n\nเขียนคำแนะนำการทบทวนสั้น ๆ 2-3 ประโยค ภาษาไทย ให้กำลังใจ "
              "และบอกว่าควรกลับไปทบทวนหัวข้อไหนก่อน")
    return _call(prompt).strip()
