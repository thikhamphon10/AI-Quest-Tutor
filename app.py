
import streamlit as st
from ai_engine import generate_questions, AIError
from pdf_processor import extract_text
from game_engine import GameEngine
from games.battle import render_battle_game

# Page Configuration
st.set_page_config(
    page_title="AI Quest Tutor - เกมติวแฟนตาซี",
    page_icon="🐾",
    layout="wide",
)

# Custom Kawaii CSS Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Kanit', sans-serif;
        background-color: #FFF5F5;
    }

    .kawaii-card {
        background: #FFFFFF;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 8px 16px rgba(255, 182, 193, 0.3);
        border: 2px solid #FFD1DC;
        margin-bottom: 15px;
    }

    .status-bar {
        background: linear-gradient(135deg, #FFB7B2, #FFDAC1);
        border-radius: 15px;
        padding: 12px 20px;
        color: #5D4037;
        font-weight: bold;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-around;
        align-items: center;
    }

    .stButton>button {
        background-color: #FF9AA2 !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: bold !important;
        padding: 10px 24px !important;
        transition: all 0.2s ease !important;
    }

    .stButton>button:hover {
        background-color: #FFB7B2 !important;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)


# Initialize Game
engine = GameEngine()

# ตรวจสอบข้อมูลผู้เล่น
if "user_data" not in st.session_state:
    st.error(
        "ไม่พบข้อมูลผู้เล่น กรุณาตรวจสอบว่า GameEngine() "
        "สร้าง user_data ใน st.session_state แล้วหรือไม่"
    )
    st.stop()

if "current_page" not in st.session_state:
    st.session_state.current_page = "map"

user = st.session_state.user_data

# Header Status Bar
st.markdown(f"""
<div class='status-bar'>
    <span>🏰 Level: {user['level']}</span>
    <span>⭐ Stars: {user['stars']}</span>
    <span>🪙 Coins: {user['coins']}</span>
    <span>✨ XP: {user['xp']} / {user['max_xp']}</span>
</div>
""", unsafe_allow_html=True)


# Sidebar
with st.sidebar:
    st.title("🐾 AI Quest Tutor")
    st.caption("ติวสนุกด้วยภารกิจพิชิตเวทมนตร์")

    avatars = st.session_state.get("avatars", {})

    if avatars:
        st.subheader("👤 ตัวละครของคุณ")
        selected = st.selectbox(
            "เลือกคู่หูผจญภัย:",
            list(avatars.keys()),
            format_func=lambda x: avatars[x]["name"],
        )
        st.session_state.user_data["selected_avatar"] = selected
        st.image(avatars[selected]["img"], width=80)
        st.caption(avatars[selected]["desc"])
    else:
        st.warning("ยังไม่มีข้อมูลตัวละครใน GameEngine")

    st.markdown("---")

    if st.button("🗺️ หน้าหลัก / แผนที่", use_container_width=True):
        st.session_state.current_page = "map"
        st.rerun()

    if st.button("📚 สร้างบทเรียนจาก AI", use_container_width=True):
        st.session_state.current_page = "ai_generator"
        st.rerun()


# Page 1: World Map
if st.session_state.current_page == "map":
    st.markdown("## 🗺️ แผนที่โลกแห่งการเรียนรู้")
    st.write("เลือกด่านมอนสเตอร์เพื่อเริ่มภารกิจด้วยความรู้!")

    monsters = st.session_state.get("monsters", {})
    cols = st.columns(3)

    for stage_id in [1, 2, 3]:
        with cols[stage_id - 1]:
            monster = monsters.get(stage_id)

            if not monster:
                st.warning(f"ยังไม่มีข้อมูลมอนสเตอร์ด่าน {stage_id}")
                continue

            is_unlocked = stage_id in user.get("unlocked_stages", [])

            st.markdown(
                f"<div class='kawaii-card' style='text-align:center; "
                f"opacity:{1.0 if is_unlocked else 0.5};'>",
                unsafe_allow_html=True,
            )
            st.image(monster["img"], width=80)
            st.markdown(f"#### ด่านที่ {stage_id}: {monster['name']}")

            if is_unlocked:
                st.success("ปลดล็อกแล้ว")

                if st.button(
                    f"⚔️ ท้าประลองด่าน {stage_id}",
                    key=f"btn_stage_{stage_id}",
                    use_container_width=True,
                ):
                    if not st.session_state.get("active_questions"):
                        st.warning(
                            "กรุณาสร้างโจทย์จากเมนู "
                            "'สร้างบทเรียนจาก AI' ก่อน!"
                        )
                    else:
                        st.session_state.selected_stage = stage_id
                        st.session_state.current_page = "battle"
                        st.rerun()
            else:
                st.info("🔒 ยังไม่ปลดล็อก")

            st.markdown("</div>", unsafe_allow_html=True)


# Page 2: AI Question Generator
elif st.session_state.current_page == "ai_generator":
    st.markdown("## 📚 สร้างโจทย์ติวหนังสือด้วย AI")

    tab1, tab2 = st.tabs([
        "📝 ป้อนข้อความ/เนื้อหา",
        "📄 อัปโหลดไฟล์ PDF",
    ])

    with tab1:
        text_content = st.text_area(
            "กรอกเนื้อหาที่ต้องการให้ AI ออกข้อสอบ:",
            height=150,
            placeholder="เช่น ชีววิทยา เรื่องการสังเคราะห์ด้วยแสง",
        )

    with tab2:
        uploaded_file = st.file_uploader(
            "อัปโหลดเอกสาร PDF",
            type=["pdf"],
        )

    difficulty = st.selectbox(
        "ระดับความยาก:",
        ["ง่าย (Easy)", "ปานกลาง (Medium)", "ยาก (Hard)"],
    )

    num_q = st.slider(
        "จำนวนข้อสอบ:",
        min_value=3,
        max_value=10,
        value=5,
    )

    if st.button(
        "🪄 ร่ายคาถาสร้างโจทย์!",
        type="primary",
        use_container_width=True,
    ):
        content = text_content.strip()

        if uploaded_file is not None and not content:
            try:
                content = extract_text(uploaded_file)
            except Exception as e:
                st.error(f"อ่านไฟล์ PDF ไม่สำเร็จ: {e}")
                content = ""

        if not content:
            st.error("กรุณากรอกเนื้อหาหรืออัปโหลดไฟล์ PDF ก่อน")
        else:
            with st.spinner("🔮 กำลังอัญเชิญ Gemini AI..."):
                try:
                    # สร้างคำถามจากเนื้อหา
                    questions = generate_questions(
                        material=content,
                        n=num_q,
                    )

                    # ปรับระดับความยากตามที่ผู้ใช้เลือก
                    difficulty_map = {
                        "ง่าย (Easy)": "easy",
                        "ปานกลาง (Medium)": "medium",
                        "ยาก (Hard)": "hard",
                    }
                    chosen_difficulty = difficulty_map[difficulty]

                    for question in questions:
                        question["difficulty"] = chosen_difficulty

                        rewards = {
                            "easy": (15, 10),
                            "medium": (20, 15),
                            "hard": (30, 25),
                        }
                        damage, xp = rewards[chosen_difficulty]
                        question["damage"] = damage
                        question["xp"] = xp

                    st.session_state.active_questions = questions
                    st.success(
                        f"สร้างโจทย์สำเร็จ {len(questions)} ข้อ! "
                        "พร้อมเข้าสู่การต่อสู้"
                    )

                except AIError as e:
                    st.error(f"สร้างโจทย์ไม่สำเร็จ: {e}")
                except Exception as e:
                    st.error(
                        f"เกิดข้อผิดพลาด: {type(e).__name__}: {e}"
                    )

    if st.session_state.get("active_questions"):
        st.info(
            f"มีโจทย์พร้อมเล่นแล้ว "
            f"{len(st.session_state.active_questions)} ข้อ"
        )

        if st.button("⚔️ ไปที่แผนที่เพื่อเริ่มลุย!"):
            st.session_state.current_page = "map"
            st.rerun()


# Page 3: Battle
elif st.session_state.current_page == "battle":
    st.markdown("## ⚔️ การต่อสู้ด้วยเวทมนตร์แห่งปัญญา")

    if st.button("⬅️ ถอนตัวกลับแผนที่"):
        st.session_state.current_page = "map"
        st.rerun()

    stage = st.session_state.get("selected_stage", 1)

    render_battle_game(
        st.session_state.get("active_questions", []),
        current_stage=stage,
    )
