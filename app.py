
import os

import streamlit as st

import ai_engine
import pdf_processor
from game_engine import go, init_state, new_game, topic_report
from games import battle, speed_run, weakness
from utils import render_topics


NUM_Q = 10

MODE_NAME = {
    "battle": "⚔️ Battle Quest",
    "speed": "⚡ Speed Run",
    "weakness": "🔥 Weakness Training",
}

st.set_page_config(
    page_title="AI Quest Tutor",
    page_icon="🎮",
    layout="centered",
)

init_state()
s = st.session_state


def get_api_key():
    """อ่าน Gemini API Key จาก Environment หรือ Streamlit Secrets"""
    key = os.getenv("GEMINI_API_KEY")

    if not key:
        try:
            key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            key = None

    return str(key).strip() if key else None


def start_game(mode):
    s.game = new_game(mode, s.questions)
    go("game")


def page_home():
    st.title("🎮 AI Quest Tutor")
    st.caption("Learn. Play. Level Up.")

    api_key = get_api_key()

    if not api_key:
        st.warning(
            "ยังไม่ได้ตั้งค่า GEMINI_API_KEY "
            "กรุณาตั้งค่าใน Streamlit Community Cloud "
            "ที่ Manage app > Settings > Secrets"
        )
    else:
        st.success("✅ พบการตั้งค่า Gemini API Key")

    if st.button(
        "🚀 Start Quest",
        type="primary",
        use_container_width=True,
    ):
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
        pdf = st.file_uploader(
            "เลือกไฟล์ PDF",
            type="pdf",
        )

    with tab2:
        notes = st.text_area(
            "วางเนื้อหาบทเรียน",
            height=250,
        )

    st.caption("ถ้ามีทั้ง PDF และ Notes ระบบจะใช้ PDF")

    if st.button(
        "🤖 สร้างคำถามด้วย AI",
        type="primary",
        use_container_width=True,
    ):
        if not get_api_key():
            st.error(
                "ยังไม่พบ Gemini API Key "
                "กรุณาตั้งค่าใน Streamlit Secrets ก่อน"
            )
            return

        try:
            if pdf:
                text = pdf_processor.extract_text(pdf)
            else:
                text = pdf_processor.clean_text(notes)

                if len(text) < 50:
                    st.warning(
                        "กรุณาอัปโหลด PDF "
                        "หรือวางเนื้อหาอย่างน้อย 50 ตัวอักษร"
                    )
                    return

            with st.spinner(
                "🤖 AI กำลังอ่านเนื้อหาและสร้างคำถาม..."
            ):
                qs = ai_engine.generate_questions(text, NUM_Q)

        except (ValueError, ai_engine.AIError) as e:
            st.error(str(e))
            return
        except Exception as e:
            st.error(
                f"เกิดข้อผิดพลาด ({type(e).__name__}): {e}"
            )
            return

        s.material = text
        s.questions = qs
        s.history = {}

        go("mode")


    if st.button("⬅️ กลับ"):
        go("home")


def page_mode():
    st.header("🎯 เลือก Game Mode")

    topics = sorted({q["topic"] for q in s.questions})

    st.caption(
        f"พร้อมเล่น: {len(s.questions)} คำถาม · "
        f"หัวข้อ: {', '.join(topics)}"
    )

    modes = [
        ("battle", "Fight monsters with your knowledge"),
        ("speed", "Answer before time runs out"),
    ]

    for mode, desc in modes:
        with st.container(border=True):
            st.subheader(MODE_NAME[mode])
            st.write(desc)

            if st.button(
                "เล่นเลย",
                key=mode,
                use_container_width=True,
            ):
                start_game(mode)

    with st.container(border=True):
        st.subheader(MODE_NAME["weakness"])
        st.write("Train your weakest topics")

        if not s.history:
            st.caption("ต้องเล่นเกมอื่นอย่างน้อย 1 รอบก่อน")

        if st.button(
            "เล่นเลย",
            key="weak",
            disabled=not s.history,
            use_container_width=True,
        ):
            weakness.start()

    if st.button("⬅️ เปลี่ยนเนื้อหา"):
        go("material")


def page_game():
    g = s.game

    if not g:
        go("home")
        return

    st.caption(MODE_NAME[g["mode"]])

    game_module = {
        "battle": battle,
        "speed": speed_run,
        "weakness": weakness,
    }[g["mode"]]

    game_module.render(g)


def page_result():
    r = s.last_result

    if not r:
        go("home")
        return

    st.header(f"{MODE_NAME[r['mode']]} — ผลลัพธ์")

    banner = {
        "victory": ("success", "🏆 Victory!"),
        "gameover": ("error", "💀 Game Over"),
        "timeup": ("info", "⏱️ หมดเวลา!"),
        "done": ("success", "✅ ฝึกครบแล้ว!"),
    }

    kind, msg = banner.get(
        r["outcome"],
        ("info", "จบเกม"),
    )

    getattr(st, kind)(msg)

    c1, c2 = st.columns(2)
    c1.metric("🏆 Score", r["score"])
    c2.metric("🎯 Accuracy", f"{r['accuracy']:.0%}")

    c3, c4 = st.columns(2)
    c3.metric("✨ XP", r["xp"])
    c4.metric("🔥 Best Streak", r["best_streak"])

    st.caption(
        f"ตอบ {r['total']} ข้อ · "
        f"ถูก {r['correct']} · ผิด {r['wrong']}"
    )

    if r["before"]:
        st.subheader("📊 เทียบก่อน/หลังฝึก")

        after = {
            t["topic"]: t["accuracy"]
            for t in r["topics"]
        }

        for topic, before_accuracy in r["before"].items():
            if topic in after:
                st.write(
                    f"**{topic}**: "
                    f"{before_accuracy:.0%} → "
                    f"{after[topic]:.0%}"
                )

    overall = topic_report(s.history)

    st.subheader("🎯 Topics")
    render_topics(overall)

    strong_topics = [
        x["topic"] for x in overall
        if x["level"] == "strong"
    ]

    weak_topics = [
        x["topic"] for x in overall
        if x["level"] == "weak"
    ]

    st.write(
        "🟢 **Strong:** "
        + (", ".join(strong_topics) or "-")
    )

    st.write(
        "🔴 **Weak:** "
        + (", ".join(weak_topics) or "-")
    )

    if r["recommendation"] is None:
        with st.spinner("🤖 AI กำลังวิเคราะห์..."):
            try:
                r["recommendation"] = ai_engine.recommend(
                    overall
                )
            except ai_engine.AIError as e:
                st.warning(
                    f"AI Recommendation ใช้งานไม่ได้: {e}"
                )
                r["recommendation"] = (
                    "ลองเล่น Weakness Training "
                    "กับหัวข้อสีแดง แล้วกลับมาเทียบผลอีกครั้ง"
                )

    st.info(
        f"🤖 **AI Recommendation:** "
        f"{r['recommendation']}"
    )

    if st.button(
        "🔥 Weakness Training",
        type="primary",
        use_container_width=True,
    ):
        weakness.start()

    if st.button(
        "🔁 เล่นโหมดนี้อีกครั้ง",
        use_container_width=True,
    ):
        if r["mode"] == "weakness":
            weakness.start()
        else:
            start_game(r["mode"])

    if st.button(
        "🎮 เลือกเกมอื่น",
        use_container_width=True,
    ):
        go("mode")

    if st.button(
        "🏠 Home",
        use_container_width=True,
    ):
        go("home")


PAGES = {
    "home": page_home,
    "material": page_material,
    "mode": page_mode,
    "game": page_game,
    "result": page_result,
}

PAGES.get(s.page, page_home)()

