"""ตัวขับเคลื่อนแอปด้วย Streamlit จำลอง: ใช้ทั้งใน pytest และตอนจับภาพหน้าจอ"""
import os
import runpy
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fake_streamlit as fs  # noqa: E402


def install_fake_genai():
    """จำลอง google.genai เมื่อไม่มีแพ็กเกจจริง (ตอนทดสอบเท่านั้น) เพื่อให้ import ai_engine ได้"""
    try:
        import google.genai  # noqa: F401
        return False
    except ImportError:
        import types
        g = types.ModuleType("google"); g.__path__ = []
        ge = types.ModuleType("google.genai")
        t = types.ModuleType("google.genai.types"); er = types.ModuleType("google.genai.errors")

        class APIError(Exception):
            pass

        class GenerateContentConfig:
            def __init__(self, **k): self.k = k

        class Client:
            def __init__(self, **k): self.models = self
            def generate_content(self, **k): raise APIError("fake client: no network")

        ge.Client, ge.types, ge.errors = Client, t, er
        t.GenerateContentConfig, er.APIError = GenerateContentConfig, APIError
        g.genai = ge
        sys.modules.update({"google": g, "google.genai": ge, "google.genai.types": t, "google.genai.errors": er})
        return True


class App:
    def __init__(self, workdir=None):
        self.work = workdir or tempfile.mkdtemp(prefix="aqt_")
        os.environ["SAVE_DIR"] = os.path.join(self.work, "saves")
        os.environ.pop("GEMINI_API_KEY", None)
        os.chdir(self.work)  # saved_quizzes/ จะถูกสร้างในโฟลเดอร์ชั่วคราว ไม่ปนกับโปรเจกต์
        for m in [m for m in sys.modules if m in ("app", "game_engine", "visuals", "storage", "ai_engine", "pdf_processor", "games", "games.battle")]:
            del sys.modules[m]
        self.st = fs.install()
        install_fake_genai()

    def run(self, press=(), values=None, radio_cb=None, max_reruns=10):
        st = self.st
        st.pressed = set(press)
        if values:
            st.values.update(values)
        st.radio_cb = radio_cb
        for _ in range(max_reruns):
            st.reset_run()
            try:
                runpy.run_path(os.path.join(ROOT, "app.py"), run_name="__main__")
                break
            except fs.Rerun:
                st.pressed = set()  # ปุ่มมีผลเฉพาะรอบที่กด
                continue
        else:
            raise RuntimeError("rerun loop")
        return st

    def html(self):
        return fs.page_html(self.st)
