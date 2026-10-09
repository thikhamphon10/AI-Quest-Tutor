import os

import streamlit as st

import ai_engine
import pdf_processor
from game_engine import go, init_state, new_game, topic_report
from games import battle, speed_run, weakness
from utils import render_topics

NUM_Q = 10
MODE_NAME = {"battle": "⚔️ Battle Quest", "speed": "⚡ Speed Run", "weakness": "🔥 Weakness Training"}

st.set_page_config(page_title="AI Quest Tutor", page_icon="🎮", layout="centered")
init_state()
s = st.session_state


def start_game(mode):
    s.game = new_game(mode, s.questions)
    go("game")


def page_home():
    st.title("🎮 AI Quest Tutor")
    st.caption("Learn. Play. Level Up.")
    if not os.getenv("GEMINI_API_KEY"):
        st.warning("ยังไม่ได้ตั้งค่า GEMINI_API_KEY — ใส่ใน Replit Secrets ก่อนเริ่มเล่น")
    if st.button("🚀 Start Quest", type="primary", use_container_width=True):
        go("material")
    with st.expander("📈 My Progress", expanded=bool(s.history)):
        c1, c2 = st.columns(2)
        c1.metric("✨ Total XP", s.total_xp)
        c2.metric("🔥 Best Streak", s.best_streak)
        render_topics(topic_report(s.history))


def page_material():
    st.header("📚 Study Material")
    tab1, tab2 = st.tabs(["📄 Upload PDF", "📝 Paste Notes"])
    with tab1:
        pdf = st.file_uploader("เลือกไฟล์ PDF", type="pdf")
    with tab2:
        notes = st.text_area("วางเนื้อหาบทเรียน", height=250)
    st.caption("ถ้ามีทั้ง PDF และ Notes ระบบจะใช้ PDF")
    if st.button("🤖 สร้างคำถามด้วย AI", type="primary", use_container_width=True):
        try:
            if pdf:
                text = pdf_processor.extract_text(pdf)
            else:
                text = pdf_processor.clean_text(notes)
                if len(text) < 50:
                    st.warning("กรุณาอัปโหลด PDF หรือวางเนื้อหาให้ยาวกว่านี้")
                    return
            with st.spinner("🤖 AI กำลังอ่านเนื้อหาและสร้างคำถาม..."):
                qs = ai_engine.generate_questions(text, NUM_Q)
        except (ValueError, ai_engine.AIError) as e:
            st.error(str(e))
            return
        s.material, s.questions, s.history = text, qs, {}
        go("mode")
    if st.button("⬅️ กลับ"):
        go("home")


def page_mode():
    st.header("🎯 เลือก Game Mode")
    st.caption(f"พร้อมเล่น: {len(s.questions)} คำถาม · หัวข้อ: {', '.join(sorted({q['topic'] for q in s.questions}))}")
    for mode, desc in [("battle", "Fight monsters with your knowledge"), ("speed", "Answer before time runs out")]:
        with st.container(border=True):
            st.subheader(MODE_NAME[mode])
            st.write(desc)
            if st.button("เล่นเลย", key=mode, use_container_width=True):
                start_game(mode)
    with st.container(border=True):
        st.subheader(MODE_NAME["weakness"])
        st.write("Train your weakest topics")
        if not s.history:
            st.caption("ต้องเล่นเกมอื่นอย่างน้อย 1 รอบก่อน")
        if st.button("เล่นเลย", key="weak", disabled=not s.history, use_container_width=True):
            weakness.start()
    if st.button("⬅️ เปลี่ยนเนื้อหา"):
        go("material")


def page_game():
    g = s.game
    if not g:
        go("home")
    st.caption(MODE_NAME[g["mode"]])
    {"battle": battle, "speed": speed_run, "weakness": weakness}[g["mode"]].render(g)


def page_result():
    r = s.last_result
    if not r:
        go("home")
    st.header(f"{MODE_NAME[r['mode']]} — ผลลัพธ์")
    banner = {"victory": ("success", "🏆 Victory!"), "gameover": ("error", "💀 Game Over"),
              "timeup": ("info", "⏱️ หมดเวลา!"), "done": ("success", "✅ ฝึกครบแล้ว!")}
    kind, msg = banner.get(r["outcome"], ("info", "จบเกม"))
    getattr(st, kind)(msg)

    c1, c2 = st.columns(2)
    c1.metric("🏆 Score", r["score"])
    c2.metric("🎯 Accuracy", f"{r['accuracy']:.0%}")
    c3, c4 = st.columns(2)
    c3.metric("✨ XP", r["xp"])
    c4.metric("🔥 Best Streak", r["best_streak"])
    st.caption(f"ตอบ {r['total']} ข้อ · ถูก {r['correct']} · ผิด {r['wrong']}")

    if r["before"]:
        st.subheader("📊 เทียบก่อน/หลังฝึก")
        after = {t["topic"]: t["accuracy"] for t in r["topics"]}
        for topic, b in r["before"].items():
            if topic in after:
                st.write(f"**{topic}**: {b:.0%} → {after[topic]:.0%}")

    overall = topic_report(s.history)
    st.subheader("🎯 Topics")
    render_topics(overall)
    st.write("🟢 **Strong:** " + (", ".join(x["topic"] for x in overall if x["level"] == "strong") or "-"))
    st.write("🔴 **Weak:** " + (", ".join(x["topic"] for x in overall if x["level"] == "weak") or "-"))

    if r["recommendation"] is None:
        with st.spinner("🤖 AI กำลังวิเคราะห์..."):
            try:
                r["recommendation"] = ai_engine.recommend(overall)
            except ai_engine.AIError:
                r["recommendation"] = "ลองเล่น Weakness Training กับหัวข้อสีแดง แล้วกลับมาเทียบผลอีกครั้ง"
    st.info(f"🤖 **AI Recommendation:** {r['recommendation']}")

    if st.button("🔥 Weakness Training", type="primary", use_container_width=True):
        weakness.start()
    if st.button("🔁 เล่นโหมดนี้อีกครั้ง", use_container_width=True):
        weakness.start() if r["mode"] == "weakness" else start_game(r["mode"])
    if st.button("🎮 เลือกเกมอื่น", use_container_width=True):
        go("mode")
    if st.button("🏠 Home", use_container_width=True):
        go("home")


{"home": page_home, "material": page_material, "mode": page_mode,
 "game": page_game, "result": page_result}[s.page]()
