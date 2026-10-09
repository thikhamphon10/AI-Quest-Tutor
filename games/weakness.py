import streamlit as st

import ai_engine
from game_engine import (answer_text, choice_buttons, finish, go, new_game, record,
                         show_feedback, topic_report, weak_topics)

NUM_Q = 8


def start():
    """History → Weak Topics → AI สร้างคำถามใหม่ → เริ่มฝึก"""
    s = st.session_state
    topics = weak_topics(s.history)
    if not topics:
        st.success("🎉 ตอนนี้คุณเก่งทุกหัวข้อแล้ว ยังไม่มีจุดอ่อนให้ฝึก")
        return
    try:
        with st.spinner("🤖 AI กำลังสร้างแบบฝึกเฉพาะจุดอ่อน..."):
            qs = ai_engine.generate_questions(s.material, NUM_Q, focus_topics=topics)
    except ai_engine.AIError as e:
        st.error(str(e))
        return
    g = new_game("weakness", qs)
    g["before"] = {r["topic"]: r["accuracy"] for r in topic_report(s.history) if r["topic"] in topics}
    s.game = g
    go("game")


def render(g):
    n = len(g["queue"])
    if g["idx"] >= n:
        g["over"] = "done"
        finish(g)
    q = g["queue"][g["idx"]]
    st.progress(g["idx"] / n, text=f"🔥 ข้อ {g['idx'] + 1}/{n}  ·  หัวข้อ: {q['topic']}")
    st.subheader(q["question"])

    if g["feedback"]:
        show_feedback(g["feedback"])
        label = "📊 ดูผลลัพธ์" if g["idx"] + 1 >= n else "ข้อต่อไป ➡️"
        if st.button(label, type="primary", use_container_width=True):
            g["idx"] += 1
            g["feedback"] = None
            st.rerun()
        return

    pick = choice_buttons(q, f"w{g['idx']}")
    if pick:
        ok = pick == q["correct_answer"]
        record(g, q, ok)
        if ok:
            g["score"] += q["xp"] * 10
        g["feedback"] = {"ok": ok, "answer": answer_text(q), "explanation": q["explanation"]}
        st.rerun()
