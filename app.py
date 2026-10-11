import hashlib
import json
import os
import random

import streamlit as st

import ai_engine
import visuals as V
from ai_engine import generate_questions_from_text
from game_engine import AVATAR_ORDER, AVATARS, LAST_STAGE, MONSTERS, WEAPONS, GameEngine, qkey, stage_status
from games import review
from games.battle import render_battle_game, start_battle, available_question_count, STAGE_MODES
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


DIFF_LEVELS = ["ง่าย", "ปานกลาง", "ยาก"]
_DIFF_ALIAS = {"easy": "ง่าย", "medium": "ปานกลาง", "hard": "ยาก"}


def norm_difficulty(v) -> str:
    v = str(v or "").strip()
    v = _DIFF_ALIAS.get(v.lower(), v)
    return v if v in DIFF_LEVELS else "ปานกลาง"


def load_question_bank():
    """คลังข้อสอบรวม: question_bank.json (สำเร็จรูป) + ชุดที่ Gemini สร้างแล้วบันทึกไว้ใน saved_quizzes/ (ตัดข้อซ้ำ)
    ทุกข้อมีฟิลด์ subject / subtopic(บทเรียน) / difficulty(ง่าย|ปานกลาง|ยาก) / source"""
    out, seen = [], set()

    def add(q, subject, subtopic, source):
        if not isinstance(q, dict) or not str(q.get("question", "")).strip():
            return
        k = qkey(q["question"])
        if k in seen:
            return
        seen.add(k)
        item = dict(q)
        item["subject"] = str(q.get("subject") or subject)[:60]
        item["subtopic"] = str(q.get("subtopic") or q.get("topic") or subtopic)[:60]
        item["difficulty"] = norm_difficulty(q.get("difficulty"))
        item["source"] = q.get("source") or source
        out.append(item)

    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "question_bank.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        for q in data if isinstance(data, list) else []:
            add(q, "ทั่วไป", "ทั่วไป", "คลังข้อสอบสำเร็จรูป")
    except (OSError, ValueError):
        pass
    for qz in load_saved_quizzes():
        title = str(qz.get("title", "ชุดที่บันทึกไว้"))
        for q in qz.get("questions", []):
            add(q, "ชุดที่บันทึกไว้", title, "AI สร้าง")
    return out


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
    if st.button("📊 สรุปคะแนน / จุดอ่อนรายวิชา", use_container_width=True):
        goto("summary")
    if st.button("🎒 ตัวละครและอาวุธ", use_container_width=True):
        goto("character")

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
if page not in ("battle", "review"):
    V.hud(user, AVATARS)


def nav():
    """เมนูลัดด้านบน 2 แถว x 3 ปุ่ม (CSS บังคับไม่ให้ตกบรรทัดบนมือถือ) ใช้ได้โดยไม่ต้องเปิด sidebar"""
    try:
        box = st.container(key="topnav")
    except TypeError:  # Streamlit เก่ากว่า 1.39 ไม่มี key
        box = st.container()
    rows = [[("map", "🗺️ แผนที่"), ("question_bank", "📚 คลังข้อสอบ"), ("ai_generator", "🪄 สร้างด้วย AI")],
            [("error_notebook", "📝 สมุดผิด"), ("summary", "📊 สรุปผล"), ("character", "🎒 ตัวละคร")]]
    with box:
        for row in rows:
            for col, (pg, label) in zip(st.columns(3), row):
                with col:
                    if st.button(label, key=f"nav_{pg}", use_container_width=True,
                                 type="primary" if page == pg else "secondary"):
                        goto(pg)


if page not in ("battle", "review"):
    nav()


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
    remaining = available_question_count(qs)
    st.caption(f"ชุดข้อสอบ: {st.session_state.quiz_title or 'บทเรียนปัจจุบัน'} · เหลือ {remaining}/{len(qs)} ข้อที่ยังไม่เคยใช้")
    if remaining <= 0:
        st.warning("ข้อสอบชุดนี้ใช้ครบแล้ว จึงไม่สามารถเริ่มด่านด้วยข้อเก่าได้")
        if st.button("🔄 เริ่มรอบใหม่โดยรีเซ็ตประวัติข้อสอบ", key=f"reset_run_{stage_id}", use_container_width=True):
            st.session_state.used_question_ids = []
            engine.save()
            st.rerun()
        return
    mode_title, mode_desc = STAGE_MODES.get(stage_id, STAGE_MODES[1])
    st.info(f"รูปแบบด่าน: {mode_title} — {mode_desc}")
    count_options = [n for n in [5, 10, 15, 20, 30, 40, 50] if n <= remaining]
    if remaining not in count_options:
        count_options.append(remaining)
    preferred = st.session_state.get("selected_question_count", 5)
    count_index = min(range(len(count_options)), key=lambda i: abs(count_options[i] - min(preferred, remaining)))
    question_count = st.selectbox("จำนวนข้อในด่านนี้", count_options, index=count_index, key=f"stage_count_{stage_id}")
    pick = st.radio("เลือกคู่หูของภารกิจนี้", owned_now(), index=owned_now().index(user["selected_avatar"]),
                    format_func=lambda a: AVATARS[a]["name"], horizontal=True, key=f"dlg_hero_{stage_id}")
    if pick != user["selected_avatar"]:
        engine.select_avatar(pick)
    if st.button("⚔️ เริ่มภารกิจ!", type="primary", use_container_width=True, key=f"dlg_go_{stage_id}"):
        st.session_state.selected_stage = stage_id
        st.session_state.selected_question_count = question_count
        start_battle(stage_id, qs, question_count)
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
        st.caption(f"ชุดข้อสอบ: {st.session_state.quiz_title or 'บทเรียนปัจจุบัน'} · เหลือ {available_question_count(qs)}/{len(qs)} ข้อที่ยังไม่เคยใช้")
        if st.button("🔄 เริ่มรอบใหม่ (อนุญาตให้สุ่มข้อเดิมอีกครั้ง)", key="reset_question_history"):
            st.session_state.used_question_ids = []
            engine.save()
            st.success("รีเซ็ตประวัติข้อสอบแล้ว เริ่มผจญภัยใหม่ได้เลย")
            st.rerun()

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
    lesson = st.text_input("บทเรียน (ไม่บังคับ):", max_chars=60, placeholder="เช่น พันธุกรรม, บทที่ 3")
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
                    q["difficulty"] = norm_difficulty(q.get("difficulty") or difficulty)
                    if lesson.strip():
                        q["subtopic"] = lesson.strip()  # ใช้จัดหมวดบทเรียนในคลังข้อสอบ
                    q.setdefault("source", "AI สร้าง")
                engine.set_quiz(title, questions)
                saved = save_quiz_to_local(title, questions)
                st.session_state.gen_done = {"n": len(questions), "asked": num_q, "saved": saved}
            else:
                st.session_state.gen_done = None
                err = ai_engine.last_error
                if "QUOTA_EXHAUSTED" in err:
                    st.session_state.quota_hit = True  # แสดงกล่องแจ้งเตือน 429 + ปุ่มกลับคลังด้านล่าง
                elif err:
                    st.error(f"❌ สร้างข้อสอบไม่สำเร็จ: {err[:300]}")
                else:
                    st.error("❌ AI ไม่ได้ส่งข้อสอบกลับมา ลองใหม่อีกครั้งหรือใช้เนื้อหาที่ยาวขึ้น")

    # Error 429 (โควตา/อัตราการเรียกเต็ม): แจ้งเตือนชัดเจน และกลับไปทำข้อสอบในคลังได้ทันที
    if st.session_state.get("quota_hit") or ai_engine.last_error_kind == "quota":
        st.warning("⏳ โควตา Gemini API เต็มชั่วคราว (Error 429) — ไม่ได้เกิดจากตัวคุณ "
                   "ลองสร้างใหม่ภายหลัง หรือเล่นต่อด้วยข้อสอบในคลังได้เลย ไม่ต้องใช้ AI")
        q1, q2 = st.columns(2)
        if q1.button("📚 ไปทำข้อสอบในคลัง", type="primary", use_container_width=True, key="quota_bank"):
            st.session_state.quota_hit = False
            goto("question_bank")
        if q2.button("ปิดข้อความนี้", use_container_width=True, key="quota_dismiss"):
            st.session_state.quota_hit = False
            ai_engine.last_error_kind = ""
            st.rerun()

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
    V.page_head("คลังข้อสอบแยกตามวิชา 📚", "เลือกวิชา บทเรียน ความยาก และจำนวนข้อ เล่นได้ทันทีแม้ Gemini ใช้โควตาครบแล้ว", user["selected_avatar"])
    all_bank = load_question_bank()
    subjects = sorted({q.get("subject", "ทั่วไป") for q in all_bank})
    if not all_bank:
        st.error("ไม่พบไฟล์ question_bank.json กรุณาตรวจสอบว่าอัปโหลดไฟล์โปรเจกต์ครบ หรือสร้างข้อสอบด้วย AI ก่อน")
    else:
        subject = st.selectbox("เลือกวิชา", subjects)
        filtered = [q for q in all_bank if q.get("subject") == subject]
        topics = sorted({q.get("subtopic") or q.get("topic", "ทั่วไป") for q in filtered})
        topic = st.selectbox("เลือกบท/หัวข้อ", ["ทุกหัวข้อ"] + topics)
        if topic != "ทุกหัวข้อ":
            filtered = [q for q in filtered if (q.get("subtopic") or q.get("topic", "ทั่วไป")) == topic]
        cnt = {d: sum(1 for q in filtered if q["difficulty"] == d) for d in DIFF_LEVELS}
        V.html(f'<span class="pill e">ง่าย {cnt["ง่าย"]}</span><span class="pill m">ปานกลาง {cnt["ปานกลาง"]}</span>'
               f'<span class="pill h">ยาก {cnt["ยาก"]}</span>'
               f'<span class="pill ai">AI สร้าง {sum(1 for q in filtered if q.get("source") == "AI สร้าง")}</span>')
        diff_pick = st.selectbox("ระดับความยาก", ["ทุกระดับ"] + DIFF_LEVELS)
        if diff_pick != "ทุกระดับ":
            filtered = [q for q in filtered if q["difficulty"] == diff_pick]
        st.info(f"มีข้อสอบ {len(filtered)} ข้อ · ใช้งานได้โดยไม่ต้องเรียก Gemini API")
        max_q = len(filtered)
        choices = [n for n in [5, 10, 15, 20, 30, 40, 50] if n <= max_q]
        if max_q and max_q not in choices:
            choices.append(max_q)
        if not choices:
            choices = [1]
        count = st.selectbox("🎯 จำนวนข้อในการเล่นครั้งนี้", choices, index=min(1, len(choices)-1),
                             help="ระบบจะสุ่มข้อสอบจากหัวข้อที่เลือกใหม่ทุกครั้งที่เริ่มเล่น")
        st.caption("เลือกจำนวนข้อได้ในแต่ละด่าน · ไม่ใช้โควตา Gemini · ข้อที่ AI สร้างจะถูกเก็บเข้าคลังนี้อัตโนมัติ")
        if st.button("🎮 เลือกชุดข้อสอบนี้", type="primary", use_container_width=True, disabled=not filtered):
            title = f"คลังข้อสอบ: {subject}" + (f" · {topic}" if topic != "ทุกหัวข้อ" else "") + (f" · {diff_pick}" if diff_pick != "ทุกระดับ" else "")
            # เก็บทั้งคลังที่กรองแล้วไว้เป็น pool; จำนวนข้อเลือกแยกในแต่ละด่าน
            engine.set_quiz(title[:80], filtered)
            st.session_state.selected_question_count = count
            st.session_state.pop("battle", None)
            goto("map")
        if st.button("🪄 ไม่พอ? สร้างข้อใหม่ด้วย AI", use_container_width=True, key="bank_ai"):
            goto("ai_generator")
        with st.expander("ดูตัวอย่างข้อสอบ"):
            for i, q in enumerate(filtered[:50], 1):
                st.markdown(f"**{i}. {q['question']}**")
                st.caption(f"หัวข้อ: {q.get('subtopic') or q.get('topic', 'ทั่วไป')} · ระดับ{q['difficulty']} · " + " · ".join(q.get("options", [])))
            if len(filtered) > 50:
                st.caption(f"แสดง 50 จาก {len(filtered)} ข้อ")

# ---------------------------------------------------------
# PAGE 5: สมุดข้อผิดพลาด
# ---------------------------------------------------------
elif page == "error_notebook":
    V.page_head("สมุดข้อผิดพลาด 📝", "รวบรวมข้อที่ตอบผิดเพื่อกลับมาทบทวน พร้อมเฉลยและคำอธิบาย", user["selected_avatar"])
    errors = user.get("error_notebook", [])
    if not errors:
        st.success("ยังไม่มีข้อผิดพลาดให้ทบทวน ลองทำข้อสอบแล้วระบบจะบันทึกข้อที่ตอบผิดให้อัตโนมัติ ✨")
    else:
        pending = [x for x in errors if not x.get("reviewed")]
        c1, c2 = st.columns(2)
        c1.metric("ข้อผิดพลาดทั้งหมด", len(errors))
        c2.metric("ยังไม่ได้ทบทวน", len(pending))
        subs = sorted({e.get("subject", "ไม่ระบุ") for e in errors})
        flt = st.selectbox("กรองตามวิชา", ["ทุกวิชา"] + subs)
        only = None if flt == "ทุกวิชา" else flt
        ids = review.pick_items(errors, only)
        if st.button(f"🔁 เริ่มทบทวนซ้ำ ({len(ids)} ข้อ)", type="primary", use_container_width=True, disabled=not ids, key="nb_review"):
            review.start(ids)
            goto("review")
        st.caption(f"ทบทวนรอบละไม่เกิน {review.MAX_ITEMS} ข้อ (ผิดบ่อยสุดก่อน) · ตอบถูกติดกัน 2 ครั้งถึงนับว่าทบทวนผ่าน "
                   "· ข้อเก่าที่ไม่มีตัวเลือกเก็บไว้ ทบทวนซ้ำไม่ได้ แต่ยังอ่านเฉลยและกด ‘ทบทวนแล้ว’ เองได้")
        shown = [(i, item) for i, item in enumerate(reversed(errors)) if only is None or item.get("subject") == only]
        for i, item in shown[:40]:
            with st.container(border=True):
                st.markdown(f"**{item.get('question', '')}**")
                st.caption(f"{item.get('subject', 'ไม่ระบุ')} · {item.get('topic', 'ทั่วไป')} · ผิด {item.get('wrong_count', 1)} ครั้ง"
                           + (" · ✅ ทบทวนแล้ว" if item.get("reviewed") else ""))
                st.write(f"คำตอบของคุณ: {item.get('wrong_answer', '-')}")
                st.write(f"เฉลย: {item.get('correct_answer', '-')}")
                with st.expander("ดูคำอธิบาย"):
                    st.write(item.get("explanation") or "ไม่มีคำอธิบาย")
                if not item.get("reviewed"):
                    if st.button("✅ ทบทวนแล้ว", key=f"review_error_{i}"):
                        item["reviewed"] = True
                        engine.save()
                        st.rerun()
        if len(shown) > 40:
            st.caption(f"แสดง 40 จาก {len(shown)} ข้อ (เลือกวิชาเพื่อกรองดูเพิ่ม)")
        if st.button("🧹 ล้างสมุดข้อผิดพลาด", type="secondary"):
            user["error_notebook"] = []
            engine.save()
            st.rerun()

elif page == "review":
    V.page_head("ทบทวนข้อที่เคยพลาด", "อ่านโจทย์ ตอบใหม่ แล้วดูคำอธิบาย", user["selected_avatar"])
    review.render()

# ---------------------------------------------------------
# PAGE 5.5: สรุปคะแนนและจุดอ่อนแยกตามวิชา
# ---------------------------------------------------------
elif page == "summary":
    V.page_head("สรุปคะแนนและจุดอ่อน 📊", "ดูว่าวิชาไหนเก่งแล้ว วิชาไหนควรกลับไปทบทวน", user["selected_avatar"])
    ss = user.get("subject_stats", {})
    if not ss:
        st.info("ยังไม่มีสถิติแยกตามวิชา ลองเล่นด่านสัก 1 ด่านก่อน ระบบจะสรุปให้ตรงนี้")
        c1, c2 = st.columns(2)
        if c1.button("🗺️ ไปแผนที่", type="primary", use_container_width=True, key="sum_map"):
            goto("map")
        if c2.button("📚 เลือกข้อสอบจากคลัง", use_container_width=True, key="sum_bank"):
            goto("question_bank")
    else:
        ta = user["total_answered"]
        m1, m2, m3 = st.columns(3)
        m1.metric("🎯 ความแม่นยำรวม", f"{(user['total_correct'] / ta if ta else 0):.0%}")
        m2.metric("📝 ตอบแล้ว", ta)
        m3.metric("🔥 คอมโบสูงสุด", user["best_streak"])
        rows = sorted((v["correct"] / (v["correct"] + v["wrong"]), subj, v) for subj, v in ss.items() if v["correct"] + v["wrong"] > 0)
        weakest = [r[1] for r in rows if r[0] < 0.6]
        if weakest:
            st.warning("📌 ควรทบทวนก่อน: " + ", ".join(weakest))
        else:
            st.success("🌟 ทุกวิชาแม่นยำตั้งแต่ 60% ขึ้นไป เยี่ยมมาก!")
        for k, (acc, subj, v) in enumerate(rows):  # วิชาที่อ่อนที่สุดอยู่บนสุด
            tot = v["correct"] + v["wrong"]
            level = "🔴 ต้องทบทวน" if acc < 0.6 else "🟢 แข็งแรง" if acc >= 0.8 else "🟡 พอใช้"
            with st.container(border=True):
                st.markdown(f"#### {subj}  {level}")
                st.progress(acc, text=f"ถูก {v['correct']} จาก {tot} ข้อ ({acc:.0%})")
                trows = sorted((tv["correct"] / (tv["correct"] + tv["wrong"]), t, tv) for t, tv in v["topics"].items()
                               if tv["correct"] + tv["wrong"] > 0)
                for tacc, t, tv in trows[:4]:
                    st.progress(tacc, text=f"หัวข้อ {t} — ถูก {tv['correct']}/{tv['correct'] + tv['wrong']}")
                if len(trows) > 4:
                    st.caption(f"…และอีก {len(trows) - 4} หัวข้อที่แม่นยำกว่า")
                n_m = sum(1 for e in user["error_notebook"] if not e.get("reviewed") and e.get("subject") == subj)
                if st.button(f"🎯 ฝึกจุดอ่อนวิชา {subj}" + (f" (มีข้อผิดค้าง {n_m})" if n_m else ""), key=f"sum_train_{k}",
                             use_container_width=True, type="primary" if acc < 0.6 else "secondary"):
                    weak = {t for tacc, t, tv in trows if tacc < 0.6 and tv["correct"] + tv["wrong"] >= 2} or {t for _a, t, _v in trows[:2]}
                    pool = [q for q in load_question_bank() if q.get("subject") == subj and (q.get("subtopic") in weak or q.get("topic") in weak)]
                    pool += [{"question": e["question"], "options": e["options"], "answer": e["options"][e["idx"]], "explanation": e["explanation"],
                              "topic": e["topic"], "subject": subj, "difficulty": "ปานกลาง"}
                             for e in user["error_notebook"] if not e.get("reviewed") and e.get("subject") == subj and review.can_review(e)]
                    seen, picked = set(), []
                    for q in pool:
                        if qkey(q["question"]) not in seen:
                            seen.add(qkey(q["question"]))
                            picked.append(q)
                    random.shuffle(picked)
                    if not picked:
                        st.info("ยังไม่มีข้อในคลังสำหรับหัวข้อที่อ่อน ลองสร้างข้อใหม่ด้วย AI ในวิชานี้ได้เลย")
                    else:
                        engine.set_quiz(f"ฝึกจุดอ่อน: {subj}"[:80], picked[:12])
                        st.session_state.selected_question_count = min(10, len(picked[:12]))
                        st.session_state.pop("battle", None)
                        st.toast(f"เตรียมข้อฝึก {len(picked[:12])} ข้อให้แล้ว!", icon="🎯")
                        goto("map")
        if st.button("📝 ไปสมุดข้อผิดพลาด", use_container_width=True, key="sum_notebook"):
            goto("error_notebook")

# ---------------------------------------------------------
# PAGE 5.7: ตัวละครและอาวุธ (ใช้งานบนมือถือ/iPad ได้โดยไม่ต้องเปิด sidebar)
# ---------------------------------------------------------
elif page == "character":
    V.page_head("ตัวละครและอาวุธ 🎒", "ตั้งชื่อนักผจญภัย เลือกคู่หู และเลือกอาวุธคู่ใจ", user["selected_avatar"], "cheer")
    name_in = st.text_input("ชื่อนักผจญภัย", value=user.get("player_name", "นักผจญภัย"), max_chars=24, key="char_name_input")
    if st.button("💾 บันทึกชื่อ", use_container_width=True, key="char_name_save"):
        if name_in.strip():
            user["player_name"] = name_in.strip()
            engine.save()
            st.toast("บันทึกชื่อแล้ว!", icon="✨")
            st.rerun()
        else:
            st.warning("ชื่อต้องมีอย่างน้อย 1 ตัวอักษร")
    st.subheader("🐾 คู่หูผจญภัย")
    for col, aid in zip(st.columns(4), AVATAR_ORDER):
        with col:
            V.html(V.hero_card(aid, AVATARS[aid], aid in user["unlocked_avatars"], aid == user["selected_avatar"]))
            own = aid in user["unlocked_avatars"]
            label = "ใช้อยู่ ✓" if aid == user["selected_avatar"] else ("ดูรายละเอียด" if own else f"🔒 {AVATARS[aid]['cost']} เหรียญ")
            if st.button(label, key=f"ch_hero_{aid}", use_container_width=True):
                open_hero(aid)
    st.subheader("⚔️ อาวุธ")
    st.caption(f"เหรียญของคุณ: {user['coins']}")
    for col, (wid, w) in zip(st.columns(len(WEAPONS)), WEAPONS.items()):
        own = wid in user["unlocked_weapons"]
        with col:
            V.html(f'<div class="hcard {"sel" if wid == user["selected_weapon"] else ""} {"" if own else "locked"}">'
                   f'<div style="font-size:2.4rem">{w["icon"]}</div><div class="nm">{V.esc(w["name"])}</div>'
                   f'<div class="tg">{V.esc(w["desc"])}</div></div>')
            if wid == user["selected_weapon"]:
                st.button("ใช้อยู่ ✓", key=f"ch_w_cur_{wid}", disabled=True, use_container_width=True)
            elif own:
                if st.button("เลือกใช้", key=f"ch_w_use_{wid}", use_container_width=True):
                    engine.select_weapon(wid)
                    st.rerun()
            else:
                if st.button(f"🔓 {w['cost']} เหรียญ", key=f"ch_w_buy_{wid}", use_container_width=True, disabled=user["coins"] < w["cost"]):
                    ok, msg = engine.buy_weapon(wid)
                    if ok:
                        st.toast(f"ปลดล็อก{w['name']}แล้ว!", icon="⚔️")
                        st.rerun()
                    st.warning(msg)
                if user["coins"] < w["cost"]:
                    st.caption(f"ขาดอีก {w['cost'] - user['coins']} เหรียญ")

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
