import streamlit as st
from game_engine import GameEngine

def render_battle_game(questions, current_stage=1):
    engine = GameEngine()
    
    if "current_q_idx" not in st.session_state:
        st.session_state.current_q_idx = 0
    if "monster_hp" not in st.session_state:
        monster_info = st.session_state.monsters.get(current_stage, {"name": "มอนสเตอร์", "hp": 100, "max_hp": 100})
        st.session_state.monster_hp = monster_info["hp"]
        st.session_state.monster_max_hp = monster_info["max_hp"]
    if "last_action_effect" not in st.session_state:
        st.session_state.last_action_effect = None

    idx = st.session_state.current_q_idx
    if idx >= len(questions) or st.session_state.monster_hp <= 0:
        # Victory Screen
        st.markdown("<div class='kawaii-card' style='text-align: center;'>", unsafe_allow_html=True)
        st.balloons()
        st.markdown("### 🎉 ชนะการต่อสู้แล้ว! 🎉")
        st.write("คุณได้ปราบมอนสเตอร์และได้รับความรู้อย่างคุ้มค่า!")
        
        # Reward calculation
        xp_earned = 50 * len(questions)
        coins_earned = 30 * len(questions)
        st.success(f"🎁 รางวัลที่ได้รับ: +{xp_earned} XP | +{coins_earned} Coins | +1 ⭐")
        
        if st.button("🌟 รับรางวัล & กลับสู่แผนที่", use_container_width=True):
            engine.add_reward(xp_earned, coins_earned, 1)
            engine.unlock_next_stage(current_stage)
            # Reset battle state
            del st.session_state.current_q_idx
            del st.session_state.monster_hp
            st.session_state.current_page = "map"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        return

    q = questions[idx]
    avatar_id = st.session_state.user_data["selected_avatar"]
    avatar_info = st.session_state.avatars[avatar_id]
    monster_info = st.session_state.monsters.get(current_stage, {"name": "มอนสเตอร์น่ารัก", "img": "https://img.icons8.com/isometric-3d/100/slime.png"})

    # Battle Arena Layout
    col_hero, col_vs, col_monster = st.columns([1, 0.5, 1])

    with col_hero:
        st.markdown(f"""
        <div class='kawaii-card' style='text-align: center;'>
            <img src='{avatar_info["img"]}' class='avatar-img pulse-anim'/>
            <h4>{avatar_info["name"]}</h4>
            <span style='color: #888;'>ผู้กล้าฝั่งเรา</span>
        </div>
        """, unsafe_allow_html=True)

    with col_vs:
        st.markdown("<h2 style='text-align: center; margin-top: 40px; color: #FF9AA2;'>VS</h2>", unsafe_allow_html=True)

    with col_monster:
        hp_percent = max(0, int((st.session_state.monster_hp / st.session_state.monster_max_hp) * 100))
        st.markdown(f"""
        <div class='kawaii-card' style='text-align: center;'>
            <img src='{monster_info["img"]}' class='avatar-img'/>
            <h4>{monster_info["name"]}</h4>
            <div style='background-color: #e0e0e0; border-radius: 10px; overflow: hidden; height: 15px; margin-top: 5px;'>
                <div style='background-color: #FF6B6B; width: {hp_percent}%; height: 100%; transition: width 0.5s;'></div>
            </div>
            <small>HP: {st.session_state.monster_hp} / {st.session_state.monster_max_hp}</small>
        </div>
        """, unsafe_allow_html=True)

    # Effect Notification
    if st.session_state.last_action_effect:
        if st.session_state.last_action_effect == "hit":
            st.markdown("<div style='background: #D4EDDA; padding: 8px; border-radius: 10px; text-align: center; color: #155724;'>✨ คาถาเวทมนตร์เข้าเป้า! มอนสเตอร์สูญเสีย HP!</div>", unsafe_allow_html=True)
        elif st.session_state.last_action_effect == "miss":
            st.markdown("<div style='background: #F8D7DA; padding: 8px; border-radius: 10px; text-align: center; color: #721C24;'>💨 การโจมตีร่ายเวทผิดพลาด! ตรวจสอบเฉลยด้านล่าง</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"### ❓ โจทย์ข้อที่ {idx + 1} / {len(questions)}")
    st.write(q.get("question", ""))

    options = q.get("options", [])
    selected_option = st.radio("เลือกคำตอบ:", options, key=f"q_{idx}")

    if st.button("🪄 ใช้เวทมนตร์โจมตี!", type="primary", use_container_width=True):
        correct_ans = q.get("answer", "")
        dmg_per_hit = int(st.session_state.monster_max_hp / len(questions))

        if selected_option == correct_ans:
            st.session_state.monster_hp -= dmg_per_hit
            st.session_state.last_action_effect = "hit"
            st.toast("🎯 ตอบถูกต้อง! ปล่อยพลังเวทมนตร์ใส่ศัตรู!", icon="✨")
            st.session_state.current_q_idx += 1
            st.rerun()
        else:
            st.session_state.last_action_effect = "miss"
            st.error(f"💡 เฉลย: {correct_ans}")
            if "explanation" in q:
                st.info(f"📖 คำอธิบายเพิ่มเติม: {q['explanation']}")
            st.session_state.current_q_idx += 1
