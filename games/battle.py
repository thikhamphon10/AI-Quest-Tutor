import html as _html
import math
import uuid
import random
import hashlib

import streamlit as st

import visuals as V
from game_engine import AVATARS, LAST_STAGE, MONSTERS, WEAPONS, GameEngine, avatar_mod, stage_status

LET = "ABCD"
WRONG_BASE = 20  # พลังที่ผู้เล่นเสียเมื่อตอบผิด 1 ข้อ (จาก 100)


def _esc(t) -> str:
    return _html.escape(str(t)).replace("\n", "<br>")


def norm_q(q: dict) -> dict:
    """รองรับทั้งรูปแบบ choices/correct_answer(A-D) และ options/answer(ข้อความ) ของ Gemini"""
    opts = [str(o).strip() for o in q.get("choices", q.get("options", []))]
    ans = str(q.get("correct_answer", q.get("answer", ""))).strip()
    idx = None
    if len(ans) == 1 and ans.upper() in LET and ord(ans.upper()) - 65 < len(opts):
        idx = ord(ans.upper()) - 65
    if idx is None:
        for i, o in enumerate(opts):
            if o == ans or o.casefold() == ans.casefold():
                idx = i
                break
    if idx is None and ans:
        for i, o in enumerate(opts):
            if ans.casefold() in o.casefold() or (len(o) > 2 and o.casefold() in ans.casefold()):
                idx = i
                break
    return {"question": str(q.get("question", "")).strip(), "options": opts, "idx": idx,
            "explanation": str(q.get("explanation", "")).strip(),
            "topic": (str(q.get("topic") or "ทั่วไป").strip() or "ทั่วไป")[:40],
            "subject": str(q.get("subject") or "ไม่ระบุ")[:60]}


def question_id(q: dict) -> str:
    """รหัสคงที่ของข้อสอบ ป้องกันข้อซ้ำแม้เรียงตัวเลือกใหม่"""
    raw = "|".join([str(q.get("subject", "")).strip().casefold(),
                    str(q.get("topic", "")).strip().casefold(),
                    " ".join(str(q.get("question", "")).split()).casefold()])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def available_question_count(questions: list) -> int:
    used = set(st.session_state.get("used_question_ids", []))
    valid = [q for q in questions if isinstance(q, dict) and str(q.get("question", "")).strip()]
    unique = {question_id(q): q for q in valid}
    return sum(1 for qid in unique if qid not in used)


def start_battle(stage_id: int, questions: list, count: int = None):
    """สุ่มโดยไม่คืนข้อสอบที่ใช้แล้วในรอบผจญภัยเดียวกัน"""
    valid = [q for q in questions if isinstance(q, dict) and str(q.get("question", "")).strip()]
    used = set(st.session_state.get("used_question_ids", []))
    unique = {question_id(q): q for q in valid}
    fresh = [q for qid, q in unique.items() if qid not in used]
    random.shuffle(fresh)
    if count is None:
        count = st.session_state.get("selected_question_count", min(10, len(fresh)))
    chosen = fresh[:max(1, min(int(count or 1), len(fresh)))] if fresh else []
    # บันทึกข้อที่ตอบจริงเท่านั้น; หากออกกลางด่าน ข้อที่ยังไม่เห็น/ยังไม่ตอบยังใช้ได้
    qs = [norm_q(q) for q in chosen]
    qs = [q for q in qs if q["question"] and len(q["options"]) >= 2]
    m = MONSTERS[stage_id]
    st.session_state.battle = {
        "uid": uuid.uuid4().hex[:8], "stage": stage_id, "qs": qs, "idx": 0,
        "monster_hp": m["hp"], "monster_max": m["max_hp"], "player_hp": 100,
        "answered": False, "last": None, "done": None, "result": None,
        "correct": 0, "wrong": 0, "streak": 0, "best_streak": 0, "xp": 0, "coins": 0,
        "topics": {}, "subjects": {}, "log": [],
    }


STAGE_MODES = {
    1: ("⚔️ ศึกฝึกหัด", "ตอบถูกเพื่อโจมตีมอนสเตอร์ กติกาพื้นฐาน"),
    2: ("🔥 ด่านคอมโบ", "ตอบถูกต่อเนื่องเพื่อเพิ่มพลังโจมตี ยิ่งคอมโบสูงยิ่งแรง"),
    3: ("🛡️ ด่านทำลายเกราะ", "ทุกคำตอบถูกลำดับที่ 2 จะปล่อยคลื่นเวทแรงพิเศษ"),
    4: ("💗 ด่านเอาตัวรอด", "ระวังคำตอบผิด เพราะมอนสเตอร์โจมตีแรงขึ้น"),
    5: ("💰 ล่าขุมทรัพย์", "ตอบถูกเพื่อรับเหรียญโบนัสสำหรับซื้ออาวุธ"),
    6: ("🐉 บอสหลายเฟส", "ทุก 3 ข้อบอสจะเปลี่ยนเฟส พลังโจมตีพิเศษเพิ่มขึ้น"),
}


def _finalize(engine: GameEngine, b: dict):
    if b["result"] is None:
        b["result"] = engine.finish_battle(b["stage"], b["done"] == "win", b["correct"], b["wrong"],
                                           b["xp"], b["coins"], b["best_streak"], b["topics"], b["subjects"])


def _answer(engine: GameEngine, b: dict, q: dict, pick: int):
    d = st.session_state.user_data
    mod = avatar_mod(d["selected_avatar"])
    n = len(b["qs"])
    ok = q["idx"] is not None and pick == q["idx"]
    t = b["topics"].setdefault(q["topic"], {"correct": 0, "wrong": 0})
    sj = b["subjects"].setdefault(q["subject"], {}).setdefault(q["topic"], {"correct": 0, "wrong": 0})
    if ok:
        need = max(3, math.ceil(n * 0.7))
        weapon_id = d.get("selected_weapon", "star_wand")
        weapon = WEAPONS.get(weapon_id, WEAPONS["star_wand"])
        base_dmg = math.ceil(b["monster_max"] / need) * mod["dmg_mult"] * weapon["damage"]
        stage = b["stage"]
        if stage == 2:
            base_dmg *= 1 + min(b["streak"], 4) * 0.12
        elif stage == 3 and (b["correct"] + 1) % 2 == 0:
            base_dmg *= 1.8
        elif stage == 6 and ((b["idx"] // 3) >= 1):
            base_dmg *= 1.25
        dmg = max(1, round(base_dmg))
        b["monster_hp"] = max(0, b["monster_hp"] - dmg)
        b["correct"] += 1
        b["streak"] += 1
        b["best_streak"] = max(b["best_streak"], b["streak"])
        b["xp"] += round((10 + 2 * min(b["streak"], 5)) * mod["xp_mult"])
        coin_reward = 10 if b["stage"] == 5 else 5
        b["coins"] += round(coin_reward * mod["coin_mult"])
        t["correct"] += 1
        sj["correct"] += 1
    else:
        penalty = WRONG_BASE + (10 if b["stage"] == 4 else 0)
        dmg = max(1, round(penalty * mod["wrong_mult"]))
        b["player_hp"] = max(0, b["player_hp"] - dmg)
        b["wrong"] += 1
        b["streak"] = 0
        t["wrong"] += 1
        sj["wrong"] += 1
    b["log"].append({"q": q, "pick": pick, "ok": ok})
    # ป้องกันการใช้ข้อเดิมซ้ำข้ามด่าน/รอบ และบันทึกลงไฟล์เซฟ
    used_ids = set(st.session_state.get("used_question_ids", []))
    used_ids.add(question_id(q))
    st.session_state.used_question_ids = sorted(used_ids)
    engine.save()
    if not ok:
        correct_text = q["options"][q["idx"]] if q["idx"] is not None else "เฉลยไม่ระบุ"
        wrong_text = q["options"][pick] if 0 <= pick < len(q["options"]) else "ไม่ระบุ"
        engine.record_error({
            "question": q["question"], "subject": q.get("subject", st.session_state.get("quiz_title", "ไม่ระบุ")),
            "topic": q.get("topic", "ทั่วไป"), "wrong_answer": wrong_text,
            "correct_answer": correct_text, "explanation": q.get("explanation", ""),
            "options": q["options"], "idx": q["idx"],  # เก็บตัวเลือกไว้ เพื่อทบทวนข้อนี้ซ้ำในโหมดทบทวนได้
        })
    b["last"] = {"ok": ok, "dmg": dmg}
    b["answered"] = True
    if b["monster_hp"] <= 0:
        b["done"] = "win"
    elif b["player_hp"] <= 0:
        b["done"] = "lose"
    elif b["idx"] + 1 >= n:
        b["done"] = "win"  # ตอบครบทุกข้อโดยฮีโร่ยังมีแรง = ผ่านด่าน (กติกาเดิม)
    if b["done"]:
        _finalize(engine, b)


def _result_panel(engine: GameEngine, b: dict):
    r = b["result"]
    win = b["done"] == "win"
    total = b["correct"] + b["wrong"]
    acc = b["correct"] / total if total else 0
    if win:
        st.success(f"🏆 ผ่านด่าน “{MONSTERS[b['stage']]['place']}” แล้ว!" + ("  ✨ ผ่านครั้งแรก รับโบนัสเพิ่ม" if r["first"] else ""))
    else:
        st.error("💤 ฮีโร่หมดแรงแล้ว ไม่เป็นไรนะ ทบทวนเฉลยด้านล่างแล้วลองใหม่ได้เลย!")
    V.html(V.rewards_html(r["xp"], r["coins"], r["stars"] if win else None, r["level"] if r["level_ups"] else None))
    if r["newly_unlocked"]:
        st.info(f"🔓 ปลดล็อกด่านใหม่: ด่านที่ {r['newly_unlocked']} “{MONSTERS[r['newly_unlocked']]['place']}”")
    c1, c2, c3 = st.columns(3)
    c1.metric("🎯 ความแม่นยำ", f"{acc:.0%}")
    c2.metric("✅ ถูก / ❌ ผิด", f"{b['correct']} / {b['wrong']}")
    c3.metric("🔥 คอมโบสูงสุด", b["best_streak"])
    st.progress(acc, text=f"ความแม่นยำรอบนี้ {acc:.0%}")

    # สรุปหัวข้อที่ควรทบทวน
    weak = [(t, v) for t, v in b["topics"].items() if v["wrong"] > 0]
    weak.sort(key=lambda x: x[1]["correct"] / max(1, x[1]["correct"] + x[1]["wrong"]))
    st.subheader("📌 หัวข้อที่ควรทบทวน")
    if weak:
        for t, v in weak:
            tot = v["correct"] + v["wrong"]
            st.progress(v["correct"] / tot, text=f"{t} — ถูก {v['correct']}/{tot}")
    else:
        st.success("เยี่ยมมาก! รอบนี้ไม่มีหัวข้อที่พลาดเลย 🌟")

    wrongs = [x for x in b["log"] if not x["ok"]]
    with st.expander(f"📖 เฉลยและคำอธิบาย ({len(b['log'])} ข้อ, ผิด {len(wrongs)} ข้อ)", expanded=bool(wrongs)):
        for i, x in enumerate(b["log"], 1):
            q = x["q"]
            right = f"{LET[q['idx']]}. {q['options'][q['idx']]}" if q["idx"] is not None else "-"
            mine = f"{LET[x['pick']]}. {q['options'][x['pick']]}"
            V.html(f"""<div class="reviewbox {'ok' if x['ok'] else ''}"><b>{i}. {_esc(q['question'])}</b><br>
                {'✅ คุณตอบ' if x['ok'] else '❌ คุณตอบ'}: {_esc(mine)}<br>{'' if x['ok'] else 'เฉลย: ' + _esc(right) + '<br>'}
                💡 {_esc(q['explanation'] or 'ไม่มีคำอธิบาย')}</div>""")

    if wrongs:
        st.caption(f"📝 ข้อที่ผิด {len(wrongs)} ข้อถูกจดลง ‘สมุดข้อผิดพลาด’ แล้ว ทบทวนซ้ำได้จากเมนู")
        if st.button("📝 ไปทบทวนที่สมุดข้อผิดพลาด", use_container_width=True, key="res_notebook"):
            st.session_state.pop("battle", None)
            st.session_state.current_page = "error_notebook"
            st.rerun()

    nxt = b["stage"] + 1
    can_next = win and nxt <= LAST_STAGE and stage_status(st.session_state.user_data, nxt)[0]
    cols = st.columns(3 if can_next else 2)
    i = 0
    if can_next:
        if cols[i].button("▶️ ด่านถัดไป", type="primary", use_container_width=True, key="res_next"):
            start_battle(nxt, st.session_state.active_questions)
            st.rerun()
        i += 1
    if cols[i].button("🔁 เล่นด่านนี้อีกครั้ง", use_container_width=True, key="res_retry",
                      type="secondary" if can_next else "primary"):
        start_battle(b["stage"], st.session_state.active_questions)
        st.rerun()
    if cols[i + 1].button("🗺️ กลับแผนที่", use_container_width=True, key="res_map"):
        st.session_state.pop("battle", None)
        st.session_state.current_page = "map"
        st.rerun()


def render_battle_game(questions, current_stage=1):
    engine = GameEngine()
    if not questions:
        st.info("ยังไม่มีโจทย์สำหรับต่อสู้ ไปที่ ‘สร้างบทเรียนใหม่’ หรือ ‘คลังข้อสอบ’ เพื่อเลือกโจทย์ก่อน")
        if st.button("📚 ไปสร้างบทเรียน", type="primary"):
            st.session_state.current_page = "ai_generator"
            st.rerun()
        return

    b = st.session_state.get("battle")
    if not b or b["stage"] != current_stage:
        start_battle(current_stage, questions)
        b = st.session_state.battle
    if not b["qs"]:
        st.warning("🎉 คุณใช้ข้อสอบในชุดนี้ครบแล้ว! ไม่มีการนำข้อเก่ามาสุ่มซ้ำ")
        st.write("เลือกชุดข้อสอบใหม่ หรือเริ่มรอบใหม่ด้วยปุ่ม ‘เริ่มรอบใหม่’ บนหน้าคลังข้อสอบ")
        if st.button("📚 ไปคลังข้อสอบ", type="primary", use_container_width=True):
            st.session_state.pop("battle", None)
            st.session_state.current_page = "question_bank"
            st.rerun()
        return

    d = st.session_state.user_data
    aid = d["selected_avatar"]
    avatar, monster = AVATARS[aid], MONSTERS[current_stage]
    n = len(b["qs"])
    idx = min(b["idx"], n - 1)
    q = b["qs"][idx]

    weapon = WEAPONS.get(d.get("selected_weapon", "star_wand"), WEAPONS["star_wand"])
    mode_title, mode_desc = STAGE_MODES.get(current_stage, STAGE_MODES[1])
    st.subheader(mode_title)
    st.caption(mode_desc)
    if current_stage == 6:
        st.info(f"🐉 เฟสบอส {min(3, b['idx'] // 3 + 1)} / 3 · {max(0, 3 - (b['idx'] % 3))} ข้อในเฟสนี้")
    st.caption(f"ด่าน {current_stage} · {monster['place']}  |  เวทของ{avatar['name']}: {avatar['skill']} · อาวุธ: {weapon['icon']} {weapon['name']}")
    V.html(V.battle_scene(b, monster, aid, avatar))

    if b["done"]:
        _result_panel(engine, b)
        return

    answered_n = b["idx"] + (1 if b["answered"] else 0)
    st.progress(answered_n / n, text=f"ภารกิจ · ข้อ {idx + 1} จาก {n}")
    if b["streak"] >= 2:
        V.html(f'<span class="combo">{V.BOLT} คอมโบ x{b["streak"]}!</span>')

    challenge_labels = {1: "KNOWLEDGE CHALLENGE", 2: "COMBO CHALLENGE", 3: "BREAK THE SHIELD", 4: "SURVIVAL CHALLENGE", 5: "TREASURE CHALLENGE", 6: "BOSS PHASE CHALLENGE"}
    V.html(f'<div class="qcard"><div class="lb">{challenge_labels.get(current_stage, "KNOWLEDGE CHALLENGE")}</div><div class="q">{_esc(q["question"])}</div></div>')

    if not b["answered"]:
        if current_stage in (2, 5, 6):
            # ด่านเหล่านี้ใช้การกดเลือกคำตอบโดยตรง แทนการเลือกแล้วกดส่งแบบด่านแรก
            if current_stage == 2:
                st.caption("⚡ รอบคอมโบ: กดคำตอบที่คิดว่าถูกได้ทันที")
                option_prefix = "⚡"
            elif current_stage == 5:
                st.caption("🎁 เลือกหีบสมบัติหนึ่งใบเพื่อเปิดคำตอบ")
                option_prefix = "🎁"
            else:
                st.caption("🐉 เลือกเวทโจมตีบอสในเฟสปัจจุบัน")
                option_prefix = "🐉"
            cols = st.columns(2)
            for i, option in enumerate(q["options"]):
                with cols[i % 2]:
                    if st.button(f"{option_prefix} {LET[i]}. {option}", key=f"choice_{b['uid']}_{idx}_{i}", use_container_width=True):
                        _answer(engine, b, q, i)
                        st.rerun()
        else:
            if current_stage == 3:
                shield_progress = b["correct"] % 2
                st.info("🛡️ เกราะเวท: " + ("ตอบถูกอีก 1 ครั้งเพื่อชาร์จคลื่นโจมตีพิเศษ" if shield_progress else "เกราะกำลังรอคำตอบถูกเพื่อเริ่มชาร์จ"))
            elif current_stage == 4:
                st.warning("💗 โหมดเอาตัวรอด: คำตอบผิดทำให้เสียพลังมากกว่าด่านทั่วไป")
            pick = st.radio("เลือกคำตอบที่ถูกต้อง", list(range(len(q["options"]))), index=None,
                            format_func=lambda i: f"{LET[i]}. {q['options'][i]}", key=f"opt_{b['uid']}_{idx}")
            if st.button("🪄 ร่ายเวท / ส่งคำตอบ", type="primary", use_container_width=True, key=f"cast_{b['uid']}_{idx}"):
                if pick is None:
                    st.warning("เลือกคำตอบก่อนนะ แล้วค่อยร่ายเวท ✨")
                else:
                    _answer(engine, b, q, pick)
                    st.rerun()
    else:
        last = b["last"]
        if last["ok"]:
            st.success(f"✨ โจมตีสำเร็จ! ลด HP มอนสเตอร์ {last['dmg']}  (+XP/เหรียญ)")
        else:
            right = f"{LET[q['idx']]}. {q['options'][q['idx']]}" if q["idx"] is not None else "-"
            st.warning(f"💦 เวทพลาด! {avatar['name']}เสียพลัง {last['dmg']}  ·  คำตอบที่ถูก: {right}")
        if q["explanation"]:
            st.info(f"📖 ทำความเข้าใจ: {q['explanation']}")
        if st.button("➡️ ไปข้อถัดไป", type="primary", use_container_width=True, key=f"next_{b['uid']}_{idx}"):
            b["idx"] += 1
            b["answered"] = False
            b["last"] = None
            st.rerun()

    if st.button("🏳️ ถอยกลับแผนที่ (ไม่นับผลด่านนี้)", key="quit_battle"):
        st.session_state.pop("battle", None)
        st.session_state.current_page = "map"
        st.rerun()
