"""ทดสอบฟีเจอร์ชุดล่าสุด: คลังข้อสอบ(วิชา/บท/ความยาก/จำนวน) · ข้อสอบ AI ที่บันทึกแล้ว · Error 429 · ชื่อ/ตัวละคร/อาวุธ
สมุดข้อผิดพลาด+ทบทวน · สรุปจุดอ่อนรายวิชา · เซฟ · ความลับ   รัน: pytest -q (ใช้ Streamlit/Gemini จำลอง ไม่ต้องมีเน็ตหรือ API Key)"""
import glob
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from driver import ROOT, App  # noqa: E402
from sample_questions import QS  # noqa: E402

LONG = "การสังเคราะห์ด้วยแสงคือกระบวนการที่พืชสีเขียวใช้แสงเปลี่ยนน้ำกับคาร์บอนไดออกไซด์เป็นน้ำตาล " * 2
BTN_GEN = "🪄 ร่ายคาถาสร้างข้อสอบ"
BTN_USE_BANK = "🎮 เลือกชุดข้อสอบนี้"


@pytest.fixture()
def app():
    a = App()
    a.run()
    a.st.session_state.active_questions = QS
    a.st.session_state.quiz_title = "t"
    return a


def _fake_batch(n=5):
    def f(text, difficulty, size, emphasis="", *a, **k):
        return [{"question": f"ข้อ AI #{i} {difficulty}", "options": ["ก", "ข", "ค", "ง"], "answer": "ข",
                 "explanation": "เพราะ ข", "topic": "หัวข้อ AI"} for i in range(size)][:n]
    return f


def _play(app, correct: bool):
    """เล่นด่าน 1 จนจบ (ด่านนี้ใช้ radio + ปุ่มร่ายเวท)"""
    S = app.st.session_state
    while not S.battle["done"]:
        b = S.battle
        q = b["qs"][b["idx"]]
        pick = q["idx"] if correct else (q["idx"] + 1) % len(q["options"])
        app.run(press=[f"cast_{b['uid']}_{b['idx']}"], radio_cb=lambda k, o, p=pick: p)
        if not S.battle["done"]:
            app.run(press=[f"next_{b['uid']}_{b['idx']}"])


def _gen(app, S, **values):
    S.current_page = "ai_generator"
    base = {"กรอกเนื้อหาที่ต้องการให้ออกข้อสอบ:": LONG, "จำนวนข้อสอบที่ต้องการ:": 5}
    base.update(values)
    return app.run(press=[BTN_GEN], values=base)


# ---------------------------------------------------------------- 1) คลังข้อสอบ: วิชา/บท/ความยาก/จำนวน
def test_bank_page_filters_subject_topic_count(app):
    import json
    S = app.st.session_state
    bank = json.load(open(os.path.join(ROOT, "question_bank.json"), encoding="utf-8"))
    topic = next(q["subtopic"] for q in bank if q["subject"] == "ฟิสิกส์")
    want = sum(1 for q in bank if q["subject"] == "ฟิสิกส์" and q["subtopic"] == topic)
    S.current_page = "question_bank"
    app.run(values={"เลือกวิชา": "ฟิสิกส์", "เลือกบท/หัวข้อ": topic, "🎯 จำนวนข้อในการเล่นครั้งนี้": 5}, press=[BTN_USE_BANK])
    assert S.current_page == "map" and len(S.active_questions) == want
    assert all(q["subject"] == "ฟิสิกส์" and q["subtopic"] == topic for q in S.active_questions)
    assert S.selected_question_count == 5
    app.run(press=["btn_stage_1", "dlg_go_1"])  # เล่นด่านด้วยข้อสอบจากคลังได้จริง
    assert S.current_page == "battle" and len(S.battle["qs"]) == min(5, want)


def test_bank_difficulty_filter_and_ai_questions_merge(app, monkeypatch):
    import ai_engine
    monkeypatch.setattr(ai_engine, "generate_questions_batch", _fake_batch())
    monkeypatch.setattr(ai_engine.time, "sleep", lambda s: None)
    S = app.st.session_state
    _gen(app, S, **{"วิชา": "ฟิสิกส์", "บทเรียน (ไม่บังคับ):": "ทดสอบบท", "ระดับความยาก:": "ยาก"})
    assert S.gen_done["n"] == 5 and S.active_questions[0]["subtopic"] == "ทดสอบบท" and S.active_questions[0]["difficulty"] == "ยาก"
    # ข้อที่ AI สร้างถูกบันทึกและโผล่ในคลังตามวิชา/บท/ความยาก
    S.current_page = "question_bank"
    app.run(values={"เลือกวิชา": "ฟิสิกส์", "เลือกบท/หัวข้อ": "ทดสอบบท", "ระดับความยาก": "ยาก"}, press=[BTN_USE_BANK])
    assert S.current_page == "map" and len(S.active_questions) == 5
    assert all(q["difficulty"] == "ยาก" and q["source"] == "AI สร้าง" for q in S.active_questions)
    # ระดับที่ไม่มีข้อ => ปุ่มใช้งานไม่ได้ (ไม่ crash)
    S.current_page = "question_bank"
    app.run(values={"เลือกวิชา": "ฟิสิกส์", "เลือกบท/หัวข้อ": "ทดสอบบท", "ระดับความยาก": "ง่าย"}, press=[BTN_USE_BANK])
    assert S.current_page == "question_bank"


def test_generated_questions_saved_without_duplicates_in_bank(app, monkeypatch):
    import ai_engine
    monkeypatch.setattr(ai_engine, "generate_questions_batch", _fake_batch())
    monkeypatch.setattr(ai_engine.time, "sleep", lambda s: None)
    S = app.st.session_state
    _gen(app, S, **{"วิชา": "ชีววิทยา", "บทเรียน (ไม่บังคับ):": "บทซ้ำ"})
    _gen(app, S, **{"วิชา": "ชีววิทยา", "บทเรียน (ไม่บังคับ):": "บทซ้ำ"})  # สร้างซ้ำด้วยชื่อชุด/ข้อเดิม
    assert len(glob.glob("saved_quizzes/*.json")) == 1  # ไม่งอกไฟล์ซ้ำ
    S.current_page = "question_bank"
    app.run(values={"เลือกวิชา": "ชีววิทยา", "เลือกบท/หัวข้อ": "บทซ้ำ", "🎯 จำนวนข้อในการเล่นครั้งนี้": 5}, press=[BTN_USE_BANK])
    texts = [q["question"] for q in S.active_questions]
    assert len(texts) == 5 and len(set(texts)) == 5  # ในคลังมี 5 ข้อไม่ซ้ำ


# ---------------------------------------------------------------- 2) Error 429
def test_quota_429_warns_and_returns_to_bank(app, monkeypatch):
    import ai_engine
    monkeypatch.setattr(ai_engine, "get_client", lambda: object())
    monkeypatch.setattr(ai_engine.time, "sleep", lambda s: None)

    def boom(*a, **k):
        raise Exception("QUOTA_EXHAUSTED: โควตาการใช้งาน Gemini API หมดแล้ว")
    monkeypatch.setattr(ai_engine, "_call_gemini_with_retry", boom)
    S = app.st.session_state
    st = _gen(app, S)
    assert ai_engine.last_error_kind == "quota"
    assert any(k == "warning" and "429" in m for k, m in st.log)
    assert "quota_bank" in st.buttons  # ปุ่มกลับไปทำข้อสอบในคลัง
    app.run(press=["quota_bank"])
    assert S.current_page == "question_bank"
    app.run(values={"เลือกวิชา": "ภาษาอังกฤษ", "🎯 จำนวนข้อในการเล่นครั้งนี้": 5}, press=[BTN_USE_BANK])
    assert S.current_page == "map" and S.active_questions  # ข้อสอบในคลังยังเล่นต่อได้หลังโดน 429
    app.run(press=["btn_stage_1", "dlg_go_1"])
    assert S.current_page == "battle"


def test_quota_partial_results_kept_and_warned(app, monkeypatch):
    import ai_engine
    monkeypatch.setattr(ai_engine, "get_client", lambda: object())
    monkeypatch.setattr(ai_engine.time, "sleep", lambda s: None)
    calls = {"n": 0}
    good = _fake_batch()

    def flaky(text, difficulty, size, emphasis="", *a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            return good(text, difficulty, size, emphasis)
        raise Exception("QUOTA_EXHAUSTED: x")
    monkeypatch.setattr(ai_engine, "generate_questions_batch", flaky)
    S = app.st.session_state
    st = _gen(app, S, **{"จำนวนข้อสอบที่ต้องการ:": 10})
    assert S.gen_done["n"] == 5 and S.gen_done["asked"] == 10 and len(S.active_questions) == 5
    assert "quota_bank" in st.buttons


def test_api_key_never_shown_or_committed(app, monkeypatch):
    import ai_engine
    fake_key = "AI" + "zaSyTESTKEY1234567890abcdefghijklmnop"  # ต่อสตริงเพื่อไม่ให้ไฟล์ทดสอบนี้ดูเหมือนมี key จริง
    monkeypatch.setenv("GEMINI_API_KEY", fake_key)
    assert "zaSyTESTKEY" not in ai_engine.scrub(f"error calling https://x?key={fake_key} failed")
    for f in glob.glob(os.path.join(ROOT, "**", "*.py"), recursive=True) + glob.glob(os.path.join(ROOT, "*.md")):
        assert not re.search(r"AIza[0-9A-Za-z_\-]{20,}", open(f, encoding="utf-8").read()), f
    gi = open(os.path.join(ROOT, ".gitignore"), encoding="utf-8").read()
    assert ".env" in gi and "secrets.toml" in gi and "saves/" in gi
    assert open(os.path.join(ROOT, ".env.example"), encoding="utf-8").read().strip() == "GEMINI_API_KEY="


# ---------------------------------------------------------------- 3) ชื่อ / ตัวละคร / อาวุธ
def test_name_weapon_and_damage(app):
    import game_engine as ge
    S = app.st.session_state
    S.current_page = "character"
    app.run(values={"ชื่อนักผจญภัย": "ดาวใส"}, press=["char_name_save"])
    assert S.user_data["player_name"] == "ดาวใส"
    app.run(press=["ch_w_buy_berry_bow"])  # เหรียญ 50 ไม่พอ -> ปุ่มกดไม่ได้
    assert "berry_bow" not in S.user_data["unlocked_weapons"]
    S.user_data["coins"] = 1000

    def first_hit(weapon):
        S.user_data["selected_weapon"] = weapon
        S.pop("battle", None)
        S.current_page = "map"
        S.used_question_ids = []
        app.run(press=["btn_stage_1", "dlg_go_1"])
        b = S.battle
        q = b["qs"][0]
        app.run(press=[f"cast_{b['uid']}_0"], radio_cb=lambda k, o, p=q["idx"]: p)
        return b["monster_max"] - S.battle["monster_hp"]
    S.user_data["unlocked_weapons"] = list(ge.WEAPONS)
    assert first_hit("rainbow_blade") > first_hit("star_wand")
    S.current_page = "character"
    app.run(press=["ch_w_use_moon_staff"])
    assert S.user_data["selected_weapon"] == "moon_staff"


def test_name_html_escaped(app):
    S = app.st.session_state
    S.user_data["player_name"] = "<i>zz</i>"
    S.current_page = "map"
    app.run()
    html = app.html()
    assert "<i>zz</i>" not in html and "&lt;i&gt;zz&lt;/i&gt;" in html


# ---------------------------------------------------------------- 4) สมุดข้อผิดพลาด + ทบทวน
def test_mistakes_notebook_and_review_mastery(app):
    S = app.st.session_state
    app.run(press=["btn_stage_1", "dlg_go_1"])
    _play(app, False)
    nb = S.user_data["error_notebook"]
    assert len(nb) == S.battle["wrong"] > 0
    e0 = nb[-1]
    assert e0["options"] and e0["idx"] is not None and e0["explanation"] and e0["correct_answer"] and not e0["reviewed"]
    S.pop("battle", None)
    S.current_page = "error_notebook"
    st = app.run()
    assert "nb_review" in st.buttons and "ดูคำอธิบาย" in app.html() and "เฉลย" in app.html()
    n, coins0 = len(nb), S.user_data["coins"]
    for _ in range(2):  # ทบทวน 2 รอบ ตอบถูกติดกัน => ทบทวนผ่าน
        S.current_page = "error_notebook"
        app.run(press=["nb_review"])
        assert S.current_page == "review"
        R = S.review
        while R["idx"] < len(R["items"]):
            idx = R["idx"]
            e = next(x for x in S.user_data["error_notebook"] if x["question"] == R["items"][idx])
            app.run(press=[f"rv_check_{R['uid']}_{idx}"], radio_cb=lambda k, o, p=e["idx"]: p)
            app.run(press=[f"rv_next_{R['uid']}_{idx}"])
        app.run()
    assert all(e["reviewed"] for e in S.user_data["error_notebook"]) and len(S.user_data["error_notebook"]) == n
    assert S.user_data["coins"] > coins0
    import games.review as rv
    assert rv.pick_items(S.user_data["error_notebook"]) == []


def test_repeat_mistake_merges_and_wrong_review_resets(app):
    import game_engine as ge
    S = app.st.session_state
    eng = ge.GameEngine()
    entry = {"question": "ทดสอบ?", "subject": "ฟิสิกส์", "topic": "t", "wrong_answer": "ข", "correct_answer": "ก", "explanation": "e",
             "options": ["ก", "ข"], "idx": 0}
    eng.record_error(entry)
    assert eng.review_answer("ทดสอบ?", True) == {"mastered": False, "right": 1}
    assert eng.review_answer("ทดสอบ?", False)["right"] == 0
    assert eng.review_answer("ทดสอบ?", True)["mastered"] is False
    assert eng.review_answer("ทดสอบ?", True)["mastered"] is True
    eng.record_error(entry)  # พลาดซ้ำ -> รวมเป็นรายการเดียว นับครั้งที่ผิดเพิ่ม และกลับมาเป็นข้อค้าง
    nb = S.user_data["error_notebook"]
    assert len(nb) == 1 and nb[0]["wrong_count"] >= 3 and nb[0]["reviewed"] is False and nb[0]["review_streak"] == 0


def test_old_notebook_entries_without_options_still_load(app):
    import game_engine as ge
    u = ge.sanitize_user({"error_notebook": [{"question": "ข้อเก่า", "wrong_answer": "ก", "correct_answer": "ข", "explanation": "x"},
                                             {"question": "", "bad": 1}, "junk"]})
    assert len(u["error_notebook"]) == 1 and u["error_notebook"][0]["options"] == []
    S = app.st.session_state
    S.user_data = u
    S.current_page = "error_notebook"
    st = app.run()
    assert not [l for l in st.log if l[0] == "error"]


# ---------------------------------------------------------------- 5) สรุปคะแนน/จุดอ่อนรายวิชา
def test_summary_by_subject_and_weak_training(app):
    S = app.st.session_state
    S.active_questions = [dict(q, subject="คณิตศาสตร์") for q in QS]
    app.run(press=["btn_stage_1", "dlg_go_1"])
    _play(app, False)
    ss = S.user_data["subject_stats"]
    assert ss["คณิตศาสตร์"]["wrong"] == S.battle["wrong"] and ss["คณิตศาสตร์"]["topics"]
    S.pop("battle", None)
    S.current_page = "summary"
    st = app.run()
    assert not [l for l in st.log if l[0] == "error"]
    assert any(k == "warning" and "คณิตศาสตร์" in m for k, m in st.log)
    assert "sum_train_0" in st.buttons
    app.run(press=["sum_train_0"])
    assert S.current_page == "map" and S.quiz_title.startswith("ฝึกจุดอ่อน") and S.active_questions


def test_all_pages_render(app):
    S = app.st.session_state
    for page in ("map", "ai_generator", "saved_quizzes", "question_bank", "error_notebook", "summary", "character", "review"):
        S.current_page = page
        st = app.run()
        assert not [l for l in st.log if l[0] == "error"], page
    S.current_page = "nonsense"
    app.run()
    assert S.current_page == "map"


# ---------------------------------------------------------------- 6) เซฟ / ความปลอดภัยของข้อมูล / ไฟล์ภาพ
def test_new_progress_survives_refresh(app):
    import game_engine as ge
    S = app.st.session_state
    S.user_data["player_name"] = "ดาวใส"
    app.run(press=["btn_stage_1", "dlg_go_1"])
    _play(app, False)
    ge.GameEngine().save()
    pid = S.player_id
    a2 = App(workdir=app.work)
    a2.st.query_params["p"] = pid
    a2.run()
    u = a2.st.session_state.user_data
    assert u["player_name"] == "ดาวใส" and u["error_notebook"] and u["subject_stats"]
    assert a2.st.session_state.used_question_ids  # ประวัติข้อสอบที่ใช้แล้วก็ถูกกู้คืน


def test_asset_folder_case_insensitive(tmp_path, app):
    import visuals as V
    (tmp_path / "Monster").mkdir()
    (tmp_path / "Monster" / "slime.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    old = V.ASSETS
    V.ASSETS = str(tmp_path)
    try:
        assert V._find_asset("monsters/slime.svg").endswith(os.path.join("Monster", "slime.svg"))
        assert V._find_asset("Monster/slime.svg").endswith(os.path.join("Monster", "slime.svg"))
    finally:
        V.ASSETS = old
    # โฟลเดอร์จริงของโปรเจกต์: ภาพมอนสเตอร์ต้องโหลดได้ (ไม่ใช่ภาพว่างสำรอง)
    blank = V.img_uri("does/not/exist.svg")
    assert V.monster_img("slime") != blank and V.monster_img("king", "ko") != blank
