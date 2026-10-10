"""รัน: pip install pytest && pytest -q   (ใช้ Streamlit/Gemini จำลอง จึงไม่ต้องมีเน็ตหรือ API Key)"""
import glob
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from driver import ROOT, App  # noqa: E402
from sample_questions import QS  # noqa: E402


@pytest.fixture()
def app():
    a = App()
    a.run()
    a.st.session_state.active_questions = QS
    a.st.session_state.quiz_title = "t"
    return a


def test_no_external_image_links():
    """ห้ามมีลิงก์รูปภายนอก (สาเหตุรูปไม่แสดงเดิม)"""
    for f in glob.glob(os.path.join(ROOT, "*.py")) + glob.glob(os.path.join(ROOT, "games", "*.py")):
        txt = open(f, encoding="utf-8").read()
        assert "icons8" not in txt, f
        assert not re.search(r"st\.image\(\s*[\"']https?://", txt), f


def test_all_assets_exist_and_used_images_resolve():
    import xml.etree.ElementTree as ET
    sys.path.insert(0, ROOT)
    import game_engine as ge
    import visuals as V
    for f in glob.glob(os.path.join(ROOT, "assets", "**", "*.svg"), recursive=True):
        ET.parse(f)
    for a in ge.AVATARS:
        for s in ("normal", "cheer", "tired"):
            assert os.path.isfile(os.path.join(ROOT, "assets", "heroes", f"{a}{'' if s == 'normal' else '_' + s}.svg"))
    for m in ge.MONSTERS.values():
        for s in ("normal", "hurt", "ko"):
            assert os.path.isfile(os.path.join(ROOT, "assets", "monsters", f"{m['img']}{'' if s == 'normal' else '_' + s}.svg"))
    assert os.path.isfile(os.path.join(ROOT, "assets", "map.svg"))
    assert V.img_uri("map.svg").startswith("data:image/svg+xml;base64,")


def test_map_page_renders_all_pages(app):
    for page in ("map", "ai_generator", "saved_quizzes"):
        app.st.session_state.current_page = page
        st = app.run()
        assert not [l for l in st.log if l[0] == "error"], page


def test_battle_win_rewards_and_unlock(app):
    S = app.st.session_state
    app.run(press=["btn_stage_1", "dlg_go_1"])
    assert S.current_page == "battle"
    while not S.battle["done"]:
        b = S.battle
        q = b["qs"][b["idx"]]
        app.run(press=[f"cast_{b['uid']}_{b['idx']}"], radio_cb=lambda k, o, p=q["idx"]: p)
        if not S.battle["done"]:
            app.run(press=[f"next_{b['uid']}_{b['idx']}"])
    assert S.battle["done"] == "win" and S.battle["monster_hp"] == 0
    u = S.user_data
    assert 2 in u["unlocked_stages"] and u["stage_stars"]["1"] == 3 and u["coins"] > 50 and u["xp"] + (u["level"] - 1) * 100 > 0


def test_battle_state_resets_between_stages(app):
    S = app.st.session_state
    app.run(press=["btn_stage_1", "dlg_go_1"])
    S.battle["monster_hp"] = 5
    app.run(press=["quit_battle"])
    S.user_data["unlocked_stages"] = [1, 2]
    app.run(press=["btn_stage_2", "dlg_go_2"])
    assert S.battle["monster_hp"] == 120 and S.battle["stage"] == 2  # ไม่ค้าง HP จากด่านก่อน


def test_wrong_answers_lose_without_stage_progress(app):
    S = app.st.session_state
    app.run(press=["btn_stage_1", "dlg_go_1"])
    while not S.battle["done"]:
        b = S.battle
        q = b["qs"][b["idx"]]
        app.run(press=[f"cast_{b['uid']}_{b['idx']}"], radio_cb=lambda k, o, p=(q["idx"] + 1) % 4: p)
        if not S.battle["done"]:
            app.run(press=[f"next_{b['uid']}_{b['idx']}"])
    assert S.battle["done"] == "lose" and S.user_data["stage_stars"] == {} and S.user_data["unlocked_stages"] == [1]


def test_progress_survives_refresh(app):
    S = app.st.session_state
    S.user_data["coins"] = 321
    app.run(press=["btn_stage_1"])  # เหตุการณ์ใด ๆ ก็ตามที่เซฟ
    app.st.session_state.user_data["coins"] = 321
    from game_engine import GameEngine
    GameEngine().save()
    a2 = App(workdir=app.work)
    a2.st.query_params["p"] = S.player_id
    a2.run()
    assert a2.st.session_state.user_data["coins"] == 321


def test_sanitize_and_storage_safety():
    sys.path.insert(0, ROOT)
    import game_engine as ge
    import storage
    u = ge.sanitize_user({"coins": "abc", "stage_stars": {"1": 99, "x": 1, "99": 3}, "unlocked_avatars": ["fox", "evil"],
                          "selected_avatar": "evil", "level": -5})
    assert u["coins"] == 50 and u["stage_stars"] == {"1": 3} and u["unlocked_avatars"] == ["bunny", "fox"] and u["selected_avatar"] == "bunny" and u["level"] == 1
    assert ge.sanitize_user("junk")["coins"] == 50
    assert not storage.valid_id("../../etc/passwd") and storage.valid_id(storage.new_id())
    with pytest.raises(ValueError):
        storage._path("../x")


def test_norm_q_formats():
    sys.path.insert(0, ROOT)
    App()
    from games.battle import norm_q
    assert norm_q({"question": "q", "options": ["a", "b", "c", "d"], "answer": "c"})["idx"] == 2
    assert norm_q({"question": "q", "choices": ["a", "b", "c", "d"], "correct_answer": "D"})["idx"] == 3
    assert norm_q({"question": "q", "options": ["ก", "ข"], "answer": "ไม่มี"})["idx"] is None


def test_level_up_and_hero_unlock(app):
    import game_engine as ge
    d = ge.default_user()
    assert ge.apply_xp(d, 260) == 2 and d["level"] == 3 and d["max_xp"] == 225
    S = app.st.session_state
    S.user_data["coins"] = 10
    ok, msg = ge.GameEngine().unlock_avatar("cat")
    assert not ok and "ไม่พอ" in msg


def test_ai_generator_loop_guard(monkeypatch):
    App()
    import ai_engine
    monkeypatch.setattr(ai_engine, "generate_questions_batch", lambda *a, **k: [{"question": "same"}])
    monkeypatch.setattr(ai_engine.time, "sleep", lambda s: None)
    out = ai_engine.generate_questions_from_text("x" * 100, "ง่าย", 10)
    assert len(out) == 1  # เดิมจะวนไม่จบ
