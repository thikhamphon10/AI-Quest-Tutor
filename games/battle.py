import streamlit as st

from game_engine import answer_text, choice_buttons, finish, record, show_feedback

WRONG_DAMAGE = 20


def render(g):
    q = g["queue"][g["idx"] % len(g["queue"])]
    c1, c2 = st.columns(2)
    c1.progress(g["player_hp"] / 100, text=f"❤️ คุณ {g['player_hp']}/100")
    c2.progress(g["monster_hp"] / 100, text=f"👹 Monster {g['monster_hp']}/100")
    st.caption(f"🔥 Streak {g['streak']}  ·  ✨ XP {g['xp']}  ·  🏆 Score {g['score']}")
    st.subheader(q["question"])

    fb = g["feedback"]
    if fb:
        show_feedback(fb)
        if g["over"] == "victory":
            st.success("🏆 Victory! คุณชนะ Monster แล้ว")
        elif g["over"] == "gameover":
            st.error("💀 Game Over")
        if g["over"]:
            if st.button("📊 ดูผลลัพธ์", type="primary", use_container_width=True):
                finish(g)
        elif st.button("ข้อต่อไป ➡️", type="primary", use_container_width=True):
            g["idx"] += 1
            g["feedback"] = None
            st.rerun()
        return

    pick = choice_buttons(q, f"b{g['idx']}")
    if pick:
        ok = pick == q["correct_answer"]
        record(g, q, ok)
        if ok:
            g["monster_hp"] = max(0, g["monster_hp"] - q["damage"])
            g["score"] += q["xp"] * 10
        else:
            g["player_hp"] = max(0, g["player_hp"] - WRONG_DAMAGE)
        g["feedback"] = {"ok": ok, "answer": answer_text(q), "explanation": q["explanation"]}
        if g["monster_hp"] <= 0:
            g["over"] = "victory"
        elif g["player_hp"] <= 0:
            g["over"] = "gameover"
        st.rerun()
