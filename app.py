import streamlit as st
import json
import os
import hashlib
from ai_engine import generate_questions_from_text
from pdf_processor import extract_text_from_pdf
from game_engine import GameEngine
from games.battle import render_battle_game

st.set_page_config(page_title="AI Quest Tutor - เกมติวแฟนตาซี", page_icon="🐾", layout="wide")

# Directory สำหรับเก็บข้อสอบไว้ทำซ้ำ (Saved Quizzes)
SAVED_QUIZZES_DIR = "saved_quizzes"
os.makedirs(SAVED_QUIZZES_DIR, exist_ok=True)

def save_quiz_to_local(title: str, questions: list):
    filename = hashlib.md5(title.encode('utf-8')).hexdigest()[:10] + ".json"
    filepath = os.path.join(SAVED_QUIZZES_DIR, filename)
    data = {"title": title, "questions": questions}
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_saved_quizzes():
    quizzes = []
    for fn in os.listdir(SAVED_QUIZZES_DIR):
        if fn.endswith(".json"):
            filepath = os.path.join(SAVED_QUIZZES_DIR, fn)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    quizzes.append(json.load(f))
            except Exception:
                pass
    return quizzes

# Custom Kawaii Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Kanit', sans-serif; background-color: #FFF5F5; }
    .kawaii-card { background: #FFFFFF; border-radius: 20px; padding: 20px; box-shadow: 0 8px 16px rgba(255, 182, 193, 0.3); border: 2px solid #FFD1DC; margin-bottom: 15px; }
    .status-bar { background: linear-gradient(135deg, #FFB7B2, #FFDAC1); border-radius: 15px; padding: 12px 20px; color: #5D4037; font-weight: bold; margin-bottom: 20px; display: flex; justify-content: space-around; }
</style>
""", unsafe_allow_html=True)

engine = GameEngine()
user = st.session_state.user_data

if "current_page" not in st.session_state:
    st.session_state.current_page = "map"

# Header Status
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
    
    if st.button("🗺️ แผนที่โลก", use_container_width=True):
        st.session_state.current_page = "map"
        st.rerun()
        
    if st.button("📚 สร้างบทเรียนใหม่ (AI)", use_container_width=True):
        st.session_state.current_page = "ai_generator"
        st.rerun()

    if st.button("📁 คลังข้อสอบที่บันทึกไว้", use_container_width=True):
        st.session_state.current_page = "saved_quizzes"
        st.rerun()

# PAGE 1: MAP
if st.session_state.current_page == "map":
    st.markdown("## 🗺️ แผนที่โลกแห่งการเรียนรู้ (World Map)")
    
    cols = st.columns(3)
    for stage_id in [1, 2, 3]:
        with cols[stage_id - 1]:
            is_unlocked = stage_id in user["unlocked_stages"]
            monster = st.session_state.monsters[stage_id]
            st.markdown(f"<div class='kawaii-card' style='text-align: center;'>", unsafe_allow_html=True)
            st.image(monster["img"], width=80)
            st.markdown(f"#### ด่านที่ {stage_id}: {monster['name']}")
            
            if is_unlocked:
                if st.button(f"⚔️ เริ่มเล่นด่าน {stage_id}", key=f"btn_stage_{stage_id}", use_container_width=True):
                    if "active_questions" not in st.session_state or not st.session_state.active_questions:
                        st.warning("⚠️ กรุณาเลือกข้อสอบจาก 'สร้างบทเรียนใหม่' หรือ 'คลังข้อสอบ' ก่อนเข้าเล่น!")
                    else:
                        st.session_state.selected_stage = stage_id
                        st.session_state.current_page = "battle"
                        st.rerun()
            else:
                st.info("🔒 ยังไม่ปลดล็อก")
            st.markdown("</div>", unsafe_allow_html=True)

# PAGE 2: AI GENERATOR
elif st.session_state.current_page == "ai_generator":
    st.markdown("## 📚 สร้างโจทย์ติวหนังสือด้วย AI (Gemini)")
    
    tab1, tab2 = st.tabs(["📝 ป้อนข้อความ/เนื้อหา", "📄 อัปโหลดไฟล์ PDF"])
    
    content = ""
    with tab1:
        content = st.text_area("กรอกเนื้อหาที่ต้องการออกข้อสอบ:", height=150)
    with tab2:
        uploaded_file = st.file_uploader("อัปโหลดไฟล์ PDF", type=["pdf"])
        if uploaded_file:
            content = extract_text_from_pdf(uploaded_file)

    col_diff, col_num = st.columns(2)
    with col_diff:
        difficulty = st.selectbox("ระดับความยาก:", ["ง่าย", "ปานกลาง", "ยาก"])
    with col_num:
        # ตัวเลือกจำนวนข้อ 5, 10, 15, 20, 30, 40, 50 ข้อ
        num_q = st.selectbox("จำนวนข้อสอบที่ต้องการ:", [5, 10, 15, 20, 30, 40, 50], index=0)

    title_input = st.text_input("ตั้งชื่อชุดข้อสอบนี้ (สำหรับบันทึกไว้ใช้ซ้ำ):", value="บทเรียนเวทมนตร์")

    if st.button("🪄 ร่ายคาถาสร้างข้อสอบ", type="primary", use_container_width=True):
        if not content.strip():
            st.error("กรุณากรอกเนื้อหาหรืออัปโหลดไฟล์ PDF ก่อนทำการสร้างข้อสอบ")
        else:
            with st.spinner("🔮 กำลังอัญเชิญ Gemini AI สร้างบทเรียนแบบแบ่ง Batch..."):
                questions = generate_questions_from_text(content, difficulty, num_q)
                
                if questions:
                    st.session_state.active_questions = questions
                    # บันทึกไว้ใน Local Storage ทันทีเพื่อนำกลับมาใช้ซ้ำเมื่อ Quota หมด
                    save_quiz_to_local(title_input, questions)
                    
                    if len(questions) < num_q:
                        st.warning(f"⚠️ เนื่องจากขีดจำกัดโควตา API ระบบสร้างข้อสอบได้สำเร็จ {len(questions)} ข้อ จากที่ขอไว้ {num_q} ข้อ (ได้รับการบันทึกไว้เรียบร้อยแล้ว)")
                    else:
                        st.success(f"🎉 สร้างข้อสอบสำเร็จครบถ้วน {len(questions)} ข้อ! และบันทึกเข้าคลังเรียบร้อยแล้ว")
                        
                    if st.button("⚔️ ไปที่แผนที่เพื่อเริ่มลุย!"):
                        st.session_state.current_page = "map"
                        st.rerun()
                else:
                    st.error("❌ ไม่สามารถสร้างข้อสอบได้ เนื่องจากโควตา API ฟรีเต็มชั่วคราว กรุณาใช้ข้อสอบเดิมใน 'คลังข้อสอบที่บันทึกไว้'")

# PAGE 3: SAVED QUIZZES
elif st.session_state.current_page == "saved_quizzes":
    st.markdown("## 📁 คลังข้อสอบที่บันทึกไว้ (เล่นได้โดยไม่ต้องใช้ API Quota)")
    quizzes = load_saved_quizzes()
    
    if not quizzes:
        st.info("ยังไม่มีชุดข้อสอบที่บันทึกไว้ คุณสามารถสร้างชุดข้อสอบใหม่ได้ในเมนู 'สร้างบทเรียนใหม่'")
    else:
        for idx, qz in enumerate(quizzes):
            st.markdown(f"<div class='kawaii-card'>", unsafe_allow_html=True)
            col_info, col_act = st.columns([3, 1])
            with col_info:
                st.markdown(f"#### 📖 {qz.get('title', 'ชุดข้อสอบไม่มีชื่อ')}")
                st.caption(f"จำนวนข้อสอบ: {len(qz.get('questions', []))} ข้อ")
            with col_act:
                if st.button("🎮 เลือกชุดนี้", key=f"select_quiz_{idx}"):
                    st.session_state.active_questions = qz.get('questions', [])
                    st.success("โหลดชุดข้อสอบเรียบร้อยแล้ว! พร้อมเข้าเล่นที่หน้าแผนที่")
                    st.session_state.current_page = "map"
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# PAGE 4: BATTLE
elif st.session_state.current_page == "battle":
    st.markdown("## ⚔️ การต่อสู้ด้วยเวทมนตร์แห่งปัญญา")
    if st.button("⬅️ กลับสู่แผนที่"):
        st.session_state.current_page = "map"
        st.rerun()
        
    stage = st.session_state.get("selected_stage", 1)
    render_battle_game(st.session_state.get("active_questions", []), current_stage=stage)
