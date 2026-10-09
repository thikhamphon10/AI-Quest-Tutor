import streamlit as st

ICON = {"weak": "🔴 Weak", "practice": "🟡 Needs Practice", "strong": "🟢 Strong"}


def render_topics(report):
    if not report:
        st.caption("ยังไม่มีข้อมูล เริ่มเล่นเกมก่อนนะ")
        return
    for r in report:
        st.progress(r["accuracy"],
                    text=f"{r['topic']} — {r['accuracy']:.0%} ({r['correct']}/{r['total']}) {ICON[r['level']]}")
