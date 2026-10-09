import streamlit as st
from ai_engine import generate_questions, AIError
from pdf_processor import extract_text
from game_engine import GameEngine
from games.battle import render_battle_game

st.set_page_config(
    page_title="AI Quest Tutor | Fantasy Academy",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600;700;800&display=swap');
:root { --ink:#201B3C; --muted:#77738F; --pink:#F472B6; --violet:#8B5CF6; }
html, body, [class*="css"] { font-family:'Kanit',sans-serif; }
.stApp { background: radial-gradient(circle at 10% 0%, #FCE7F3 0, transparent 28%), radial-gradient(circle at 95% 10%, #DBEAFE 0, transparent 25%), #F7F7FC; color:var(--ink); }
.block-container { max-width: 1250px; padding-top: 1.5rem; padding-bottom: 3rem; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#211B3D 0%,#35275B 100%); }
[data-testid="stSidebar"] * { color:#F8F7FF !important; }
[data-testid="stSidebar"] .stButton>button { background:#5B4B8A !important; border:1px solid #7668A6 !important; }
.hero-banner { padding:28px 30px; border-radius:26px; background:linear-gradient(120deg,#292044 0%,#553B83 55%,#A855A5 100%); color:white; box-shadow:0 16px 35px #3A285B26; margin-bottom:22px; position:relative; overflow:hidden; }
.hero-banner:after { content:'✦  ✧  ✦'; position:absolute; right:28px; top:16px; font-size:30px; color:#FDE68A; opacity:.9; }
.hero-kicker { font-size:12px; letter-spacing:2px; text-transform:uppercase; color:#E9D5FF; font-weight:700; }
.hero-title { font-size:clamp(27px,4vw,40px); font-weight:800; line-height:1.15; margin:7px 0; }
.hero-sub { color:#EDE9FE; font-size:15px; max-width:690px; }
.stat-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:18px 0 26px; }
.stat-card { background:#FFFFFF; border:1px solid #E9E5F5; border-radius:18px; padding:15px 17px; box-shadow:0 7px 20px #33245C0A; }
.stat-label { font-size:12px; color:#817B9B; margin-bottom:5px; }
.stat-value { font-size:23px; color:#2B2347; font-weight:800; }
.section-heading { font-size:24px; font-weight:800; color:#2B2347; margin:8px 0 4px; }
.section-sub { color:#77738F; font-size:14px; margin-bottom:16px; }
.quest-card { background:linear-gradient(160deg,#FFFFFF 0%,#FAF8FF 100%); border:1px solid #E8E1F5; border-radius:22px; padding:20px; box-shadow:0 9px 24px #39245C0C; min-height:245px; }
.character-orb { height:112px; width:112px; margin:3px auto 12px; display:flex; align-items:center; justify-content:center; border-radius:30px; font-size:62px; background:linear-gradient(145deg,#FFFFFF,#EDE9FE); border:1px solid #DDD6FE; box-shadow:inset 0 2px 0 #FFFFFF,0 10px 22px #4C1D9517; }
.pill { display:inline-block; border-radius:999px; padding:5px 10px; font-size:11px; font-weight:700; background:#F3E8FF; color:#6D28D9; }
.feature-card { background:white; border:1px solid #E9E5F5; border-radius:18px; padding:17px; height:100%; }
.feature-icon { font-size:25px; margin-bottom:7px; }
.stButton>button { border-radius:13px !important; border:0 !important; background:linear-gradient(100deg,#8B5CF6,#C026D3) !important; color:white !important; font-weight:700 !important; min-height:43px; box-shadow:0 6px 15px #8B5CF62B; transition:transform .15s ease,box-shadow .15s ease; }
.stButton>button:hover { transform:translateY(-2px); box-shadow:0 10px 20px #8B5CF63B; }
.stTextArea textarea, .stTextInput input, [data-baseweb="select"] > div { border-radius:13px !important; }
[data-testid="stProgressBar"] > div > div { background:linear-gradient(90deg,#A78BFA,#F472B6); }
hr { border-color:#E7E2F1; }
@media(max-width:700px) { .stat-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } .hero-banner { padding:23px 20px; } .hero-banner:after { display:none; } }
</style>
""", unsafe_allow_html=True)

engine = GameEngine()
if "current_page" not in st.session_state:
    st.session_state.current_page = "map"
if "active_questions" not in st.session_state:
    st.session_state.active_questions = []
user = st.session_state.user_data

# Header / player status
st.markdown("""
<div class="hero-banner">
  <div class="hero-kicker">Fantasy Academy • Learn by playing</div>
  <div class="hero-title">AI QUEST <span style="color:#FDE68A">TUTOR</span> ⚔️</div>
  <div class="hero-sub">เปลี่ยนบทเรียนให้เป็นภารกิจ อัปเลเวลจากความรู้ แล้วออกไปพิชิตโลกแฟนตาซีในสไตล์ของคุณ</div>
</div>
""", unsafe_allow_html=True)

xp_pct = int(min(100, user['xp'] / max(1, user['max_xp']) * 100))
st.markdown(f"""
<div class="stat-grid">
 <div class="stat-card"><div class="stat-label">🏰 PLAYER LEVEL</div><div class="stat-value">Lv. {user['level']}</div></div>
 <div class="stat-card"><div class="stat-label">✨ EXPERIENCE</div><div class="stat-value">{user['xp']} <span style="font-size:12px;color:#999">/ {user['max_xp']} XP</span></div><div style="height:5px;background:#EEEAF7;border-radius:8px;margin-top:9px"><div style="height:5px;width:{xp_pct}%;background:linear-gradient(90deg,#8B5CF6,#F472B6);border-radius:8px"></div></div></div>
 <div class="stat-card"><div class="stat-label">⭐ STARS EARNED</div><div class="stat-value">{user['stars']}</div></div>
 <div class="stat-card"><div class="stat-label">🪙 COINS</div><div class="stat-value">{user['coins']}</div></div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<div style='font-size:25px;font-weight:800;letter-spacing:-.5px'>⚔️ QUEST MENU</div><div style='color:#C4B5FD;font-size:12px;margin-bottom:18px'>Your next level starts here</div>", unsafe_allow_html=True)
    avatars = st.session_state.avatars
    avatar_ids = list(avatars.keys())
    current_avatar = user.get("selected_avatar", avatar_ids[0])
    if current_avatar not in avatar_ids:
        current_avatar = avatar_ids[0]
    selected = st.selectbox("เลือกตัวละคร", avatar_ids, index=avatar_ids.index(current_avatar), format_func=lambda key: f"{avatars[key]['icon']}  {avatars[key]['name']}")
    user["selected_avatar"] = selected
    a = avatars[selected]
    st.markdown(f"<div style='background:#FFFFFF12;border:1px solid #FFFFFF25;border-radius:18px;padding:16px;text-align:center;margin:5px 0 18px'><div style='font-size:62px;line-height:1.25'>{a['icon']}</div><div style='font-size:17px;font-weight:700'>{a['name']}</div><div style='color:#D8B4FE;font-size:12px'>{a['class']}</div><div style='font-size:12px;margin-top:8px'>{a['desc']}</div><div style='display:inline-block;background:#FFFFFF18;border-radius:20px;padding:4px 10px;margin-top:10px;font-size:11px'>SKILL: {a['skill']}</div></div>", unsafe_allow_html=True)
    if st.button("🗺️  World Map", use_container_width=True):
        st.session_state.current_page = "map"
        st.rerun()
    if st.button("📚  AI Lesson Forge", use_container_width=True):
        st.session_state.current_page = "ai_generator"
        st.rerun()
    st.markdown("<div style='margin-top:20px;color:#C4B5FD;font-size:11px'>TIP: วางเนื้อหาจากชีทเรียน แล้วให้ AI เปลี่ยนเป็นภารกิจได้เลย</div>", unsafe_allow_html=True)

# World map
if st.session_state.current_page == "map":
    st.markdown('<div class="section-heading">🗺️ World Map</div><div class="section-sub">เลือกสนามประลองที่ปลดล็อก แล้วเตรียมตัวด้วยพลังแห่งความรู้</div>', unsafe_allow_html=True)
    monsters = st.session_state.monsters
    cols = st.columns(3, gap="medium")
    for stage_id in [1, 2, 3]:
        monster = monsters[stage_id]
        unlocked = stage_id in user.get("unlocked_stages", [1])
        with cols[stage_id - 1]:
            opacity = "1" if unlocked else ".68"
            status = "AVAILABLE" if unlocked else "LOCKED"
            status_style = "background:#D1FAE5;color:#047857" if unlocked else "background:#F3F4F6;color:#6B7280"
            st.markdown(f"""
            <div class="quest-card" style="opacity:{opacity}">
              <div style="display:flex;justify-content:space-between;align-items:center"><span class="pill">STAGE 0{stage_id}</span><span style="font-size:10px;font-weight:800;{status_style};padding:5px 9px;border-radius:999px">{status}</span></div>
              <div class="character-orb" style="background:linear-gradient(145deg,#FFFFFF,{monster['color']}26);border-color:{monster['color']}66">{monster['icon']}</div>
              <div style="text-align:center;font-size:19px;font-weight:800;color:#2B2347">{monster['name']}</div>
              <div style="text-align:center;color:#77738F;font-size:13px;margin-top:3px">{monster['title']}</div>
              <div style="text-align:center;color:#9A94B0;font-size:11px;margin-top:11px">BOSS HP · {monster['max_hp']}</div>
            </div>
            """, unsafe_allow_html=True)
            if unlocked:
                if st.button(f"⚔️  Enter Stage {stage_id}", key=f"stage_{stage_id}", use_container_width=True):
                    if not st.session_state.active_questions:
                        st.warning("สร้างชุดคำถามจากเมนู AI Lesson Forge ก่อน แล้วค่อยเริ่มต่อสู้")
                    else:
                        st.session_state.selected_stage = stage_id
                        st.session_state.reward_claimed = False
                        for key in ("current_q_idx", "monster_hp", "monster_max_hp", "last_action_effect", "battle_answered"):
                            st.session_state.pop(key, None)
                        st.session_state.current_page = "battle"
                        st.rerun()
            else:
                st.button("🔒 Clear previous stage first", key=f"locked_{stage_id}", disabled=True, use_container_width=True)

    st.markdown("<div style='height:10px'></div><div class='section-heading'>✨ Your adventure toolkit</div><div class='section-sub'>ทุกอย่างที่ต้องใช้เพื่อเริ่มติวแบบเกมอยู่ตรงนี้</div>", unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3, gap="medium")
    with f1:
        st.markdown('<div class="feature-card"><div class="feature-icon">🧠</div><b>AI Question Forge</b><div style="font-size:13px;color:#77738F;margin-top:6px">เปลี่ยนเนื้อหาที่เรียนให้กลายเป็นโจทย์ปรนัย 4 ตัวเลือก</div></div>', unsafe_allow_html=True)
    with f2:
        st.markdown('<div class="feature-card"><div class="feature-icon">⚡</div><b>Battle to Learn</b><div style="font-size:13px;color:#77738F;margin-top:6px">ตอบถูกเพื่อโจมตีมอนสเตอร์ ตอบผิดก็ได้เรียนรู้จากเฉลย</div></div>', unsafe_allow_html=True)
    with f3:
        st.markdown('<div class="feature-card"><div class="feature-icon">🏆</div><b>Earn & Level Up</b><div style="font-size:13px;color:#77738F;margin-top:6px">สะสม XP เหรียญ และดาว เพื่อปลดล็อกด่านต่อไป</div></div>', unsafe_allow_html=True)

# AI question generator
elif st.session_state.current_page == "ai_generator":
    st.markdown('<div class="section-heading">📚 AI Lesson Forge</div><div class="section-sub">วางเนื้อหาจากชีทเรียน หรืออัปโหลด PDF แล้วให้ AI สร้างโจทย์สำหรับสนามประลอง</div>', unsafe_allow_html=True)
    left, right = st.columns([1.35, 0.85], gap="large")
    with left:
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["📝 Paste lesson notes", "📄 Upload PDF"])
        with tab1:
            text_content = st.text_area("เนื้อหาบทเรียน", height=230, placeholder="วางเนื้อหาจากชีทเรียนตรงนี้...\n\nตัวอย่าง: Photosynthesis คือกระบวนการที่พืชใช้พลังงานแสง...", key="lesson_text")
        with tab2:
            uploaded_file = st.file_uploader("เลือกไฟล์ PDF", type=["pdf"], key="lesson_pdf")
            st.caption("PDF ที่เป็นข้อความเลือกคัดลอกได้จะอ่านได้ดีที่สุด")
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="feature-card"><div class="feature-icon">🪄</div><b style="font-size:18px">Quest Settings</b><div style="color:#77738F;font-size:13px;margin:4px 0 16px">ปรับรูปแบบภารกิจของคุณ</div>', unsafe_allow_html=True)
        difficulty = st.selectbox("ระดับความยาก", ["ง่าย (Easy)", "ปานกลาง (Medium)", "ยาก (Hard)"])
        num_q = st.slider("จำนวนข้อ", min_value=3, max_value=10, value=5)
        st.markdown("<div style='background:#F5F3FF;border-radius:13px;padding:12px;font-size:12px;color:#6D28D9;margin:10px 0 15px'>✨ เคล็ดลับ: ใส่เนื้อหาที่ชัดเจน เพื่อให้คำถามอ้างอิงจากบทเรียนของคุณ</div>", unsafe_allow_html=True)
        create_clicked = st.button("🪄  Forge my questions", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if create_clicked:
        content = (text_content or "").strip()
        if not content and uploaded_file is not None:
            try:
                content = extract_text(uploaded_file)
            except Exception as e:
                st.error(f"อ่าน PDF ไม่สำเร็จ: {e}")
        if not content:
            st.warning("กรุณาวางเนื้อหาหรือเลือกไฟล์ PDF ก่อนสร้างโจทย์")
        else:
            with st.spinner("✨ กำลังหลอมรวมบทเรียนเป็นภารกิจ..."):
                try:
                    questions = generate_questions(material=content, n=num_q)
                    difficulty_map = {"ง่าย (Easy)": "easy", "ปานกลาง (Medium)": "medium", "ยาก (Hard)": "hard"}
                    chosen = difficulty_map[difficulty]
                    rewards = {"easy": (15, 10), "medium": (20, 15), "hard": (30, 25)}
                    for question in questions:
                        question["difficulty"] = chosen
                        question["damage"], question["xp"] = rewards[chosen]
                    st.session_state.active_questions = questions
                    for key in ("current_q_idx", "monster_hp", "monster_max_hp", "last_action_effect", "battle_answered"):
                        st.session_state.pop(key, None)
                    st.success(f"สำเร็จ! สร้างภารกิจ {len(questions)} ข้อเรียบร้อย พร้อมเข้าต่อสู้แล้ว")
                except AIError as e:
                    st.error(f"สร้างโจทย์ไม่สำเร็จ: {e}")
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {type(e).__name__}: {e}")

    if st.session_state.active_questions:
        st.markdown("---")
        st.markdown(f"<div class='feature-card'><span class='pill'>QUEST READY</span><h3 style='margin:10px 0 4px'>⚔️ มีโจทย์พร้อมเล่น {len(st.session_state.active_questions)} ข้อ</h3><div style='color:#77738F;font-size:13px'>กลับไปที่ World Map เพื่อเลือกมอนสเตอร์และเริ่มภารกิจ</div></div>", unsafe_allow_html=True)
        if st.button("🗺️  ไปเลือกด่าน", use_container_width=True):
            st.session_state.current_page = "map"
            st.rerun()

elif st.session_state.current_page == "battle":
    st.markdown('<div class="section-heading">⚔️ Battle Arena</div><div class="section-sub">ใช้ความรู้เป็นอาวุธ ทุกคำตอบพาคุณเข้าใกล้ชัยชนะ</div>', unsafe_allow_html=True)
    if st.button("← กลับแผนที่"):
        st.session_state.current_page = "map"
        st.rerun()
    render_battle_game(st.session_state.get("active_questions", []), current_stage=st.session_state.get("selected_stage", 1))
