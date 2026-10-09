import streamlit as st

class GameEngine:
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
                "selected_avatar": "bunny",
                "inventory": []
            }

        if "avatars" not in st.session_state:
            st.session_state.avatars = {
                "bunny": {
                    "name": "น้องต่ายสายเวท",
                    "img": "https://img.icons8.com/isometric-3d/100/rabbit.png",
                    "desc": "เชี่ยวชาญการยิงคาถาเวทมนตร์สีชมพู"
                },
                "cat": {
                    "name": "เหมียวนักปราชญ์",
                    "img": "https://img.icons8.com/isometric-3d/100/cat.png",
                    "desc": "เพิ่มโบนัส Coin 10% เมื่อตอบถูก"
                },
                "bear": {
                    "name": "หมีเกราะหนา",
                    "img": "https://img.icons8.com/isometric-3d/100/bear.png",
                    "desc": "ช่วยลดโอกาสโดนโจมตีหนัก"
                },
                "fox": {
                    "name": "จิ้งจอกนักเล่าเรื่อง",
                    "img": "https://img.icons8.com/isometric-3d/100/fox.png",
                    "desc": "ได้รับ XP มากขึ้นในการต่อสู้"
                }
            }

        if "monsters" not in st.session_state:
            st.session_state.monsters = {
                1: {"name": "Slime น้อยจอมขี้เกียจ", "hp": 100, "max_hp": 100, "img": "https://img.icons8.com/isometric-3d/100/slime.png"},
                2: {"name": "ค้างคาวราตรีจอมง่วง", "hp": 150, "max_hp": 150, "img": "https://img.icons8.com/isometric-3d/100/bat.png"},
                3: {"name": "มังกรตัวจิ๋วพ่นไฟ", "hp": 200, "max_hp": 200, "img": "https://img.icons8.com/isometric-3d/100/dragon.png"}
            }

    def add_reward(self, xp_gained, coins_gained, stars_gained=1):
        data = st.session_state.user_data
        data["xp"] += xp_gained
        data["coins"] += coins_gained
        data["stars"] += stars_gained

        # Level up logic
        while data["xp"] >= data["max_xp"]:
            data["xp"] -= data["max_xp"]
            data["level"] += 1
            data["max_xp"] = int(data["max_xp"] * 1.5)

    def unlock_next_stage(self, current_stage):
        next_stage = current_stage + 1
        if next_stage not in st.session_state.user_data["unlocked_stages"]:
            st.session_state.user_data["unlocked_stages"].append(next_stage)
