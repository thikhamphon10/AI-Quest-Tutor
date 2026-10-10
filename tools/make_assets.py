"""สร้างภาพตัวละคร/มอนสเตอร์/แผนที่ (SVG) -> assets/
รัน: python tools/make_assets.py
ภาพทั้งหมดเป็นงานวาดเองด้วยโค้ด (ไม่มีลิขสิทธิ์ของผู้อื่น) แก้สี/รูปทรงแล้วรันใหม่ได้
"""
import math
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
INK = "#4a3560"       # สีเส้น/ตา
BLUSH = "#ff9db8"


def star(cx, cy, R, r, n=5, rot=-90):
    pts = []
    for i in range(n * 2):
        rad = R if i % 2 == 0 else r
        a = math.radians(rot + i * 180 / n)
        pts.append(f"{cx + rad * math.cos(a):.1f},{cy + rad * math.sin(a):.1f}")
    return " ".join(pts)


def svg(w, h, body, x0=0):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} 0 {w} {h}" width="{w}" height="{h}">'
            f'{body}</svg>')


# ---------------------------------------------------------------- faces
def eyes(state, cx, cy, gap=24, size=1.0):
    xl, xr = cx - gap, cx + gap
    if state == "cheer":      # ตาหยี ^ ^
        return "".join(
            f'<path d="M{x-9*size},{cy+3} Q{x},{cy-10*size} {x+9*size},{cy+3}" fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>'
            for x in (xl, xr))
    if state == "tired":      # หลับตา ง่วง
        return "".join(
            f'<path d="M{x-9*size},{cy} Q{x},{cy+7*size} {x+9*size},{cy}" fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>'
            for x in (xl, xr)) + f'<path d="M{xr+22},{cy-18} q6,-2 12,0 l-12,8 q6,-2 12,0" fill="none" stroke="#8ec5ff" stroke-width="3" stroke-linecap="round"/>'
    if state == "hurt":       # > <
        return (f'<path d="M{xl-8},{cy-8} L{xl+5},{cy} L{xl-8},{cy+8}" fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
                f'<path d="M{xr+8},{cy-8} L{xr-5},{cy} L{xr+8},{cy+8}" fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
    if state == "ko":         # ตาวนเป็นก้นหอย
        out = ""
        for x in (xl, xr):
            out += (f'<circle cx="{x}" cy="{cy}" r="9" fill="#fff" stroke="{INK}" stroke-width="2.5"/>'
                    f'<path d="M{x},{cy} m0,-2 a2.5,2.5 0 1 1 -2.5,2.5 a5,5 0 1 1 5,5 a7.5,7.5 0 1 1 -7.5,-7.5" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>')
        return out
    out = ""
    for x in (xl, xr):
        out += (f'<ellipse cx="{x}" cy="{cy}" rx="{8*size}" ry="{10*size}" fill="{INK}"/>'
                f'<circle cx="{x-2.5*size}" cy="{cy-3.5*size}" r="{3.2*size}" fill="#fff"/>'
                f'<circle cx="{x+2.5*size}" cy="{cy+3*size}" r="{1.5*size}" fill="#fff" opacity=".8"/>')
    return out


def mouth(state, cx, cy):
    if state == "cheer":
        return f'<path d="M{cx-10},{cy} Q{cx},{cy+16} {cx+10},{cy} Z" fill="#ff7f9c" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>'
    if state == "tired":
        return f'<path d="M{cx-6},{cy+3} q3,-3 6,0 q3,3 6,0" fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>'
    if state in ("hurt", "ko"):
        extra = f'<path d="M{cx+2},{cy+4} q4,12 9,4 q-1,-5 -9,-4Z" fill="#ff8fa8"/>' if state == "ko" else ""
        return f'<ellipse cx="{cx}" cy="{cy+3}" rx="6" ry="5" fill="#7a3d5c"/>' + extra
    return f'<path d="M{cx-8},{cy} Q{cx-4},{cy+7} {cx},{cy} Q{cx+4},{cy+7} {cx+8},{cy}" fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>'


def blush(cx, cy, gap=44):
    return "".join(f'<ellipse cx="{x}" cy="{cy}" rx="10" ry="6" fill="{BLUSH}" opacity=".75"/>' for x in (cx - gap, cx + gap))


# ---------------------------------------------------------------- heroes
HEROES = {
    "bunny": dict(fur="#ffffff", edge="#e5d3f2", inner="#ffc2d9", robe="#ffd1e8"),
    "cat":   dict(fur="#d9c8ff", edge="#b9a2f0", inner="#ffc2d9", robe="#c0d4ff"),
    "bear":  dict(fur="#f1cba5", edge="#d9a77c", inner="#ffd9c2", robe="#ffe49e"),
    "fox":   dict(fur="#ffc08a", edge="#f09a5a", inner="#ffffff", robe="#bfeacb"),
}


def wand(kind):
    stick = '<line x1="150" y1="158" x2="176" y2="104" stroke="#c99a6b" stroke-width="5" stroke-linecap="round"/>'
    if kind == "bunny":
        top = f'<polygon points="{star(180,92,17,8)}" fill="#ffe27a" stroke="#f0b93c" stroke-width="2.5" stroke-linejoin="round"/>'
    elif kind == "cat":
        top = ('<path d="M184,76 a17,17 0 1 0 8,28 a14,14 0 1 1 -8,-28Z" fill="#fff0a8" stroke="#f0c850" stroke-width="2.5" stroke-linejoin="round"/>')
    elif kind == "bear":
        top = ('<path d="M180,106 C158,90 166,72 180,82 C194,72 202,90 180,106Z" fill="#ff8fb5" stroke="#f0608f" stroke-width="2.5" stroke-linejoin="round"/>')
    else:
        top = ('<path d="M180,106 C164,100 166,84 176,74 C176,84 184,84 184,76 C196,86 196,102 180,106Z" fill="#ff9a4d" stroke="#e8702a" stroke-width="2.5" stroke-linejoin="round"/>'
               '<path d="M180,104 C172,100 174,92 180,88 C184,94 188,98 180,104Z" fill="#ffe08a"/>')
    return stick + top


def hero_svg(name, state="normal"):
    c = HEROES[name]
    fur, edge, inner, robe = c["fur"], c["edge"], c["inner"], c["robe"]
    st = f'stroke="{edge}" stroke-width="3.5" stroke-linejoin="round"'
    b = '<ellipse cx="100" cy="209" rx="54" ry="8" fill="#6b4c8a" opacity=".12"/>'
    behind, front = "", ""
    if name == "bunny":
        behind += (f'<g transform="rotate(-9 72 56)"><ellipse cx="72" cy="40" rx="17" ry="42" fill="{fur}" {st}/><ellipse cx="72" cy="44" rx="8" ry="28" fill="{inner}"/></g>'
                   f'<g transform="rotate(9 128 56)"><ellipse cx="128" cy="40" rx="17" ry="42" fill="{fur}" {st}/><ellipse cx="128" cy="44" rx="8" ry="28" fill="{inner}"/></g>')
        front += ('<path d="M120,58 l-14,-10 l2,18 z M120,58 l14,-10 l-2,18 z" fill="#ff8fc0" stroke="#e8609a" stroke-width="2" stroke-linejoin="round"/>'
                  '<circle cx="120" cy="58" r="4.5" fill="#ffd1e8" stroke="#e8609a" stroke-width="2"/>')
    elif name == "cat":
        behind += (f'<path d="M150,190 C196,196 206,150 184,134" fill="none" stroke="{edge}" stroke-width="16" stroke-linecap="round"/>'
                   f'<path d="M150,190 C196,196 206,150 184,134" fill="none" stroke="{fur}" stroke-width="10" stroke-linecap="round"/>')
        behind += (f'<path d="M46,76 L52,22 L94,52 Z" fill="{fur}" {st}/><path d="M154,76 L148,22 L106,52 Z" fill="{fur}" {st}/>'
                   f'<path d="M56,62 L58,36 L78,52 Z" fill="{inner}"/><path d="M144,62 L142,36 L122,52 Z" fill="{inner}"/>')
        front += ('<path d="M82,128 l-34,-4 M82,134 l-34,6 M118,128 l34,-4 M118,134 l34,6" stroke="#8d78c8" stroke-width="2.2" stroke-linecap="round" fill="none" opacity=".7"/>'
                  '<path d="M100,112 l-5,-3 h10 z" fill="#ff8fa8" stroke="#ff8fa8" stroke-width="2" stroke-linejoin="round"/>'
                  f'<polygon points="{star(70,58,9,4)}" fill="#fff0a8" stroke="#f0c850" stroke-width="2"/>')
    elif name == "bear":
        behind += (f'<circle cx="54" cy="58" r="21" fill="{fur}" {st}/><circle cx="146" cy="58" r="21" fill="{fur}" {st}/>'
                   f'<circle cx="54" cy="60" r="10" fill="{inner}"/><circle cx="146" cy="60" r="10" fill="{inner}"/>')
        front += ('<ellipse cx="100" cy="118" rx="23" ry="17" fill="#fff4e6" stroke="#e8c9a8" stroke-width="2.5"/>'
                  '<ellipse cx="100" cy="111" rx="7" ry="5" fill="#6b4a3a"/>'
                  '<g><circle cx="72" cy="52" r="7" fill="#ff9fc0"/><circle cx="72" cy="52" r="3" fill="#fff3a0"/>'
                  '<circle cx="90" cy="46" r="7" fill="#ffe27a"/><circle cx="90" cy="46" r="3" fill="#fff"/>'
                  '<circle cx="110" cy="46" r="7" fill="#bde0ff"/><circle cx="110" cy="46" r="3" fill="#fff"/>'
                  '<circle cx="128" cy="52" r="7" fill="#d9b8ff"/><circle cx="128" cy="52" r="3" fill="#fff3a0"/></g>')
    else:  # fox
        behind += (f'<path d="M148,196 C206,206 214,146 184,128 C190,158 168,176 148,176Z" fill="{fur}" {st}/>'
                   '<path d="M184,128 C196,138 204,156 200,170 C190,160 182,148 184,128Z" fill="#fff"/>')
        behind += (f'<path d="M44,80 L54,16 L98,54 Z" fill="{fur}" {st}/><path d="M156,80 L146,16 L102,54 Z" fill="{fur}" {st}/>'
                   '<path d="M54,16 L62,40 L48,46Z" fill="#8a5a44"/><path d="M146,16 L138,40 L152,46Z" fill="#8a5a44"/>')
        front += ('<path d="M44,112 q12,-6 18,8 q-8,12 -18,12 z M156,112 q-12,-6 -18,8 q8,12 18,12 z" fill="#fff"/>'
                  '<path d="M100,108 q-6,0 -6,5 q6,6 12,0 q0,-5 -6,-5Z" fill="#6b4a3a"/>')
    # ร่างกาย (เสื้อคลุม) + เท้า + แขน
    body = (f'<ellipse cx="82" cy="198" rx="17" ry="9" fill="{fur}" {st}/><ellipse cx="118" cy="198" rx="17" ry="9" fill="{fur}" {st}/>'
            f'<path d="M60,176 C58,150 78,140 100,140 C122,140 142,150 140,176 C138,194 62,194 60,176Z" fill="{robe}" stroke="#ffffff" stroke-width="3" stroke-linejoin="round"/>'
            f'<path d="M78,150 Q100,164 122,150" fill="none" stroke="#fff" stroke-width="3" opacity=".8"/>'
            f'<circle cx="100" cy="162" r="6" fill="#ffe27a" stroke="#f0b93c" stroke-width="2"/>')
    if name == "fox":
        body += '<path d="M82,146 Q100,160 118,146 L112,138 Q100,148 88,138Z" fill="#7ed3a0" stroke="#58b880" stroke-width="2.5" stroke-linejoin="round"/>'
    arms = (f'<circle cx="58" cy="164" r="11" fill="{fur}" {st}/>'
            f'<circle cx="148" cy="158" r="11" fill="{fur}" {st}/>')
    head = f'<ellipse cx="100" cy="100" rx="58" ry="52" fill="{fur}" {st}/>'
    face = blush(100, 118, 40) + eyes(state, 100, 100, 26) + mouth(state, 100, 124 if name != "bear" and name != "fox" else 126)
    if name in ("bear", "fox", "cat"):
        face = face  # จมูกวาดไว้ใน front แล้ว
    # ลำดับวาด: เงา, ของด้านหลัง, ลำตัว, ไม้เท้า, แขน, หัว, หน้า, ของด้านหน้า
    # (bear/fox วาดปากกับจมูกร่วมกัน: front มาก่อนหน้า เพื่อให้ปากทับ muzzle)
    parts = [b, behind, wand(name) if state != "tired" else "", body, arms, head, front, face]
    if state == "cheer":
        parts.append(f'<polygon points="{star(30,70,8,3.5)}" fill="#ffe27a"/><polygon points="{star(176,40,6,2.6)}" fill="#ffb3d9"/>')
    return svg(230, 220, "".join(parts), x0=-15)


# ---------------------------------------------------------------- monsters
def orbit_stars(cx, cy):
    out = ""
    for i, (dx, dy, r, col) in enumerate([(-58, -10, 9, "#ffe27a"), (0, -34, 7, "#ffb3d9"), (58, -10, 9, "#bde0ff")]):
        out += f'<polygon points="{star(cx+dx,cy+dy,r,r*0.45)}" fill="{col}" stroke="#fff" stroke-width="1.5"/>'
    return out


def monster_svg(name, state="normal"):
    sh = '<ellipse cx="100" cy="190" rx="60" ry="8" fill="#6b4c8a" opacity=".12"/>'
    brow = lambda cx, cy, gap=24: (
        f'<path d="M{cx-gap-9},{cy-17} L{cx-gap+7},{cy-12}" stroke="{INK}" stroke-width="3.2" stroke-linecap="round"/>'
        f'<path d="M{cx+gap+9},{cy-17} L{cx+gap-7},{cy-12}" stroke="{INK}" stroke-width="3.2" stroke-linecap="round"/>') if state == "normal" else ""
    face = lambda cx, cy, gap=24: blush(cx, cy + 14, gap + 17) + eyes(state, cx, cy, gap) + brow(cx, cy, gap) + mouth(state, cx, cy + 16)
    body = ""
    top = (state == "ko")
    if name == "slime":
        body = ('<path d="M28,150 C22,92 66,50 100,50 C134,50 178,92 172,150 C170,176 140,186 100,186 C60,186 30,176 28,150Z" fill="#a8e6ff" stroke="#6ec6ec" stroke-width="4" stroke-linejoin="round"/>'
                '<ellipse cx="68" cy="88" rx="16" ry="9" fill="#fff" opacity=".6" transform="rotate(-30 68 88)"/>'
                '<path d="M100,50 C96,36 108,30 106,20 C116,30 118,44 108,52Z" fill="#a8e6ff" stroke="#6ec6ec" stroke-width="3" stroke-linejoin="round"/>') + face(100, 128)
    elif name == "mushroom":
        body = ('<path d="M66,128 h68 v38 C134,184 66,184 66,166Z" fill="#fff3e0" stroke="#e8cfa8" stroke-width="4" stroke-linejoin="round"/>'
                '<path d="M16,126 C16,60 64,30 100,30 C136,30 184,60 184,126 C184,138 150,142 100,142 C50,142 16,138 16,126Z" fill="#ffb3c9" stroke="#f08aa8" stroke-width="4" stroke-linejoin="round"/>'
                '<circle cx="56" cy="88" r="12" fill="#fff"/><circle cx="108" cy="64" r="10" fill="#fff"/><circle cx="150" cy="96" r="13" fill="#fff"/><circle cx="92" cy="104" r="7" fill="#fff"/>') + face(100, 152, 20)
    elif name == "ghost":
        body = ('<path d="M38,176 L38,96 C38,54 68,32 100,32 C132,32 162,54 162,96 L162,176 C152,164 142,184 131,174 C120,164 110,184 100,174 C90,164 80,184 69,174 C58,164 48,184 38,176Z" fill="#f6f2ff" stroke="#cfc3ee" stroke-width="4" stroke-linejoin="round"/>'
                '<ellipse cx="30" cy="124" rx="12" ry="8" fill="#f6f2ff" stroke="#cfc3ee" stroke-width="3.5" transform="rotate(25 30 124)"/>'
                '<ellipse cx="170" cy="124" rx="12" ry="8" fill="#f6f2ff" stroke="#cfc3ee" stroke-width="3.5" transform="rotate(-25 170 124)"/>') + face(100, 100)
    elif name == "cupcake":
        body = ('<path d="M48,126 L152,126 L140,186 L60,186Z" fill="#ffd9a8" stroke="#eab97a" stroke-width="4" stroke-linejoin="round"/>'
                '<path d="M70,128 L74,184 M92,128 L94,186 M114,128 L114,186 M134,128 L130,184" stroke="#f3c48a" stroke-width="3" fill="none"/>'
                '<ellipse cx="100" cy="112" rx="64" ry="30" fill="#ffb7d5" stroke="#f08ab5" stroke-width="4"/>'
                '<ellipse cx="100" cy="82" rx="46" ry="24" fill="#ffc6df" stroke="#f08ab5" stroke-width="4"/>'
                '<ellipse cx="100" cy="58" rx="28" ry="17" fill="#ffd3e6" stroke="#f08ab5" stroke-width="4"/>'
                '<path d="M100,42 C98,30 104,22 112,18" stroke="#6bbf7a" stroke-width="4" fill="none" stroke-linecap="round"/>'
                '<circle cx="100" cy="40" r="10" fill="#ff6f8f" stroke="#e0476d" stroke-width="3"/>'
                '<rect x="66" y="76" width="8" height="3.5" rx="2" fill="#8ec5ff" transform="rotate(-30 70 78)"/><rect x="126" y="70" width="8" height="3.5" rx="2" fill="#ffe27a" transform="rotate(25 130 72)"/>'
                '<rect x="140" y="104" width="8" height="3.5" rx="2" fill="#b8f0c8" transform="rotate(-20 144 106)"/><rect x="50" y="108" width="8" height="3.5" rx="2" fill="#fff" transform="rotate(30 54 110)"/>') + face(100, 108, 26)
    elif name == "dragon":
        body = ('<path d="M150,160 C196,170 200,120 176,110 C180,136 166,146 150,146Z" fill="#c4a8ff" stroke="#9f80e6" stroke-width="4" stroke-linejoin="round"/>'
                '<path d="M60,100 C28,78 20,104 30,126 C42,120 52,112 60,100Z" fill="#ffc2dc" stroke="#f08ab5" stroke-width="3.5" stroke-linejoin="round"/>'
                '<path d="M140,100 C172,78 180,104 170,126 C158,120 148,112 140,100Z" fill="#ffc2dc" stroke="#f08ab5" stroke-width="3.5" stroke-linejoin="round"/>'
                '<ellipse cx="100" cy="124" rx="64" ry="58" fill="#d2baff" stroke="#9f80e6" stroke-width="4"/>'
                '<ellipse cx="100" cy="152" rx="36" ry="28" fill="#f3eaff"/>'
                '<path d="M64,78 L58,46 L84,66Z" fill="#ffe27a" stroke="#f0b93c" stroke-width="3" stroke-linejoin="round"/>'
                '<path d="M136,78 L142,46 L116,66Z" fill="#ffe27a" stroke="#f0b93c" stroke-width="3" stroke-linejoin="round"/>'
                '<path d="M88,68 l6,-12 l6,12 l6,-12 l6,12" fill="#ffc2dc" stroke="#f08ab5" stroke-width="2.5" stroke-linejoin="round"/>') + face(100, 112, 26)
    elif name == "king":
        body = ('<path d="M34,100 C20,140 22,176 40,186 L160,186 C178,176 180,140 166,100Z" fill="#ff9fc0" stroke="#e8709a" stroke-width="4" stroke-linejoin="round"/>'
                '<path d="M30,150 C26,92 66,56 100,56 C134,56 174,92 170,150 C168,178 140,188 100,188 C60,188 32,178 30,150Z" fill="#fffaf5" stroke="#e8d9cc" stroke-width="4" stroke-linejoin="round"/>'
                '<path d="M70,70 L66,30 L84,50 L100,22 L116,50 L134,30 L130,70Z" fill="#ffe27a" stroke="#f0b93c" stroke-width="4" stroke-linejoin="round"/>'
                '<circle cx="100" cy="38" r="5" fill="#ff7fa8"/><circle cx="72" cy="40" r="4" fill="#8ec5ff"/><circle cx="128" cy="40" r="4" fill="#8be0b0"/>'
                '<path d="M86,148 Q100,160 114,148" fill="none" stroke="#e8d9cc" stroke-width="3"/>') + face(100, 118, 26)
    extra = orbit_stars(100, 40) if top else ""
    return svg(200, 200, sh + body + extra)


MONSTERS = ["slime", "mushroom", "ghost", "cupcake", "dragon", "king"]


# ---------------------------------------------------------------- map
NODES = [(150, 590), (330, 400), (520, 600), (700, 360), (900, 560), (1040, 220)]


def map_svg():
    p = []
    p.append('<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#cfe8ff"/><stop offset=".55" stop-color="#f3e4ff"/><stop offset="1" stop-color="#ffe6f0"/></linearGradient>'
             '<linearGradient id="g1" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c9f2c7"/><stop offset="1" stop-color="#a6e3b4"/></linearGradient>'
             '<linearGradient id="g2" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#d8f7cf"/><stop offset="1" stop-color="#b9ecc2"/></linearGradient></defs>')
    p.append('<rect width="1200" height="800" fill="url(#sky)"/>')
    # รุ้ง
    for i, col in enumerate(["#ffb3c1", "#ffd6a5", "#fdffb6", "#caffbf", "#9bf6ff", "#bdb2ff"]):
        r = 330 - i * 16
        p.append(f'<path d="M{700-r},330 A{r},{r} 0 0 1 {700+r},330" fill="none" stroke="{col}" stroke-width="16" opacity=".55"/>')
    # ก้อนเมฆ
    for (x, y, s) in [(120, 110, 1.0), (520, 70, 0.8), (930, 120, 1.1), (320, 230, .7), (1110, 330, .8)]:
        p.append(f'<g transform="translate({x} {y}) scale({s})" fill="#fff" opacity=".92"><ellipse cx="0" cy="0" rx="60" ry="26"/><ellipse cx="-32" cy="-14" rx="34" ry="24"/><ellipse cx="22" cy="-22" rx="40" ry="30"/></g>')
    # เนินเขา
    p.append('<path d="M0,520 C150,440 300,470 440,520 C600,580 700,470 860,450 C1020,430 1120,480 1200,500 L1200,800 L0,800Z" fill="url(#g2)"/>')
    p.append('<path d="M0,640 C160,590 320,640 520,660 C720,680 900,600 1200,640 L1200,800 L0,800Z" fill="url(#g1)"/>')
    # ปราสาทปลายทาง
    p.append('<g transform="translate(1040 150)"><rect x="-70" y="10" width="140" height="80" rx="8" fill="#ffe4ef" stroke="#f3b6cf" stroke-width="4"/>'
             '<rect x="-84" y="-10" width="36" height="100" rx="6" fill="#ffd6e7" stroke="#f3b6cf" stroke-width="4"/><rect x="48" y="-10" width="36" height="100" rx="6" fill="#ffd6e7" stroke="#f3b6cf" stroke-width="4"/>'
             '<path d="M-90,-8 L-66,-50 L-42,-8Z M42,-8 L66,-50 L90,-8Z M-30,10 L0,-48 L30,10Z" fill="#c9b5ff" stroke="#a48ae6" stroke-width="4" stroke-linejoin="round"/>'
             '<path d="M-14,90 v-34 a14,14 0 0 1 28,0 v34Z" fill="#a48ae6"/></g>')
    # เส้นทาง
    d = "M150,590 C210,470 270,430 330,400 C420,420 450,610 520,600 C600,590 620,380 700,360 C780,350 820,560 900,560 C980,560 1010,330 1040,220"
    p.append(f'<path d="{d}" fill="none" stroke="#fff" stroke-width="30" stroke-linecap="round" opacity=".85"/>')
    p.append(f'<path d="{d}" fill="none" stroke="#ffb8d6" stroke-width="6" stroke-linecap="round" stroke-dasharray="2 18"/>')
    # ต้นไม้/ดอกไม้
    for (x, y, s) in [(40, 560, 1), (240, 680, .9), (420, 470, .8), (610, 700, 1.1), (800, 470, .9), (1000, 700, 1), (1150, 580, .9), (60, 360, .7)]:
        p.append(f'<g transform="translate({x} {y}) scale({s})"><rect x="-5" y="0" width="10" height="26" rx="4" fill="#d9b38c"/><circle cx="0" cy="-8" r="24" fill="#bff0c0" stroke="#8fd4a0" stroke-width="3"/><circle cx="-8" cy="-12" r="5" fill="#fff" opacity=".6"/><circle cx="10" cy="-4" r="4" fill="#ffc2d9"/><circle cx="-6" cy="4" r="4" fill="#ffe27a"/></g>')
    for (x, y) in [(90, 700), (360, 730), (560, 760), (760, 720), (960, 770), (1100, 690), (200, 500), (860, 640)]:
        p.append(f'<g transform="translate({x} {y})"><circle r="9" fill="#ffd1e8"/><circle r="4" fill="#ffe27a"/></g>')
    # ดาวลอย
    for (x, y, r) in [(250, 90, 10), (700, 150, 8), (1130, 230, 9), (60, 220, 8), (460, 330, 7)]:
        p.append(f'<polygon points="{star(x,y,r,r*.45)}" fill="#fff6b0" stroke="#ffe27a" stroke-width="2"/>')
    return svg(1200, 800, "".join(p))


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    for h in HEROES:
        for st in ("normal", "cheer", "tired"):
            write(os.path.join(ROOT, "heroes", f"{h}{'' if st == 'normal' else '_' + st}.svg"), hero_svg(h, st))
    for m in MONSTERS:
        for st in ("normal", "hurt", "ko"):
            write(os.path.join(ROOT, "monsters", f"{m}{'' if st == 'normal' else '_' + st}.svg"), monster_svg(m, st))
    write(os.path.join(ROOT, "map.svg"), map_svg())
    print("assets written to", os.path.abspath(ROOT))


if __name__ == "__main__":
    main()
