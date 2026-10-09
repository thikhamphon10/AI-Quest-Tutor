import time

import streamlit as st

from game_engine import choice_buttons, finish, record

TIME_LIMIT = 60


@st.fragment(run_every=1)
def timer():
    g = st.session_state.game
    if not g:
        return
    left = max(0, TIME_LIMIT - int(time.time() - g["start"]))
    st.progress(left / TIME_LIMIT, text=f"⏱️ เหลือ {left} วินาที")
    if left == 0:
        g["over"] = "timeup"
        finish(g)


def render(g):
    timer()
    if time.time() - g["start"] >= TIME_LIMIT:
        g["over"] = "timeup"
        finish(g)
    q = g["queue"][g["idx"] % len(g["queue"])]
    c1, c2, c3 = st.columns(3)
    c1.metric("🏆 Score", g["score"])
    c2.metric("🔥 Streak", g["streak"])
    c3.metric("✅ ถูก", g["correct"])
    st.subheader(q["question"])
    pick = choice_buttons(q, f"s{g['idx']}")
    if pick:
        ok = pick == q["correct_answer"]
        record(g, q, ok)
        if ok:
            g["score"] += 10 + 2 * min(g["streak"], 5)  # Streak bonus
        g["idx"] += 1
        st.rerun()
