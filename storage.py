"""บันทึก/โหลดความก้าวหน้าเป็นไฟล์ JSON ต่อผู้เล่น (ไม่ใช้ streamlit เพื่อให้ทดสอบง่าย)

ผู้เล่นแต่ละคนมี player id สุ่มอยู่ใน URL (?p=...) รีเฟรชหน้าแล้ว id เดิมยังอยู่ จึงโหลดเซฟเดิมได้
ที่เก็บไฟล์: โฟลเดอร์ saves/ (เปลี่ยนได้ด้วยตัวแปรแวดล้อม SAVE_DIR)
หมายเหตุ: บน Streamlit Community Cloud ดิสก์ถูกล้างเมื่อแอปรีสตาร์ท จึงมีปุ่มดาวน์โหลด/นำเข้าไฟล์เซฟสำรองในหน้าแรก
"""
import json
import os
import re
import secrets

_ID_RE = re.compile(r"^[a-f0-9]{16,32}$")


def save_dir() -> str:
    d = os.getenv("SAVE_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves")
    return d


def new_id() -> str:
    return secrets.token_hex(8)


def valid_id(pid) -> bool:
    return isinstance(pid, str) and bool(_ID_RE.match(pid))


def _path(pid: str) -> str:
    if not valid_id(pid):  # กัน path traversal
        raise ValueError("invalid player id")
    return os.path.join(save_dir(), f"{pid}.json")


def exists(pid: str) -> bool:
    return valid_id(pid) and os.path.isfile(_path(pid))


def load(pid: str):
    """คืน dict หรือ None ถ้าไม่มี/ไฟล์เสีย"""
    try:
        with open(_path(pid), "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def save(pid: str, data: dict) -> bool:
    """เขียนแบบ atomic คืน True ถ้าสำเร็จ"""
    try:
        os.makedirs(save_dir(), exist_ok=True)
        tmp = _path(pid) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, _path(pid))
        return True
    except (OSError, ValueError, TypeError):
        return False
