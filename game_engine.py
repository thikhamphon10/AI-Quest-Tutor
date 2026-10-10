import streamlit as st

import storage

# ---------------------------------------------------------------- ข้อมูลตัวละคร (ภาพอยู่ใน assets/ ไม่ใช้ลิงก์ภายนอก)
# perk: xp_mult / coin_mult / wrong_mult (พลังที่เสียเมื่อตอบผิด) / dmg_mult (พลังโจมตี)
AVATARS = {
    "bunny": {"name": "มิลกี้", "class": "กระต่ายดาวนำโชค", "color": "#ffd34d", "skill": "ประกายดาว",
              "desc": "กระต่ายขี้อายที่เป่าไม้กายสิทธิ์ดาวได้ เวทมนตร์ทำให้ทุกคนอารมณ์ดี",
              "perk": "ดาวนำโชค: ได้ XP เพิ่ม 10%", "mod": {"xp_mult": 1.10}, "cost": 0},
    "cat": {"name": "ลูน่า", "class": "แมวเวทจันทรา", "color": "#b79cff", "skill": "แสงจันทร์เหมียว",
            "desc": "แมวเจ้าเล่ห์ที่ชอบนอนบนดวงจันทร์ ปล่อยลำแสงจันทร์ที่สวยและหอมกลิ่นนม",
            "perk": "เหมียวรวย: ได้เหรียญเพิ่ม 20%", "mod": {"coin_mult": 1.20}, "cost": 100},
    "bear": {"name": "ฮันนี่", "class": "หมีใจดีขนปุย", "color": "#ff8fb5", "skill": "คลื่นหัวใจน้ำผึ้ง",
             "desc": "หมีตัวกลมที่กอดเก่งที่สุดในแดนเวทมนตร์ ขนปุยช่วยซับแรงกระแทก",
             "perk": "ขนปุยกันกระแทก: ตอบผิดเสียพลังน้อยลง 25%", "mod": {"wrong_mult": 0.75}, "cost": 150},
    "fox": {"name": "เอมเบอร์", "class": "จิ้งจอกเปลวไฟ", "color": "#ff9a4d", "skill": "ไฟจิ้งจอก",
            "desc": "จิ้งจอกคล่องแคล่วที่มีหางฟูนุ่ม ลูกไฟของเขาอบอุ่นและร้อนแรงกว่าที่คิด",
            "perk": "ไฟจิ้งจอก: พลังโจมตีเพิ่ม 20%", "mod": {"dmg_mult": 1.20}, "cost": 200},
}
AVATAR_ORDER = ["bunny", "cat", "bear", "fox"]
DEFAULT_AVATAR = "bunny"

WEAPONS = {
    "star_wand": {"name": "ไม้กายสิทธิ์ดาว", "icon": "🪄", "damage": 1.00, "cost": 0, "desc": "อาวุธเริ่มต้นสมดุล"},
    "berry_bow": {"name": "ธนูเบอร์รี", "icon": "🏹", "damage": 1.10, "cost": 100, "desc": "เพิ่มพลังโจมตี 10%"},
    "moon_staff": {"name": "คทาจันทรา", "icon": "🔮", "damage": 1.20, "cost": 220, "desc": "เพิ่มพลังโจมตี 20%"},
    "rainbow_blade": {"name": "ดาบสายรุ้ง", "icon": "⚔️", "damage": 1.35, "cost": 400, "desc": "เพิ่มพลังโจมตี 35%"},
}
# รหัสตัวละครของเวอร์ชันก่อนหน้า -> ตัวละครใหม่ (เซฟเก่ายังใช้ได้)
LEGACY_AVATAR = {"shadow_fox": "fox", "arcane_mage": "cat", "cyber_knight": "bear", "storm_dragon": "bunny"}

MONSTERS = {
    1: {"name": "เจลลี่สไลม์", "title": "สไลม์คริสตัลสีมิ้นต์", "img": "slime", "hp": 100, "max_hp": 100,
        "color": "#34D399", "place": "ทุ่งเจลลี่", "reward": "เริ่มต้นการผจญภัย",
        "desc": "สไลม์ตัวจิ๋วที่เด้งดึ๋งไปทั่วทุ่ง ชอบแกล้งนักเดินทางให้เดินช้าลง"},
    2: {"name": "ชรูมมี่", "title": "เห็ดขี้อายแห่งป่านุ่มนิ่ม", "img": "mushroom", "hp": 120, "max_hp": 120,
        "color": "#F472B6", "place": "ป่าเห็ดนุ่มนิ่ม", "reward": "ปลดล็อกหุบเขาเมฆ",
        "desc": "เห็ดขี้อายที่ซ่อนอยู่ในป่า ใครเดินผ่านจะถูกโปรยละอองฝันหวาน"},
    3: {"name": "บู๊บู้", "title": "ผีเมฆขี้เซาะ", "img": "ghost", "hp": 150, "max_hp": 150,
        "color": "#8B5CF6", "place": "หุบเขาเมฆฝัน", "reward": "ปลดล็อกเมืองคัพเค้ก",
        "desc": "ผีเมฆที่ชอบหลอกให้ตกใจแล้วหัวเราะคิกคัก"},
    4: {"name": "คัพเค้กจอมซน", "title": "คัพเค้กที่เดินได้", "img": "cupcake", "hp": 180, "max_hp": 180,
        "color": "#FB7185", "place": "เมืองคัพเค้กหวาน", "reward": "ปลดล็อกถ้ำมังกร",
        "desc": "คัพเค้กที่ตื่นขึ้นมาเดินได้ ตั้งใจจะแจกความหวานให้ทั้งเมือง"},
    5: {"name": "ดราโก้จิ๋ว", "title": "มังกรพ่นฟองสบู่", "img": "dragon", "hp": 220, "max_hp": 220,
        "color": "#F97316", "place": "ถ้ำมังกรจิ๋ว", "reward": "พิชิตปราสาทราชาโมจิ",
        "desc": "มังกรตัวเล็กพ่นฟองสบู่แทนไฟ แต่ปีกน้อย ๆ แข็งแรงเกินคาด"},
    6: {"name": "ราชาโมจิ", "title": "ราชาแห่งแดนขนมนุ่มนิ่ม", "img": "king", "hp": 300, "max_hp": 300,
        "color": "#F59E0B", "place": "ปราสาทราชาโมจิ", "reward": "ผู้พิทักษ์แดนเวทมนตร์",
        "desc": "ราชาผู้ยิ่งใหญ่ เขาจะง่วงนอนก็ต่อเมื่อคุณพิสูจน์ความรู้ให้เห็น", "req_stars": 8},
}
LAST_STAGE = max(MONSTERS)
MAX_STARS = 3 * LAST_STAGE

# ค่าที่บันทึกลงไฟล์เซฟ
SAVE_VERSION = 2


def default_user() -> dict:
    return {"player_name": "นักผจญภัย", "level": 1, "xp": 0, "max_xp": 100, "coins": 50, "stars": 0, "unlocked_stages": [1],
            "selected_weapon": "star_wand", "unlocked_weapons": ["star_wand"], "error_notebook": [],
            "selected_avatar": DEFAULT_AVATAR, "inventory": [], "unlocked_avatars": [DEFAULT_AVATAR],
            "stage_stars": {}, "best_streak": 0, "total_correct": 0, "total_answered": 0, "topic_stats": {}}


def _i(v, lo=0, hi=10**9, d=0):
    try:
        return max(lo, min(hi, int(v)))
    except (TypeError, ValueError):
        return d


def sanitize_user(raw) -> dict:
    """ตรวจ/ล้างข้อมูลเซฟ (จากไฟล์หรือที่ผู้ใช้อัปโหลด) ให้ปลอดภัยและเข้ากับเซฟเวอร์ชันเก่า"""
    u = default_user()
    if not isinstance(raw, dict):
        return u
    u["player_name"] = str(raw.get("player_name", "นักผจญภัย")).strip()[:24] or "นักผจญภัย"
    owned_weapons = raw.get("unlocked_weapons", ["star_wand"])
    if not isinstance(owned_weapons, list):
        owned_weapons = ["star_wand"]
    u["unlocked_weapons"] = list(dict.fromkeys(w for w in owned_weapons if w in WEAPONS))
    if "star_wand" not in u["unlocked_weapons"]:
        u["unlocked_weapons"].insert(0, "star_wand")
    selected_weapon = raw.get("selected_weapon", "star_wand")
    u["selected_weapon"] = selected_weapon if selected_weapon in u["unlocked_weapons"] else "star_wand"
    notebook = raw.get("error_notebook", [])
    u["error_notebook"] = [x for x in notebook if isinstance(x, dict) and str(x.get("question", "")).strip()][-200:] if isinstance(notebook, list) else []
    u["level"] = _i(raw.get("level"), 1, 999, 1)
    u["max_xp"] = _i(raw.get("max_xp"), 100, 10**9, 100)
    u["xp"] = _i(raw.get("xp"), 0, u["max_xp"] - 1, 0)
    u["coins"] = _i(raw.get("coins"), 0, 10**9, 50)
    for k in ("best_streak", "total_correct", "total_answered"):
        u[k] = _i(raw.get(k), 0, 10**7)
    stages = raw.get("unlocked_stages")
    ok = sorted({s for s in stages if isinstance(s, int) and s in MONSTERS}) if isinstance(stages, list) else []
    u["unlocked_stages"] = ok or [1]
    if 1 not in u["unlocked_stages"]:
        u["unlocked_stages"].insert(0, 1)
    ss = {}
    if isinstance(raw.get("stage_stars"), dict):
        for k, v in raw["stage_stars"].items():
            if str(k).isdigit() and int(k) in MONSTERS:
                ss[str(int(k))] = _i(v, 0, 3)
    u["stage_stars"] = ss
    u["stars"] = sum(ss.values()) if ss else _i(raw.get("stars"), 0, MAX_STARS)
    owned = []
    for a in (raw.get("unlocked_avatars") or []) if isinstance(raw.get("unlocked_avatars"), list) else []:
        a = LEGACY_AVATAR.get(a, a)
        if a in AVATARS and a not in owned:
            owned.append(a)
    if DEFAULT_AVATAR not in owned:
        owned.insert(0, DEFAULT_AVATAR)
    u["unlocked_avatars"] = owned
    sel = LEGACY_AVATAR.get(raw.get("selected_avatar"), raw.get("selected_avatar"))
    u["selected_avatar"] = sel if sel in owned else DEFAULT_AVATAR
    ts = {}
    if isinstance(raw.get("topic_stats"), dict):
        for t, v in raw["topic_stats"].items():
            if isinstance(v, dict):
                ts[str(t)[:60]] = {"correct": _i(v.get("correct"), hi=10**6), "wrong": _i(v.get("wrong"), hi=10**6)}
    u["topic_stats"] = ts
    return u


def sanitize_questions(qs) -> list:
    out = []
    for q in qs if isinstance(qs, list) else []:
        if isinstance(q, dict) and str(q.get("question", "")).strip() and isinstance(q.get("choices", q.get("options")), list):
            out.append(q)
    return out[:200]


def avatar_mod(avatar_id: str) -> dict:
    m = {"xp_mult": 1.0, "coin_mult": 1.0, "wrong_mult": 1.0, "dmg_mult": 1.0}
    m.update(AVATARS.get(avatar_id, AVATARS[DEFAULT_AVATAR])["mod"])
    return m


def apply_xp(data: dict, xp: int):
    """เพิ่ม XP แล้วเลื่อนเลเวล (สูตรเดิม: max_xp x1.5 ทุกเลเวล) คืนจำนวนเลเวลที่เพิ่ม"""
    data["xp"] += xp
    ups = 0
    while data["xp"] >= data["max_xp"]:
        data["xp"] -= data["max_xp"]
        data["level"] += 1
        data["max_xp"] = int(data["max_xp"] * 1.5)
        ups += 1
    return ups


def stage_status(user: dict, stage_id: int):
    """(ปลดล็อกไหม, เหตุผลถ้าล็อก)"""
    if stage_id not in user["unlocked_stages"]:
        return False, f"ต้องผ่านด่านที่ {stage_id - 1} “{MONSTERS[stage_id - 1]['place']}” ก่อน"
    need = MONSTERS[stage_id].get("req_stars", 0)
    if user["stars"] < need:
        return False, f"ต้องมีดาวอย่างน้อย {need} ดวง (ตอนนี้มี {user['stars']} ดวง) ลองกลับไปเล่นด่านเก่าให้ได้ดาวเพิ่ม"
    return True, ""


def calc_stars(accuracy: float) -> int:
    return 3 if accuracy >= 0.85 else 2 if accuracy >= 0.6 else 1


class GameEngine:
    """ข้อมูลเกมและตัวละคร ภาพทุกชิ้นเป็น SVG ในโฟลเดอร์ assets/ (ไม่ใช้ลิงก์รูปภายนอก)"""

    def __init__(self):
        self.init_state()

    def init_state(self):
        s = st.session_state
        if "user_data" not in s:
            pid = st.query_params.get("p")
            if not storage.valid_id(pid):
                pid = storage.new_id()
                st.query_params["p"] = pid  # id อยู่ใน URL รีเฟรชแล้วยังเป็นผู้เล่นคนเดิม
            s.player_id = pid
            data = storage.load(pid) if storage.exists(pid) else None
            s.user_data = sanitize_user(data.get("user_data") if data else None)
            s.active_questions = sanitize_questions(data.get("active_questions") if data else [])
            s.quiz_title = str(data.get("quiz_title", ""))[:80] if data else ""
        # รองรับเซฟ/Session State จากเวอร์ชันก่อนหน้า และเติมฟิลด์ใหม่โดยไม่ลบความคืบหน้าเดิม
        s.user_data = sanitize_user(s.user_data)
        s.setdefault("active_questions", [])
        s.setdefault("quiz_title", "")
        s.setdefault("save_ok", True)
        # ตารางข้อมูลถูกสร้างใหม่ทุกครั้ง (ไม่เก็บ URL รูปเก่าใน session state)
        s.avatars = AVATARS
        s.monsters = MONSTERS
        d = s.user_data
        if d.get("selected_avatar") not in d["unlocked_avatars"]:
            d["selected_avatar"] = DEFAULT_AVATAR

    # ---- บันทึก / โหลด
    def snapshot(self) -> dict:
        s = st.session_state
        return {"v": SAVE_VERSION, "user_data": s.user_data, "active_questions": s.active_questions,
                "quiz_title": s.quiz_title}

    def save(self):
        st.session_state.save_ok = storage.save(st.session_state.player_id, self.snapshot())

    def restore(self, raw) -> bool:
        """กู้คืนจากไฟล์เซฟที่ผู้ใช้อัปโหลด"""
        if not isinstance(raw, dict) or "user_data" not in raw:
            return False
        s = st.session_state
        s.user_data = sanitize_user(raw.get("user_data"))
        s.active_questions = sanitize_questions(raw.get("active_questions"))
        s.quiz_title = str(raw.get("quiz_title", ""))[:80]
        self.save()
        return True

    def set_quiz(self, title: str, questions: list):
        st.session_state.active_questions = questions
        st.session_state.quiz_title = title
        self.save()

    # ---- รางวัล / ปลดล็อก
    def add_reward(self, xp_gained, coins_gained, stars_gained=0):
        data = st.session_state.user_data
        data["coins"] += coins_gained
        data["stars"] = min(MAX_STARS, data["stars"] + stars_gained)
        return apply_xp(data, xp_gained)

    def unlock_next_stage(self, current_stage):
        nxt = current_stage + 1
        unlocked = st.session_state.user_data["unlocked_stages"]
        if nxt <= LAST_STAGE and nxt not in unlocked:
            unlocked.append(nxt)
            return nxt
        return None

    def unlock_avatar(self, avatar_id: str):
        d = st.session_state.user_data
        a = AVATARS[avatar_id]
        if avatar_id in d["unlocked_avatars"]:
            return False, "ปลดล็อกแล้ว"
        if d["coins"] < a["cost"]:
            return False, f"เหรียญไม่พอ ต้องใช้ {a['cost']} (มี {d['coins']})"
        d["coins"] -= a["cost"]
        d["unlocked_avatars"].append(avatar_id)
        self.save()
        return True, ""

    def select_avatar(self, avatar_id: str):
        d = st.session_state.user_data
        if avatar_id in d["unlocked_avatars"]:
            d["selected_avatar"] = avatar_id
            self.save()

    def buy_weapon(self, weapon_id: str):
        d = st.session_state.user_data
        if weapon_id not in WEAPONS:
            return False, "ไม่พบอาวุธนี้"
        if weapon_id in d["unlocked_weapons"]:
            return False, "มีอาวุธนี้แล้ว"
        cost = WEAPONS[weapon_id]["cost"]
        if d["coins"] < cost:
            return False, f"เหรียญไม่พอ ต้องใช้ {cost} เหรียญ"
        d["coins"] -= cost
        d["unlocked_weapons"].append(weapon_id)
        d["selected_weapon"] = weapon_id
        self.save()
        return True, ""

    def select_weapon(self, weapon_id: str):
        d = st.session_state.user_data
        if weapon_id in d["unlocked_weapons"]:
            d["selected_weapon"] = weapon_id
            self.save()

    def record_error(self, entry: dict):
        d = st.session_state.user_data
        if not isinstance(entry, dict) or not entry.get("question"):
            return
        item = dict(entry)
        item["question"] = str(item.get("question", ""))[:1000]
        item["explanation"] = str(item.get("explanation", ""))[:1500]
        item["topic"] = str(item.get("topic", "ทั่วไป"))[:60]
        item["subject"] = str(item.get("subject", "ไม่ระบุ"))[:60]
        item["wrong_answer"] = str(item.get("wrong_answer", ""))[:500]
        item["correct_answer"] = str(item.get("correct_answer", ""))[:500]
        item["reviewed"] = False
        # ป้องกันบันทึกข้อเดิมซ้ำติดกัน
        if not d["error_notebook"] or d["error_notebook"][-1].get("question") != item["question"]:
            d["error_notebook"].append(item)
            d["error_notebook"] = d["error_notebook"][-200:]
        self.save()

    def finish_battle(self, stage_id: int, cleared: bool, correct: int, wrong: int, xp: int, coins: int,
                      best_streak: int, topics: dict):
        """สรุปผลด่านและบันทึก คืน dict รางวัลสำหรับแสดงผล"""
        d = st.session_state.user_data
        total = correct + wrong
        acc = correct / total if total else 0
        stars = calc_stars(acc) if cleared else 0
        key = str(stage_id)
        old = d["stage_stars"].get(key, 0)
        first = cleared and old == 0
        bonus_xp = bonus_coins = 0
        if cleared:
            m = avatar_mod(d["selected_avatar"])
            bonus_xp = round((50 + 10 * (stage_id - 1)) * m["xp_mult"])
            bonus_coins = round((30 + 10 * (stage_id - 1) + (20 if first else 0)) * m["coin_mult"])
        new_stars = max(0, stars - old)
        if stars > old:
            d["stage_stars"][key] = stars
        ups = self.add_reward(xp + bonus_xp, coins + bonus_coins, new_stars)
        newly = self.unlock_next_stage(stage_id) if cleared else None
        d["best_streak"] = max(d["best_streak"], best_streak)
        d["total_correct"] += correct
        d["total_answered"] += total
        for t, v in topics.items():
            e = d["topic_stats"].setdefault(t, {"correct": 0, "wrong": 0})
            e["correct"] += v["correct"]
            e["wrong"] += v["wrong"]
        self.save()
        return {"xp": xp + bonus_xp, "coins": coins + bonus_coins, "bonus_xp": bonus_xp, "bonus_coins": bonus_coins,
                "stars": stars, "new_stars": new_stars, "level_ups": ups, "level": d["level"],
                "newly_unlocked": newly, "first": first}
