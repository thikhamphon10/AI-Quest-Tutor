import streamlit as st


class GameEngine:
    """ข้อมูลเกมและตัวละคร ใช้ Emoji แทนรูปภาพภายนอกเพื่อไม่ให้รูปเสีย"""

    def __init__(self):
        self.init_state()

    def init_state(self):
        if "user_data" not in st.session_state:
            st.session_state.user_data = {
                "level": 1,
                "xp": 0,
                "max_xp": 100,
                "coins": 50,
                "stars": 0,
                "unlocked_stages": [1],
                "selected_avatar": "shadow_fox",
                "inventory": [],
            }

        # Rebuild these definitions each rerun so old image URLs in session state are removed.
        st.session_state.avatars = {
            "shadow_fox": {
                "name": "Shadow Fox",
                "icon": "🦊",
                "class": "นักดาบเงา",
                "color": "#8B5CF6",
                "desc": "นักดาบเงาความเร็วสูง ผู้กล้าประจำทีม",
                "skill": "Shadow Slash",
            },
            "arcane_mage": {
                "name": "Arcane Mage",
                "icon": "🧙🏻‍♀️",
                "class": "จอมเวทอาร์เคน",
                "color": "#EC4899",
                "desc": "จอมเวทผู้ควบคุมพลังดาวและคาถา",
                "skill": "Star Burst",
            },
            "cyber_knight": {
                "name": "Cyber Knight",
                "icon": "🦾",
                "class": "อัศวินไซเบอร์",
                "color": "#06B6D4",
                "desc": "นักรบเทคโนโลยีเกราะพลังงาน",
                "skill": "Pulse Strike",
            },
            "storm_dragon": {
                "name": "Storm Dragon",
                "icon": "🐲",
                "class": "มังกรสายฟ้า",
                "color": "#F59E0B",
                "desc": "คู่หูมังกรผู้ใช้สายฟ้าและเปลวเพลิง",
                "skill": "Thunder Roar",
            },
        }

        st.session_state.monsters = {
            1: {"name": "Mint Slime", "title": "สไลม์คริสตัล", "icon": "🟢", "hp": 100, "max_hp": 100, "color": "#34D399", "reward": "เริ่มต้นการผจญภัย"},
            2: {"name": "Night Bat", "title": "ค้างคาวรัตติกาล", "icon": "🦇", "hp": 150, "max_hp": 150, "color": "#8B5CF6", "reward": "ปลดล็อกถ้ำเงา"},
            3: {"name": "Inferno Dragon", "title": "มังกรเพลิง", "icon": "🐉", "hp": 200, "max_hp": 200, "color": "#F97316", "reward": "พิชิตปราสาทมังกร"},
        }

        data = st.session_state.user_data
        if data.get("selected_avatar") not in st.session_state.avatars:
            data["selected_avatar"] = "shadow_fox"

    def add_reward(self, xp_gained, coins_gained, stars_gained=1):
        data = st.session_state.user_data
        data["xp"] += xp_gained
        data["coins"] += coins_gained
        data["stars"] += stars_gained
        while data["xp"] >= data["max_xp"]:
            data["xp"] -= data["max_xp"]
            data["level"] += 1
            data["max_xp"] = int(data["max_xp"] * 1.5)

    def unlock_next_stage(self, current_stage):
        next_stage = current_stage + 1
        unlocked = st.session_state.user_data["unlocked_stages"]
        if next_stage <= 3 and next_stage not in unlocked:
            unlocked.append(next_stage)
