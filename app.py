import hashlib
import json
import os

import streamlit as st

import ai_engine
import visuals as V
from ai_engine import generate_questions_from_text
from game_engine import AVATAR_ORDER, AVATARS, LAST_STAGE, MONSTERS, WEAPONS, GameEngine, stage_status
from games.battle import render_battle_game, start_battle
from pdf_processor import extract_text_from_pdf

# ตั้งค่าหน้าเว็บ Streamlit
st.set_page_config(page_title="AI Quest Tutor - เกมติวแฟนตาซี", page_icon="🐾", layout="wide")

# สร้างโฟลเดอร์สำหรับเก็บชุดข้อสอบไว้ใช้ซ้ำ (เพื่อประหยัดโควตา API)
SAVED_QUIZZES_DIR = "saved_quizzes"
try:
    os.makedirs(SAVED_QUIZZES_DIR, exist_ok=True)
except OSError:
    pass


def save_quiz_to_local(title: str, questions: list) -> bool:
    """บันทึกชุดข้อสอบลงในไฟล์ JSON สำหรับเรียกใช้ซ้ำ (คืน False ถ้าเขียนไฟล์ไม่ได้)"""
    try:
        filename = hashlib.md5(title.encode("utf-8")).hexdigest()[:10] + ".json"
        with open(os.path.join(SAVED_QUIZZES_DIR, filename), "w", encoding="utf-8") as f:
            json.dump({"title": title, "questions": questions}, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def load_saved_quizzes():
    """ดึงชุดข้อสอบทั้งหมดที่เคยบันทึกไว้ใน Local Storage"""
    quizzes = []
    if os.path.isdir(SAVED_QUIZZES_DIR):
        for fn in sorted(os.listdir(SAVED_QUIZZES_DIR)):
            if fn.endswith(".json"):
                try:
                    with open(os.path.join(SAVED_QUIZZES_DIR, fn), "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict) and isinstance(data.get("questions"), list):
                        quizzes.append(data)
                except (OSError, ValueError):
                    pass
    return quizzes


def load_question_bank():
    try:
        with open(os.path.join(os.path.dirname(__file__), "question_bank.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


V.inject_css()

# เรียกใช้ Game Engine (โหลดความก้าวหน้าจากไฟล์เซฟ ถ้ามี)
engine = GameEngine()
user = st.session_state.user_data

if "current_page" not in st.session_state:
    st.session_state.current_page = "map"


def goto(page: str):
    st.session_state.current_page = page
    st.rerun()


# ---------------------------------------------------------
# แถบเมนูด้านข้าง (Sidebar)
# ---------------------------------------------------------
with st.sidebar:
    st.title("🐾 AI Quest Tutor")
    st.caption("ติวสนุกด้วยภารกิจพิชิตเวทมนตร์")

    st.subheader("👤 ตัวละครของคุณ")
    owned = user["unlocked_avatars"]
    selected = st.selectbox("เลือกคู่หูผจญภัย:", owned, index=owned.index(user["selected_avatar"]),
                            format_func=lambda x: AVATARS[x]["name"] + " · " + AVATARS[x]["class"])
    if selected != user["selected_avatar"]:
        engine.select_avatar(selected)
        st.rerun()
    V.html(f'<div style="text-align:center"><img src="{V.hero_img(selected)}" width="110" alt="{AVATARS[selected]["name"]}"></div>', st.sidebar)
    st.caption(AVATARS[selected]["desc"])
    st.caption("✨ " + AVATARS[selected]["perk"])
    player_name = st.text_input("ชื่อนักผจญภัย", value=user.get("player_name", "นักผจญภัย"), max_chars=24, key="player_name_input")
    if player_name.strip() and player_name.strip() != user.get("player_name"):
        user["player_name"] = player_name.strip()
        engine.save()
    weapons_owned = user.get("unlocked_weapons", ["star_wand"])
    weapon_ids = [w for w in weapons_owned if w in WEAPONS] or ["star_wand"]
    current_weapon = user.get("selected_weapon", "star_wand")
    chosen_weapon = st.selectbox("อาวุธประจำตัว", weapon_ids,
        index=weapon_ids.index(current_weapon) if current_weapon in weapon_ids else 0,
        format_func=lambda w: f'{WEAPONS[w]["icon"]} {WEAPONS[w]["name"]}', key="weapon_select")
    if chosen_weapon != current_weapon:
        engine.select_weapon(chosen_weapon)
        st.rerun()
    with st.expander("🛍️ ร้านค้าอาวุธ"):
        for wid, w in WEAPONS.items():
            st.caption(f'{w["icon"]} **{w["name"]}** · {w["desc"]} · {w["cost"]} เหรียญ')
            if wid in user.get("unlocked_weapons", []):
                st.caption("มีแล้ว" + (" · กำลังใช้" if wid == user.get("selected_weapon") else ""))
            elif st.button(f'ซื้อ {w["name"]} ({w["cost"]} 🪙)', key=f"buy_weapon_{wid}", disabled=user["coins"] < w["cost"], use_container_width=True):
                ok, msg = engine.buy_weapon(wid)
                if ok:
                    st.rerun()
                else:
                    st.warning(msg)

    st.markdown("---")
    if st.button("🗺️ หน้าหลัก / แผนที่", use_container_width=True):
        goto("map")
    if st.button("📚 สร้างบทเรียนใหม่ (AI)", use_container_width=True):
        goto("ai_generator")
    if st.button("📁 คลังข้อสอบที่บันทึกไว้", use_container_width=True):
        goto("saved_quizzes")
    if st.button("📚 คลังข้อสอบแยกตามวิชา", use_container_width=True):
        goto("question_bank")
    if st.button("📝 สมุดข้อผิดพลาด", use_container_width=True):
        goto("error_notebook")

    st.markdown("---")
    with st.expander("💾 สำรอง / กู้คืนความก้าวหน้า"):
        st.caption("ความก้าวหน้าบันทึกอัตโนมัติ (รีเฟรชแล้วยังอยู่ตราบที่ลิงก์ยังมี ?p=...) "
                   "แต่บน Streamlit Cloud เซิร์ฟเวอร์อาจล้างไฟล์เมื่อรีสตาร์ท จึงแนะนำให้ดาวน์โหลดไฟล์สำรองไว้")
        st.download_button("⬇️ ดาวน์โหลดไฟล์เซฟ", data=json.dumps(engine.snapshot(), ensure_ascii=False),
                           file_name="ai_quest_save.json", mime="application/json", use_container_width=True)
        up = st.file_uploader("กู้คืนจากไฟล์เซฟ", type=["json"], key="restore_up")
        if up is not None and st.button("♻️ กู้คืน", use_container_width=True):
            try:
                ok = engine.restore(json.loads(up.getvalue().decode("utf-8")))
            except (ValueError, UnicodeDecodeError):
                ok = False
            if ok:
                st.session_state.pop("battle", None)
                st.session_state.current_page = "map"
                st.rerun()
            else:
                st.error("ไฟล์เซฟไม่ถูกต้อง")

if not st.session_state.get("save_ok", True):
    st.warning("⚠️ เซิร์ฟเวอร์บันทึกไฟล์เซฟไม่ได้ในขณะนี้ ความก้าวหน้ายังเล่นต่อได้ แต่ควรดาวน์โหลดไฟล์เซฟจากเมนูด้านข้างเก็บไว้")

page = st.session_state.current_page
if page != "battle":
    V.hud(user, AVATARS)


# ---------------------------------------------------------
# ไดอะล็อกรายละเอียดด่าน: คลิกมอนสเตอร์ -> ดูข้อมูล -> เริ่มภารกิจ
# ---------------------------------------------------------
def _stage_detail(stage_id: int):
    m = MONSTERS[stage_id]
    ok, why = stage_status(user, stage_id)
    V.html(f'<img class="dlg-mon" src="{V.monster_img(m["img"])}" alt="{m["name"]}">')
    st.markdown(f"### ด่านที่ {stage_id}: {m['name']}")
    st.caption(f"{m['title']} · {m['place']}")
    st.write(m["desc"])
    V.html(f'<div class="tagrow"><span class="tg2">HP {m["max_hp"]}</span>'
           f'<span class="tg2">{V.stars_html(user["stage_stars"].get(str(stage_id), 0))}</span>'
           f'<span class="tg2">รางวัล: {m["reward"]}</span></div>')
    if not ok:
        st.info(f"🔒 {why}")
        return
    qs = st.session_state.active_questions
    if not qs:
        st.warning("ยังไม่ได้เลือกข้อสอบ กรุณาสร้างบทเรียนใหม่หรือเลือกจากคลังข้อสอบก่อนเข้าเล่น")
        if st.button("📚 ไปสร้างบทเรียน", use_container_width=True, key=f"dlg_gen_{stage_id}"):
            goto("ai_generator")
        return
    st.caption(f"ใช้ชุดข้อสอบ: {st.session_state.quiz_title or 'บทเรียนปัจจุบัน'} ({len(qs)} ข้อ)")
    pick = st.radio("เลือกคู่หูของภารกิจนี้", owned_now(), index=owned_now().index(user["selected_avatar"]),
                    format_func=lambda a: AVATARS[a]["name"], horizontal=True, key=f"dlg_hero_{stage_id}")
    if pick != user["selected_avatar"]:
        engine.select_avatar(pick)
    if st.button("⚔️ เริ่มภารกิจ!", type="primary", use_container_width=True, key=f"dlg_go_{stage_id}"):
        st.session_state.selected_stage = stage_id
        start_battle(stage_id, qs)
        goto("battle")


def owned_now():
    return list(user["unlocked_avatars"])


def open_stage(stage_id: int):
    if hasattr(st, "dialog"):
        st.dialog(f"รายละเอียดด่านที่ {stage_id}")(_stage_detail)(stage_id)
    else:  # Streamlit เก่ากว่า 1.37: แสดงแบบกล่องพับแทน
        with st.expander(f"รายละเอียดด่านที่ {stage_id}", expanded=True):
            _stage_detail(stage_id)


def _hero_detail(aid: str):
    a = AVATARS[aid]
    V.html(f'<img class="dlg-mon" src="{V.hero_img(aid, "cheer")}" alt="{a["name"]}">')
    st.markdown(f"### {a['name']} · {a['class']}")
    st.write(a["desc"])
    V.html(f'<div class="tagrow"><span class="tg2">เวท: {a["skill"]}</span><span class="tg2">{a["perk"]}</span></div>')
    if aid in user["unlocked_avatars"]:
        if aid == user["selected_avatar"]:
            st.success("กำลังใช้ตัวละครนี้อยู่")
        elif st.button("✅ เลือกใช้ตัวละครนี้", type="primary", use_container_width=True, key=f"use_{aid}"):
            engine.select_avatar(aid)
            st.rerun()
    else:
        can = user["coins"] >= a["cost"]
        st.caption(f"ราคาปลดล็อก {a['cost']} เหรียญ (คุณมี {user['coins']})")
        if st.button(f"🔓 ปลดล็อก ({a['cost']} เหรียญ)", type="primary", use_container_width=True,
                     disabled=not can, key=f"buy_{aid}"):
            ok, msg = engine.unlock_avatar(aid)
            if ok:
                engine.select_avatar(aid)
                st.rerun()
            st.error(msg)
        if not can:
            st.info("เล่นด่านเพื่อสะสมเหรียญเพิ่มได้เลย!")


def open_hero(aid: str):
    if hasattr(st, "dialog"):
        st.dialog(f"ตัวละคร: {AVATARS[aid]['name']}")(_hero_detail)(aid)
    else:
        with st.expander(f"ตัวละคร: {AVATARS[aid]['name']}", expanded=True):
            _hero_detail(aid)


# ---------------------------------------------------------
# PAGE 1: แผนที่เลือกด่าน (MAP)
# ---------------------------------------------------------
if page == "map":
    V.page_head(f"ยินดีต้อนรับ {user.get('player_name', 'นักผจญภัย')} 🌟", "เลือกด่านมอนสเตอร์เพื่อเริ่มภารกิจการต่อสู้ด้วยวิชาความรู้!", user["selected_avatar"], "cheer")
    V.world_banner(user["selected_avatar"], st.session_state.quiz_title)

    qs = st.session_state.active_questions
    if not qs:
        st.info("📚 เริ่มจากเลือกบทเรียนก่อนนะ — สร้างข้อสอบด้วย AI หรือเลือกจากคลังข้อสอบ แล้วกลับมาท้าประลองมอนสเตอร์")
        c1, c2 = st.columns(2)
        if c1.button("🪄 สร้างบทเรียนด้วย AI", type="primary", use_container_width=True):
            goto("ai_generator")
        if c2.button("📁 เลือกจากคลังข้อสอบ", use_container_width=True):
            goto("saved_quizzes")
    else:
        nxt = next((s for s in range(1, LAST_STAGE + 1)
                    if stage_status(user, s)[0] and user["stage_stars"].get(str(s), 0) == 0), None)
        if st.button(f"🚀 เริ่มเกม" + (f" · ด่านที่ {nxt}" if nxt else ""), type="primary", use_container_width=True, key="start_game"):
            open_stage(nxt or 1)
        st.caption(f"ชุดข้อสอบที่ใช้อยู่: {st.session_state.quiz_title or 'บทเรียนปัจจุบัน'} ({len(qs)} ข้อ)")

    st.subheader("🗺️ ด่านผจญภัย")
    nxt_stage = next((s for s in range(1, LAST_STAGE + 1)
                      if stage_status(user, s)[0] and user["stage_stars"].get(str(s), 0) == 0), None)
    for row in range(0, LAST_STAGE, 3):
        cols = st.columns(3)
        for col, sid in zip(cols, range(row + 1, min(row + 4, LAST_STAGE + 1))):
            m = MONSTERS[sid]
            ok, _why = stage_status(user, sid)
            stars = user["stage_stars"].get(str(sid), 0)
            state = "locked" if not ok else "cleared" if stars > 0 else "current" if sid == nxt_stage else "open"
            with col:
                V.html(V.stage_card(sid, m, state, stars))
                label = "🔒 ดูเงื่อนไข" if not ok else "🔍 ดูมอนสเตอร์ / เริ่มภารกิจ"
                if st.button(label, key=f"btn_stage_{sid}", use_container_width=True):
                    open_stage(sid)

    st.subheader("🐾 คู่หูผจญภัย")
    cols = st.columns(4)
    for col, aid in zip(cols, AVATAR_ORDER):
        with col:
            V.html(V.hero_card(aid, AVATARS[aid], aid in user["unlocked_avatars"], aid == user["selected_avatar"]))
            own = aid in user["unlocked_avatars"]
            label = "ใช้อยู่ ✓" if aid == user["selected_avatar"] else ("ดูรายละเอียด" if own else f"🔒 {AVATARS[aid]['cost']} เหรียญ")
            if st.button(label, key=f"btn_hero_{aid}", use_container_width=True):
                open_hero(aid)

    with st.expander("📈 สถิติของฉัน"):
        c1, c2, c3 = st.columns(3)
        c1.metric("🔥 คอมโบสูงสุด", user["best_streak"])
        ta = user["total_answered"]
        c2.metric("🎯 ตอบถูกรวม", f"{user['total_correct']}/{ta}")
        c3.metric("🎯 ความแม่นยำ", f"{(user['total_correct'] / ta if ta else 0):.0%}")
        weak = sorted(user["topic_stats"].items(), key=lambda kv: kv[1]["correct"] / max(1, kv[1]["correct"] + kv[1]["wrong"]))
        for t, v in weak[:6]:
            tot = v["correct"] + v["wrong"]
            st.progress(v["correct"] / tot, text=f"{t} — ถูก {v['correct']}/{tot}")
        if not weak:
            st.caption("ยังไม่มีสถิติ เริ่มเล่นด่านแรกได้เลย")

# ---------------------------------------------------------
# PAGE 2: สร้างบทเรียนด้วย AI (AI GENERATOR)
# ---------------------------------------------------------
elif page == "ai_generator":
    V.page_head("สร้างโจทย์ติวหนังสือด้วย AI (Gemini)", "อัปโหลด PDF หรือวางเนื้อหา แล้วให้ AI ออกข้อสอบให้", user["selected_avatar"])

    tab1, tab2 = st.tabs(["📝 ป้อนข้อความ/เนื้อหา", "📄 อัปโหลดไฟล์ PDF"])

    content = ""
    with tab1:
        content = st.text_area("กรอกเนื้อหาที่ต้องการให้ออกข้อสอบ:", height=150,
                               placeholder="เช่น เนื้อหาชีววิทยา เรื่อง การสังเคราะห์ด้วยแสง...")

    with tab2:
        uploaded_file = st.file_uploader("อัปโหลดเอกสาร PDF", type=["pdf"])
        if uploaded_file:
            content = extract_text_from_pdf(uploaded_file)
            if content:
                st.success(f"อ่านไฟล์ PDF เรียบร้อยแล้ว! ({len(content):,} ตัวอักษร) ระบบจะใช้ PDF แทนข้อความที่พิมพ์")
            else:
                st.error("ไม่สามารถอ่านข้อความจากไฟล์ PDF นี้ได้ (อาจเป็นไฟล์สแกนที่ต้องใช้ OCR) ลองวางเนื้อหาในแท็บข้อความแทน")

    subject = st.selectbox("วิชา", ["ชีววิทยา", "ฟิสิกส์", "คณิตศาสตร์", "ภาษาอังกฤษ", "วิชาอื่น ๆ"])
    col_diff, col_num = st.columns(2)
    with col_diff:
        difficulty = st.selectbox("ระดับความยาก:", ["ง่าย", "ปานกลาง", "ยาก"], index=1)
    with col_num:
        num_q = st.selectbox("จำนวนข้อสอบที่ต้องการ:", [5, 10, 15, 20, 30, 40, 50], index=0)

    emphasis = st.text_input("หัวข้อที่อยากเน้น (ไม่บังคับ):", placeholder="เช่น สมการ, ประวัติศาสตร์สมัยอยุธยา")
    title_input = st.text_input("ตั้งชื่อชุดข้อสอบนี้ (สำหรับบันทึกไว้ใช้ซ้ำ):", value="บทเรียนเวทมนตร์")

    if st.button("🪄 ร่ายคาถาสร้างข้อสอบ", type="primary", use_container_width=True):
        if not content.strip():
            st.error("กรุณากรอกเนื้อหาหรืออัปโหลดไฟล์ PDF ก่อนทำการสร้างข้อสอบ")
        elif len(content.strip()) < 50:
            st.warning("เนื้อหาสั้นเกินไป กรุณาใส่อย่างน้อย 50 ตัวอักษร")
        else:
            with st.spinner("🔮 กำลังอัญเชิญ Gemini AI สร้างบทเรียน..."):
                questions = generate_questions_from_text(content, difficulty, num_q, emphasis)
            if questions:
                title = title_input.strip() or "บทเรียนเวทมนตร์"
                for q in questions:
                    q.setdefault("subject", subject)
                engine.set_quiz(title, questions)
                saved = save_quiz_to_local(title, questions)
                st.session_state.gen_done = {"n": len(questions), "asked": num_q, "saved": saved}
            else:
                st.session_state.gen_done = None
                err = ai_engine.last_error
                if "QUOTA_EXHAUSTED" in err:
                    st.error("❌ โควตา API ฟรีเต็ม กรุณาลองใหม่ภายหลัง หรือเลือกใช้ข้อสอบจาก ‘คลังข้อสอบที่บันทึกไว้’")
                elif err:
                    st.error(f"❌ สร้างข้อสอบไม่สำเร็จ: {err[:300]}")
                else:
                    st.error("❌ AI ไม่ได้ส่งข้อสอบกลับมา ลองใหม่อีกครั้งหรือใช้เนื้อหาที่ยาวขึ้น")

    # ปุ่มนี้อยู่นอก if ของปุ่มสร้างข้อสอบ (เดิมซ้อนอยู่ข้างในจึงกดไม่ติด)
    done = st.session_state.get("gen_done")
    if done:
        if done["n"] < done["asked"]:
            st.warning(f"⚠️ สร้างข้อสอบได้ {done['n']} ข้อ จากที่ขอ {done['asked']} ข้อ (อาจเพราะข้อจำกัดโควตา API)")
        else:
            st.success(f"🎉 สร้างข้อสอบสำเร็จครบถ้วน {done['n']} ข้อ!")
        st.caption("บันทึกเข้าคลังข้อสอบเรียบร้อยแล้ว" if done["saved"] else "สร้างสำเร็จ แต่บันทึกลงคลังไม่ได้ (เซิร์ฟเวอร์ไม่อนุญาตให้เขียนไฟล์)")
        if st.button("⚔️ ไปที่แผนที่เพื่อเริ่มลุย!", type="primary", use_container_width=True):
            st.session_state.gen_done = None
            goto("map")

# ---------------------------------------------------------
# PAGE 3: คลังข้อสอบที่บันทึกไว้ (SAVED QUIZZES)
# ---------------------------------------------------------
elif page == "saved_quizzes":
    V.page_head("คลังข้อสอบที่บันทึกไว้", "เล่นได้โดยไม่ต้องใช้ API Quota", user["selected_avatar"])
    quizzes = load_saved_quizzes()

    if not quizzes:
        st.info("ยังไม่มีชุดข้อสอบที่บันทึกไว้ คุณสามารถสร้างชุดข้อสอบใหม่ได้ที่เมนู ‘สร้างบทเรียนใหม่’")
        if st.button("🪄 ไปสร้างบทเรียน", type="primary"):
            goto("ai_generator")
    else:
        for idx, qz in enumerate(quizzes):
            with st.container(border=True):
                col_info, col_act = st.columns([3, 1])
                with col_info:
                    st.markdown(f"#### 📖 {qz.get('title', 'ชุดข้อสอบไม่มีชื่อ')}")
                    st.caption(f"จำนวนข้อสอบ: {len(qz.get('questions', []))} ข้อ")
                with col_act:
                    if st.button("🎮 เลือกชุดนี้", key=f"select_quiz_{idx}", use_container_width=True):
                        engine.set_quiz(str(qz.get("title", "")), qz.get("questions", []))
                        st.session_state.pop("battle", None)
                        st.toast("โหลดชุดข้อสอบเรียบร้อยแล้ว!", icon="📖")
                        goto("map")

# ---------------------------------------------------------
# PAGE 4: คลังข้อสอบเริ่มต้น แยกวิชา ใช้ได้โดยไม่เรียก AI
# ---------------------------------------------------------
elif page == "question_bank":
    V.page_head("คลังข้อสอบแยกตามวิชา 📚", "เลือกทำข้อสอบสำรองได้ทันที แม้ Gemini ใช้โควตาครบแล้ว", user["selected_avatar"])
    all_bank = load_question_bank()
    subjects = sorted({q.get("subject", "ทั่วไป") for q in all_bank})
    if not all_bank:
        st.error("ไม่พบไฟล์ question_bank.json กรุณาตรวจสอบว่าอัปโหลดไฟล์โปรเจกต์ครบ")
    else:
        subject = st.selectbox("เลือกวิชา", subjects)
        filtered = [q for q in all_bank if q.get("subject") == subject]
        topics = sorted({q.get("topic", "ทั่วไป") for q in filtered})
        topic = st.selectbox("เลือกบท/หัวข้อ", ["ทุกหัวข้อ"] + topics)
        if topic != "ทุกหัวข้อ":
            filtered = [q for q in filtered if q.get("topic") == topic]
        st.info(f"มีข้อสอบ {len(filtered)} ข้อ · ใช้งานได้โดยไม่ต้องเรียก Gemini API")
        st.caption("คลังเริ่มต้นมีตัวอย่างข้อสอบพื้นฐาน สามารถเพิ่มข้อสอบได้ในไฟล์ question_bank.json")
        if st.button("🎮 เล่นชุดนี้", type="primary", use_container_width=True, disabled=not filtered):
            title = f"คลังข้อสอบ: {subject}" + (f" · {topic}" if topic != "ทุกหัวข้อ" else "")
            engine.set_quiz(title, filtered)
            st.session_state.pop("battle", None)
            goto("map")
        with st.expander("ดูตัวอย่างข้อสอบ"):
            for i, q in enumerate(filtered, 1):
                st.markdown(f"**{i}. {q['question']}**")
                st.caption(" · ".join(q.get("options", [])))

# ---------------------------------------------------------
# PAGE 5: สมุดข้อผิดพลาด
# ---------------------------------------------------------
elif page == "error_notebook":
    V.page_head("สมุดข้อผิดพลาด 📝", "รวบรวมข้อที่ตอบผิดเพื่อกลับมาทบทวน", user["selected_avatar"])
    errors = user.get("error_notebook", [])
    if not errors:
        st.success("ยังไม่มีข้อผิดพลาดให้ทบทวน ลองทำข้อสอบแล้วระบบจะบันทึกข้อที่ตอบผิดให้อัตโนมัติ ✨")
    else:
        pending = [x for x in errors if not x.get("reviewed")]
        c1, c2 = st.columns(2)
        c1.metric("ข้อผิดพลาดทั้งหมด", len(errors))
        c2.metric("ยังไม่ได้ทบทวน", len(pending))
        for i, item in enumerate(reversed(errors)):
            with st.container(border=True):
                st.markdown(f"**{item.get('question', '')}**")
                st.caption(f"{item.get('subject', 'ไม่ระบุ')} · {item.get('topic', 'ทั่วไป')}")
                st.write(f"คำตอบของคุณ: {item.get('wrong_answer', '-')}")
                st.write(f"เฉลย: {item.get('correct_answer', '-')}")
                with st.expander("ดูคำอธิบาย"):
                    st.write(item.get("explanation") or "ไม่มีคำอธิบาย")
                if not item.get("reviewed"):
                    if st.button("✅ ทบทวนแล้ว", key=f"review_error_{i}"):
                        item["reviewed"] = True
                        engine.save()
                        st.rerun()
        if st.button("🧹 ล้างสมุดข้อผิดพลาด", type="secondary"):
            user["error_notebook"] = []
            engine.save()
            st.rerun()

# ---------------------------------------------------------
# PAGE 6: ฉากการต่อสู้ (BATTLE)
# ---------------------------------------------------------
elif page == "battle":
    V.page_head("การต่อสู้ด้วยเวทมนตร์แห่งปัญญา", "ตอบถูกเพื่อร่ายเวทโจมตี ตอบผิดจะเสียพลัง", user["selected_avatar"], "cheer")
    V.hud(user, AVATARS)
    if st.button("⬅️ กลับสู่แผนที่"):
        st.session_state.pop("battle", None)
        goto("map")

    stage = st.session_state.get("selected_stage", 1)
    render_battle_game(st.session_state.get("active_questions", []), current_stage=stage)

else:
    goto("map")
