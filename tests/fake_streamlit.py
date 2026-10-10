"""ตัวจำลอง Streamlit แบบเบา ๆ สำหรับทดสอบเมื่อติดตั้ง streamlit จริงไม่ได้
- รันสคริปต์หน้าเว็บจริง (app.py) ได้ กดปุ่มด้วยการระบุ key / label
- เก็บ HTML ที่แอปสร้าง เพื่อนำไปเรนเดอร์ในเบราว์เซอร์ดูหน้าตา
ข้อจำกัด: ไม่ใช่ Streamlit จริง จึงไม่ได้ทดสอบ DOM/สไตล์เฉพาะของ Streamlit"""
import contextlib
import html as _h
import sys
import types


class Rerun(Exception):
    pass


class State(dict):
    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError:
            raise AttributeError(k)

    def __setattr__(self, k, v):
        self[k] = v

    def __delattr__(self, k):
        del self[k]


class Row:
    def __init__(self, kids, kind="row"):
        self.kids, self.kind = kids, kind

    def render(self):
        if self.kind == "row":
            return '<div class="fk-row">' + "".join(f'<div class="fk-col">{render(k)}</div>' for k in self.kids) + "</div>"
        return f'<div class="fk-box">{render(self.kids[0])}</div>'


def render(buf):
    return "".join(x.render() if hasattr(x, "render") else x for x in buf)


class Fake(types.ModuleType):
    def __init__(self):
        super().__init__("streamlit")
        self.session_state = State()
        self.query_params = {}
        self.reset_run()
        self.pressed = set()
        self.values = {}
        self.radio_cb = None
        self.log = []          # ข้อความ/คำเตือนทั้งหมดที่แสดง
        self.sidebar = _Sidebar(self)

    # ---- รอบการรัน
    def reset_run(self):
        self.root = []
        self.cur = self.root
        self.log = []
        self.buttons = []
        if hasattr(self, 'sidebar'):
            self.sidebar.buf[:] = []

    def _add(self, s):
        self.cur.append(s)

    @contextlib.contextmanager
    def _into(self, buf):
        old = self.cur
        self.cur = buf
        try:
            yield
        finally:
            self.cur = old

    # ---- องค์ประกอบ
    def set_page_config(self, **k): pass

    def markdown(self, s, unsafe_allow_html=False, **k):
        self._add(s if unsafe_allow_html else f'<div class="md">{_h.escape(str(s))}</div>')
        self.log.append(("md", str(s)[:200]) if not unsafe_allow_html else ("html", ""))

    def _msg(self, kind, s, **k):
        self._add(f'<div class="alert {kind}">{_h.escape(str(s))}</div>')
        self.log.append((kind, str(s)))

    def success(self, s, **k): self._msg("success", s)
    def info(self, s, **k): self._msg("info", s)
    def warning(self, s, **k): self._msg("warning", s)
    def error(self, s, **k): self._msg("error", s)
    def toast(self, s, **k): self.log.append(("toast", str(s)))
    def caption(self, s, **k): self._add(f'<div class="cap">{_h.escape(str(s))}</div>')
    def write(self, s, **k): self._add(f'<p>{_h.escape(str(s))}</p>')
    def title(self, s, **k): self._add(f'<h1>{_h.escape(str(s))}</h1>')
    def header(self, s, **k): self._add(f'<h2>{_h.escape(str(s))}</h2>')
    def subheader(self, s, **k): self._add(f'<h3>{_h.escape(str(s))}</h3>')

    def metric(self, label, value, **k):
        self._add(f'<div class="metric"><small>{_h.escape(str(label))}</small><b>{_h.escape(str(value))}</b></div>')

    def progress(self, v, text="", **k):
        assert 0 <= v <= 1, f"progress value out of range: {v}"
        self._add(f'<div class="prog"><div style="width:{v*100:.0f}%"></div><span>{_h.escape(str(text))}</span></div>')

    @contextlib.contextmanager
    def spinner(self, t=""):
        yield

    def button(self, label, key=None, disabled=False, type="secondary", **k):
        self.buttons.append(key or label)
        self._add(f'<button class="{type}" {"disabled" if disabled else ""}>{_h.escape(str(label))}</button>')
        hit = (key in self.pressed or label in self.pressed) and not disabled
        if hit:
            self.pressed.discard(key)
            self.pressed.discard(label)
        return hit

    def download_button(self, label, **k):
        self._add(f'<button class="secondary">{_h.escape(label)}</button>')
        return False

    def text_area(self, label, **k):
        self._add(f'<div class="inp">{_h.escape(label)}</div>')
        return self.values.get(label, "")

    def text_input(self, label, value="", **k):
        self._add(f'<div class="inp">{_h.escape(label)}</div>')
        return self.values.get(label, value)

    def file_uploader(self, label, **k):
        self._add(f'<div class="inp">{_h.escape(label)}</div>')
        return self.values.get(label)

    def selectbox(self, label, options, index=0, format_func=str, **k):
        self._add(f'<div class="inp">{_h.escape(label)}: {_h.escape(str(format_func(options[index])))}</div>')
        return self.values.get(label, options[index] if options else None)

    def radio(self, label, options, index=0, format_func=str, key=None, horizontal=False, **k):
        self._add('<div class="radio">' + "".join(f'<div>○ {_h.escape(str(format_func(o)))}</div>' for o in options) + "</div>")
        if self.radio_cb:
            r = self.radio_cb(key, options)
            if r is not None:
                return r
        if key in self.values:
            return self.values[key]
        return None if index is None else options[index]

    # ---- ตัวจัดวาง
    def columns(self, spec, **k):
        n = spec if isinstance(spec, int) else len(spec)
        kids = [[] for _ in range(n)]
        self._add(Row(kids))
        return [_Ctx(self, b) for b in kids]

    def tabs(self, labels):
        out = []
        for l in labels:
            b = []
            self._add(f'<div class="tab">{_h.escape(l)}</div>')
            self._add(Row([b], "box"))
            out.append(_Ctx(self, b))
        return out

    def container(self, **k):
        b = []
        self._add(Row([b], "box"))
        return _Ctx(self, b)

    def expander(self, label, expanded=False, **k):
        b = []
        self._add(f'<div class="exp">▸ {_h.escape(label)}</div>')
        self._add(Row([b], "box"))
        return _Ctx(self, b)

    def dialog(self, title, **k):
        def deco(fn):
            def run(*a, **kw):
                self.log.append(("dialog", title))
                b = []
                self._add(f'<div class="dlg"><b>{_h.escape(title)}</b>')
                self._add(Row([b], "box"))
                self._add("</div>")
                with self._into(b):
                    return fn(*a, **kw)
            return run
        return deco

    def rerun(self):
        raise Rerun()

    def stop(self):
        raise Rerun()


class _Ctx:
    def __init__(self, st, buf):
        self.st, self.buf = st, buf

    def __enter__(self):
        self.__dict__.setdefault("_stack", []).append(self.st.cur)
        self.st.cur = self.buf
        return self

    def __exit__(self, *a):
        self.st.cur = self._stack.pop()

    def __getattr__(self, name):  # col.metric(...), col.button(...)
        fn = getattr(self.st, name)

        def call(*a, **k):
            with self:
                return fn(*a, **k)
        return call


class _Sidebar(_Ctx):
    def __init__(self, st):
        super().__init__(st, [])



def install():
    fake = Fake()
    sys.modules["streamlit"] = fake
    return fake


def page_html(fake, css_extra=""):
    side = render(fake.sidebar.buf)
    main = render(fake.root)
    return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{{margin:0;font-family:'Mali','Noto Sans Thai',sans-serif;}}
.app{{display:flex;min-height:100vh}} .side{{width:250px;flex:none;padding:1rem;box-sizing:border-box;}}
.main{{flex:1;padding:1rem 2rem;max-width:1100px;box-sizing:border-box;min-width:0}}
.fk-row{{display:flex;gap:1rem;flex-wrap:wrap}}.fk-col{{flex:1 1 140px;min-width:0}}
button{{width:100%;padding:.7rem;border-radius:99px;border:3px solid #fff;background:linear-gradient(180deg,#fff,#ffeaf4);font-weight:700;margin:.2rem 0;font-family:inherit;color:#4a3560;box-shadow:0 4px 0 #f2c2da}}
button.primary{{background:linear-gradient(180deg,#ffb7d6,#ff86b8);color:#fff}}
.alert{{padding:.7rem 1rem;border-radius:18px;margin:.4rem 0}}.success{{background:#dff7e8}}.info{{background:#e3f0ff}}.warning{{background:#fff4d6}}.error{{background:#ffe0e6}}
.cap{{font-size:.85rem;opacity:.75;margin:.2rem 0}} .metric{{background:#ffffffc0;border-radius:18px;padding:.5rem .8rem}} .metric small{{display:block}}
.prog{{position:relative;background:#efe5fa;border-radius:99px;height:22px;margin:.3rem 0;overflow:hidden}}.prog div{{height:100%;background:linear-gradient(90deg,#ffb3d9,#b79cff)}}.prog span{{position:absolute;left:10px;top:1px;font-size:.8rem}}
.dlg{{border:3px dashed #b79cff;border-radius:20px;padding:.8rem;margin:.5rem 0;background:#fff}}.radio div{{margin:.2rem 0}}.exp,.tab,.inp{{font-weight:700;margin:.3rem 0}}
@media(max-width:700px){{.side{{display:none}}.main{{padding:.5rem .7rem}}}}
{css_extra}</style></head><body><div class="stApp"><div class="app"><div class="side">{side}</div><div class="main">{main}</div></div></div></body></html>"""
