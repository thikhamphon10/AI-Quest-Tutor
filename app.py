import streamlit as st
from ai_engine import generate_questions
from pdf_processor import extract_text_from_pdf
from game_engine import GameEngine
from games.battle import render_battle_game

# Page Configuration
st.set_page_config(page_title="AI Quest Tutor - เกมติวแฟนตาซี", page_icon="🐾", layout="wide")

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
    
    .avatar-img {
        width: 90px;
        height: 90px;
        border-radius: 50%;
        background-color: #FFE5EC;
        padding: 5px;
        border: 3px solid #FF80BF;
        transition: transform 0.3s ease;
    }
    
    .avatar-img:hover {
        transform: scale(1.1);
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .pulse-anim {
        animation: pulse 2s infinite;
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

# Initialize Logic
engine = GameEngine()
user = st.session_state.user_data

if "current_page" not in st.session_state:
    st.session_state.current_page = "map"

# Header Status Bar
st.markdown(f"""
<div class='status-bar'>
    <span>🏰 Level: {user['level']}</span>
    <span>⭐ Stars: {user['stars']}</span>
    <span>🪙 Coins: {user['coins']}</span>
    <span>✨ XP: {user['xp']} / {user['max_xp']}</span>
</div>
""", unsafe_allow_html=True)

# Navigation / Sidebar
with st.sidebar:
    st.title("🐾 AI Quest Tutor")
    st.caption("ติวสนุกด้วยภารกิจพิชิตเวทมนตร์")
    
    st.subheader("👤 ตัวละครของคุณ")
    avatars = st.session_state.avatars
    selected = st.selectbox("เลือกคู่หูผจญภัย:", list(avatars.keys()), format_func=lambda x: avatars[x]["name"])
    st.session_state.user_data["selected_avatar"] = selected
    st.image(avatars[selected]["img"], width=80)
    st.caption(avatars[selected]["desc"])
    
    st.markdown("---")
    if st.button("🗺️ หน้าหลัก / แผนที่", use_container_width=True):
        st.session_state.current_page = "map"
        st.rerun()
        
    if st.button("📚 สร้างบทเรียนจาก AI", use_container_width=True):
        st.session_state.current_page = "ai_generator"
        st.rerun()

# Page 1: Map / Stage Selection
if st.session_state.current_page == "map":
    st.markdown("## 🗺️ แผนที่โลกแห่งการเรียนรู้ (World Map)")
    st.write("เลือกด่านมอนสเตอร์เพื่อเริ่มภารกิจการต่อสู้ด้วยวิชาความรู้!")

    cols = st.columns(3)
    for stage_id in [1, 2, 3]:
        with cols[stage_id - 1]:
            is_unlocked = stage_id in user["unlocked_stages"]
            monster = st.session_state.monsters[stage_id]
            
            st.markdown(f"<div class='kawaii-card' style='text-align: center; opacity: {1.0 if is_unlocked else 0.5};'>", unsafe_allow_html=True)
            st.image(monster["img"], width=80)
            st.markdown(f"#### ด่านที่ {stage_id}: {monster['name']}")
            
            if is_unlocked:
                st.success("ปลดล็อกแล้ว")
                if st.button(f"⚔️ ท้าประลองด่าน {stage_id}", key=f"btn_stage_{stage_id}", use_container_width=True):
                    if "active_questions" not in st.session_state or not st.session_state.active_questions:
                        st.warning("⚠️ กรุณาสร้างโจทย์บทเรียนที่เมนู 'สร้างบทเรียนจาก AI' ในแถบด้านข้างก่อน!")
                    else:
                        st.session_state.selected_stage = stage_id
                        st.session_state.current_page = "battle"
                        st.rerun()
            else:
                st.info("🔒 ยังไม่ปลดล็อก")
            st.markdown("</div>", unsafe_allow_html=True)

# Page 2: AI Generator (Gemini Integration)
elif st.session_state.current_page == "ai_generator":
    st.markdown("## 📚 สร้างโจทย์ติวหนังสือด้วย AI (Gemini)")
    
    tab1, tab2 = st.tabs(["📝 ป้อนข้อความ/เนื้อหา", "📄 อัปโหลดไฟล์ PDF"])
    
    content = ""
    with tab1:
        content = st.text_area("กรอกเนื้อหาที่ต้องการให้ AI ออกข้อสอบ:", height=150, placeholder="เช่น เนื้อหาชีววิทยา เรื่อง การสังเคราะห์ด้วยแสง...")
    
    with tab2:
        uploaded_file = st.file_uploader("อัปโหลดเอกสาร PDF", type=["pdf"])
        if uploaded_file:
            content = extract_text_from_pdf(uploaded_file)
            st.success("อ่านไฟล์ PDF เรียบร้อยแล้ว!")

    col_diff, col_num = st.columns(2)
    with col_diff:
        difficulty = st.selectbox("ระดับความยาก:", ["ง่าย (Easy)", "ปานกลาง (Medium)", "ยาก (Hard)"])
    with col_num:
        num_q = st.slider("จำนวนข้อสอบ:", min_value=3, max_value=10, value=5)

    if st.button("🪄 ร่ายคาถา generarate โจทย์!", type="primary", use_container_width=True):
        if not content.strip():
            st.error("กรุณากรอกเนื้อหาหรืออัปโหลดไฟล์ PDF ก่อนทำการสร้างโจทย์")
        else:
            with st.spinner("🔮 กำลังอัญเชิญ Gemini AI สร้างบทเรียน..."):
               difficulty_map = {
    "ง่าย (Easy)": "easy",
    "ปานกลาง (Medium)": "medium",
    "ยาก (Hard)": "hard",
}

questions = generate_questions(
    material=content,
    n=num_q,
)
                if questions:
                    st.session_state.active_questions = questions
                    st.success(f"สร้างโจทย์เรียบร้อยแล้ว {len(questions)} ข้อ! พร้อมเข้าสู่การต่อสู้")
                    if st.button("⚔️ ไปที่แผนที่เพื่อเริ่มลุย!"):
                        st.session_state.current_page = "map"
                        st.rerun()

# Page 3: Interactive Battle System
elif st.session_state.current_page == "battle":
    st.markdown("## ⚔️ การต่อสู้ด้วยเวทมนตร์แห่งปัญญา")
    if st.button("⬅️ ถอนตัวกลับแผนที่"):
        st.session_state.current_page = "map"
        st.rerun()
        
    stage = st.session_state.get("selected_stage", 1)
    render_battle_game(st.session_state.get("active_questions", []), current_stage=stage)
