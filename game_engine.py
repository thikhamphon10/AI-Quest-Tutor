import random
import time

import streamlit as st

LETTERS = "ABCD"


def init_state():
    defaults = {"page": "home", "material": "", "questions": [], "history": {},
                "total_xp": 0, "best_streak": 0, "game": None, "last_result": None}
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def go(page: str):
    st.session_state.page = page
    st.rerun()


# ---------- Weakness logic ----------
def classify(acc: float) -> str:
    return "weak" if acc < 0.6 else "strong" if acc >= 0.8 else "practice"


def topic_report(stats: dict):
    rows = []
    for topic, s in stats.items():
        total = s["correct"] + s["wrong"]
        if total:
            acc = s["correct"] / total
            rows.append({"topic": topic, "correct": s["correct"], "total": total,
                         "accuracy": acc, "level": classify(acc)})
    return sorted(rows, key=lambda r: r["accuracy"])


def weak_topics(stats: dict):
    rep = topic_report(stats)
    weak = [r["topic"] for r in rep if r["level"] == "weak"]
    return weak or [r["topic"] for r in rep if r["level"] == "practice"]


# ---------- Game ----------
def new_game(mode: str, questions: list):
    qs = list(questions)
    random.shuffle(qs)
    return {"mode": mode, "queue": qs, "idx": 0, "player_hp": 100, "monster_hp": 100,
            "score": 0, "streak": 0, "best_streak": 0, "xp": 0, "correct": 0, "wrong": 0,
            "topics": {}, "feedback": None, "over": None, "start": time.time(), "before": None}


def record(g: dict, q: dict, ok: bool):
    """บันทึกคำตอบ 1 ข้อ ลงทั้งเกมนี้และ history รวม"""
    for store in (g["topics"], st.session_state.history):
        s = store.setdefault(q["topic"], {"correct": 0, "wrong": 0})
        s["correct" if ok else "wrong"] += 1
    if ok:
        g["correct"] += 1
        g["streak"] += 1
        g["best_streak"] = max(g["best_streak"], g["streak"])
        g["xp"] += q["xp"]
        st.session_state.total_xp += q["xp"]
    else:
        g["wrong"] += 1
        g["streak"] = 0
    st.session_state.best_streak = max(st.session_state.best_streak, g["best_streak"])


def finish(g: dict):
    total = g["correct"] + g["wrong"]
    st.session_state.last_result = {
        "mode": g["mode"], "outcome": g["over"], "score": g["score"], "xp": g["xp"],
        "correct": g["correct"], "wrong": g["wrong"], "total": total,
        "accuracy": g["correct"] / total if total else 0, "best_streak": g["best_streak"],
        "topics": topic_report(g["topics"]), "before": g["before"], "recommendation": None,
    }
    st.session_state.game = None
    go("result")


def choice_buttons(q: dict, key: str):
    for i, c in enumerate(q["choices"]):
        if st.button(f"{LETTERS[i]}. {c}", key=f"{key}_{i}", use_container_width=True):
            return LETTERS[i]
    return None


def answer_text(q: dict) -> str:
    return f"{q['correct_answer']}. {q['choices'][LETTERS.index(q['correct_answer'])]}"


def show_feedback(fb: dict):
    if fb["ok"]:
        st.success("✅ ถูกต้อง!")
    else:
        st.error(f"❌ ผิด — คำตอบที่ถูกคือ {fb['answer']}")
    st.info(f"💡 {fb['explanation']}")
