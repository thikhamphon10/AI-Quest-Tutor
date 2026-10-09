import streamlit as st
from game_engine import GameEngine


def render_battle_game(questions, current_stage=1):
    engine = GameEngine()
    if not questions:
        st.info("ยังไม่มีโจทย์สำหรับต่อสู้ ไปที่ AI Lesson Forge เพื่อสร้างโจทย์ก่อน")
        return

    monsters = st.session_state.monsters
    monster_info = monsters.get(current_stage, monsters[1])
    avatar_id = st.session_state.user_data.get("selected_avatar", "shadow_fox")
    avatar_info = st.session_state.avatars.get(avatar_id, list(st.session_state.avatars.values())[0])

    if "current_q_idx" not in st.session_state:
        st.session_state.current_q_idx = 0
    if "monster_hp" not in st.session_state:
        st.session_state.monster_hp = monster_info["hp"]
        st.session_state.monster_max_hp = monster_info["max_hp"]
    if "last_action_effect" not in st.session_state:
        st.session_state.last_action_effect = None
    if "battle_answered" not in st.session_state:
        st.session_state.battle_answered = False

    idx = st.session_state.current_q_idx
    if idx >= len(questions) or st.session_state.monster_hp <= 0:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#2B2347,#5B3F8C);border-radius:24px;padding:28px;color:white;text-align:center;margin:12px 0 18px">
          <div style="font-size:70px">🏆✨🎉</div><div style="font-size:28px;font-weight:800">QUEST CLEARED!</div>
          <div style="color:#E9D5FF;margin-top:5px">ชัยชนะเกิดจากความรู้และความพยายามของคุณ</div>
        </div>
        """, unsafe_allow_html=True)
        xp_earned = 50 * len(questions)
        coins_earned = 30 * len(questions)
        st.success(f"🎁 รางวัล: +{xp_earned} XP  ·  +{coins_earned} Coins  ·  +1 ⭐")
        if not st.session_state.get("reward_claimed", False):
            if st.button("🌟 รับรางวัลและกลับแผนที่", use_container_width=True):
                engine.add_reward(xp_earned, coins_earned, 1)
                engine.unlock_next_stage(current_stage)
                st.session_state.reward_claimed = True
                for key in ("current_q_idx", "monster_hp", "monster_max_hp", "last_action_effect", "battle_answered"):
                    st.session_state.pop(key, None)
                st.session_state.current_page = "map"
                st.rerun()
        else:
            if st.button("🗺️ กลับแผนที่", use_container_width=True):
                st.session_state.current_page = "map"
                st.rerun()
        return

    q = questions[idx]
    options = q.get("choices", q.get("options", []))
    correct_letter = str(q.get("correct_answer", q.get("answer", ""))).strip().upper()
    hp = max(0, st.session_state.monster_hp)
    max_hp = max(1, st.session_state.monster_max_hp)
    hp_pct = int(hp / max_hp * 100)

    col_hero, col_versus, col_enemy = st.columns([1, .45, 1], gap="medium")
    with col_hero:
        st.markdown(f"""
        <div style="background:linear-gradient(160deg,#FFFFFF,#F3E8FF);border:1px solid #DDD6FE;border-radius:23px;padding:20px;text-align:center;min-height:205px;box-shadow:0 10px 25px #4C1D9510">
          <div style="font-size:11px;font-weight:800;letter-spacing:1.5px;color:#7C3AED">YOUR HERO</div>
          <div style="font-size:76px;line-height:1.4;filter:drop-shadow(0 8px 8px #8B5CF622)">{avatar_info['icon']}</div>
          <div style="font-size:19px;font-weight:800;color:#2B2347">{avatar_info['name']}</div>
          <div style="font-size:12px;color:#77738F">{avatar_info['class']}</div>
          <div style="display:inline-block;margin-top:9px;padding:4px 10px;border-radius:999px;background:#EDE9FE;color:#6D28D9;font-size:11px;font-weight:700">{avatar_info['skill']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_versus:
        st.markdown("<div style='text-align:center;padding-top:72px;font-size:24px;font-weight:900;color:#C026D3;text-shadow:0 3px 12px #C026D333'>VS</div><div style='text-align:center;font-size:20px'>⚡</div>", unsafe_allow_html=True)
    with col_enemy:
        st.markdown(f"""
        <div style="background:linear-gradient(160deg,#FFFFFF,{monster_info['color']}16);border:1px solid {monster_info['color']}55;border-radius:23px;padding:20px;text-align:center;min-height:205px;box-shadow:0 10px 25px #4C1D9510">
          <div style="font-size:11px;font-weight:800;letter-spacing:1.5px;color:#B45309">BOSS ENCOUNTER</div>
          <div style="font-size:76px;line-height:1.4;filter:drop-shadow(0 8px 8px #8B5CF622)">{monster_info['icon']}</div>
          <div style="font-size:19px;font-weight:800;color:#2B2347">{monster_info['name']}</div>
          <div style="font-size:12px;color:#77738F">{monster_info['title']}</div>
          <div style="height:8px;background:#EEEAF7;border-radius:99px;overflow:hidden;margin-top:12px"><div style="height:8px;width:{hp_pct}%;background:linear-gradient(90deg,#FB7185,#F97316);border-radius:99px"></div></div>
          <div style="font-size:11px;color:#77738F;margin-top:5px">HP {hp} / {max_hp}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    st.progress((idx + 1) / len(questions), text=f"QUEST PROGRESS  ·  QUESTION {idx + 1} OF {len(questions)}")

    if st.session_state.last_action_effect == "hit":
        st.success("✨ โจมตีสำเร็จ! พลังความรู้เข้าเป้า")
    elif st.session_state.last_action_effect == "miss":
        st.warning("💡 ยังไม่ถูกนะ ลองอ่านเฉลยแล้วไปต่อได้เลย")

    st.markdown(f"<div style='background:white;border:1px solid #E8E1F5;border-radius:20px;padding:22px;margin:12px 0'><div style='font-size:11px;font-weight:800;letter-spacing:1px;color:#8B5CF6'>KNOWLEDGE CHALLENGE</div><div style='font-size:21px;font-weight:700;color:#2B2347;margin-top:7px'>{q.get('question','')}</div></div>", unsafe_allow_html=True)

    if not st.session_state.battle_answered:
        selected_option = st.radio("เลือกคำตอบที่ถูกต้อง", options, key=f"battle_option_{current_stage}_{idx}")
        if st.button("🪄  CAST SPELL / ส่งคำตอบ", type="primary", use_container_width=True):
            if correct_letter in ("A", "B", "C", "D") and options:
                correct_index = ord(correct_letter) - ord("A")
                correct_text = options[correct_index] if correct_index < len(options) else correct_letter
            else:
                correct_text = correct_letter
            damage = max(1, int(max_hp / len(questions)))
            if selected_option == correct_text or selected_option == correct_letter:
                st.session_state.monster_hp = max(0, st.session_state.monster_hp - damage)
                st.session_state.last_action_effect = "hit"
                st.toast("ตอบถูก! มอนสเตอร์ได้รับความเสียหาย", icon="⚡")
            else:
                st.session_state.last_action_effect = "miss"
            st.session_state.battle_answered = True
            st.rerun()
    else:
        if correct_letter in ("A", "B", "C", "D") and options:
            correct_index = ord(correct_letter) - ord("A")
            correct_text = options[correct_index] if correct_index < len(options) else correct_letter
        else:
            correct_text = correct_letter
        if st.session_state.last_action_effect == "miss":
            st.markdown(f"<div style='background:#FFF7ED;border:1px solid #FED7AA;border-radius:14px;padding:13px;color:#9A3412'><b>คำตอบที่ถูก:</b> {correct_text}</div>", unsafe_allow_html=True)
        if q.get("explanation"):
            st.info(f"📖 ทำความเข้าใจ: {q['explanation']}")
        if st.button("➡️ ไปข้อถัดไป", type="primary", use_container_width=True):
            st.session_state.current_q_idx += 1
            st.session_state.battle_answered = False
            st.rerun()
