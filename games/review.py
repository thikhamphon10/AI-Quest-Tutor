"""โหมดทบทวนข้อที่ตอบผิด (จากสมุดข้อผิดพลาด)
ตอบถูกติดกันครบ MASTER_AFTER ครั้ง = ‘ทบทวนแล้ว’ (reviewed) ตอบผิดจะเริ่มนับใหม่
ให้รางวัลเล็กน้อยต่อข้อที่ถูก (XP/เหรียญ) เป็นกำลังใจ แต่ข้อที่ทบทวนแล้วจะไม่ให้รางวัลซ้ำ"""
import uuid

import streamlit as st

import visuals as V
from game_engine import MASTER_AFTER, GameEngine, qkey

LET = "ABCD"
REVIEW_XP = 5
REVIEW_COINS = 2
MAX_ITEMS = 10


def can_review(e: dict) -> bool:
    return bool(e.get("options")) and e.get("idx") is not None


def pick_items(errors: list, subject: str | None = None, limit: int = MAX_ITEMS) -> list:
    """เลือกข้อที่ยังไม่ทบทวนและมีตัวเลือกครบ (ผิดบ่อยสุดก่อน) คืนรายการ ‘ตัวคำถาม’ ไว้ใช้เป็นกุญแจ"""
    rows = [e for e in errors if not e.get("reviewed") and can_review(e) and (not subject or e.get("subject") == subject)]
    rows.sort(key=lambda e: -e.get("wrong_count", 1))
    return [e["question"] for e in rows[:limit]]


def start(items: list):
    st.session_state.review = {"uid": uuid.uuid4().hex[:8], "items": list(items), "idx": 0, "answered": False,
                               "last": None, "ok": 0, "wrong": 0, "xp": 0, "coins": 0, "mastered": 0, "levelups": 0}


def _leave(page: str):
    st.session_state.pop("review", None)
    st.session_state.current_page = page
    st.rerun()


def _entry(question: str):
    k = qkey(question)
    return next((e for e in st.session_state.user_data["error_notebook"] if qkey(e["question"]) == k), None)


def render():
    r = st.session_state.get("review")
    engine = GameEngine()
    if not r or not r["items"]:
        st.info("ยังไม่ได้เลือกข้อที่จะทบทวน ไปที่สมุดข้อผิดพลาดแล้วกดเริ่มทบทวนได้เลย")
        if st.button("📝 ไปสมุดข้อผิดพลาด", type="primary", key="rv_empty"):
            _leave("error_notebook")
        return
    n = len(r["items"])
    while r["idx"] < n and _entry(r["items"][r["idx"]]) is None:  # ข้ามข้อที่ถูกล้างออกจากสมุดไปแล้ว
        r["idx"] += 1

    if r["idx"] >= n:
        V.html('<div class="glass" style="text-align:center"><h3>🎉 ทบทวนครบแล้ว!</h3></div>')
        V.html(V.rewards_html(r["xp"], r["coins"], None, st.session_state.user_data["level"] if r["levelups"] else None))
        c1, c2, c3 = st.columns(3)
        c1.metric("✅ ถูก", r["ok"])
        c2.metric("❌ ผิด", r["wrong"])
        c3.metric("🌟 ทบทวนผ่าน", r["mastered"])
        if r["wrong"]:
            st.caption("ข้อที่ยังผิดจะอยู่ในสมุดต่อ ลองทบทวนอีกรอบวันหลังได้")
        a, b = st.columns(2)
        if a.button("📝 กลับสมุดข้อผิดพลาด", type="primary", use_container_width=True, key="rv_book"):
            _leave("error_notebook")
        if b.button("🗺️ กลับแผนที่", use_container_width=True, key="rv_map"):
            _leave("map")
        return

    e = _entry(r["items"][r["idx"]])
    opts, right_i = e["options"], e["idx"]
    st.progress(r["idx"] / n, text=f"ทบทวนข้อ {r['idx'] + 1} จาก {n}")
    V.html(f'<span class="pill">{V.esc(e["subject"])}</span><span class="pill">{V.esc(e["topic"])}</span>'
           f'<span class="pill h">เคยผิด {e["wrong_count"]} ครั้ง</span>')
    V.html(f'<div class="qcard"><div class="lb">REVIEW · ทบทวนข้อที่เคยพลาด</div><div class="q">{V.esc(e["question"])}</div></div>')
    key = f"{r['uid']}_{r['idx']}"

    if not r["answered"]:
        pick = st.radio("เลือกคำตอบ", list(range(len(opts))), index=None,
                        format_func=lambda i: f"{LET[i]}. {opts[i]}", key=f"rv_opt_{key}")
        if st.button("✅ ตรวจคำตอบ", type="primary", use_container_width=True, key=f"rv_check_{key}"):
            if pick is None:
                st.warning("เลือกคำตอบก่อนนะ ✨")
            else:
                was_done = e["reviewed"]
                ok = pick == right_i
                res = engine.review_answer(e["question"], ok)
                if ok and not was_done:
                    r["xp"] += REVIEW_XP
                    r["coins"] += REVIEW_COINS
                    r["levelups"] += engine.add_reward(REVIEW_XP, REVIEW_COINS)
                    engine.save()
                r["ok" if ok else "wrong"] += 1
                r["mastered"] += bool(res["mastered"] and not was_done)
                r["last"] = {"ok": ok, "res": res}
                r["answered"] = True
                st.rerun()
        return

    last = r["last"]
    if last["ok"]:
        if last["res"]["mastered"]:
            st.success(f"🌟 ถูกต้อง! ตอบถูกติดกัน {MASTER_AFTER} ครั้งแล้ว ข้อนี้ ‘ทบทวนผ่าน’ (+{REVIEW_XP} XP, +{REVIEW_COINS} เหรียญ)")
        else:
            st.success(f"✅ ถูกต้อง! ({last['res']['right']}/{MASTER_AFTER} ครั้งติด) ตอบถูกอีกครั้งในรอบหน้าเพื่อให้ข้อนี้ผ่าน")
    else:
        st.warning(f"💦 ยังไม่ใช่นะ คำตอบที่ถูกคือ {LET[right_i]}. {opts[right_i]}  ไม่เป็นไร อ่านคำอธิบายแล้วลองใหม่ได้")
    st.info(f"📖 {e['explanation'] or 'ข้อนี้ยังไม่มีคำอธิบาย'}")
    label = "🏁 ดูสรุป" if r["idx"] + 1 >= n else "➡️ ข้อถัดไป"
    if st.button(label, type="primary", use_container_width=True, key=f"rv_next_{key}"):
        r["idx"] += 1
        r["answered"] = False
        r["last"] = None
        st.rerun()
    if st.button("⬅️ หยุดทบทวน", key=f"rv_stop_{key}"):
        _leave("error_notebook")
