"""ธีมเกม Kawaii: CSS + ตัวสร้าง HTML (HUD, การ์ดด่าน, การ์ดตัวละคร, ฉากต่อสู้, รางวัล)
ภาพทุกชิ้นอ่านจาก assets/ แล้วฝังเป็น data URI ในหน้าเว็บ -> ไม่มีลิงก์ภายนอก รูปจึงแสดงได้ทั้งบนเครื่องและ Streamlit Cloud"""
import base64
import os
from functools import lru_cache
from game_engine import MAX_STARS

import streamlit as st

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

SKY = {  # (บน, ล่าง, พื้น) ของฉากต่อสู้แต่ละมอนสเตอร์
    "slime": ("#cfeeff", "#e6f9ff", "#b8ecc5"), "mushroom": ("#ffe3ef", "#fff1f6", "#c9f0b8"),
    "ghost": ("#d8d4ff", "#efeaff", "#cfe3ff"), "cupcake": ("#ffe0c8", "#fff0e2", "#ffd1e3"),
    "dragon": ("#e4d4ff", "#f6ecff", "#cdeccb"), "king": ("#ffd6e8", "#fff0c9", "#e5d1ff"),
}


@lru_cache(maxsize=None)
def img_uri(rel: str) -> str:
    """อ่านไฟล์ภาพใน assets/ แล้วคืน data URI (ถ้าไฟล์หาย จะคืนภาพว่างโปร่งใสแทน ไม่ทำให้แอปล้ม)"""
    path = os.path.join(ASSETS, rel)
    try:
        with open(path, "rb") as f:
            return "data:image/svg+xml;base64," + base64.b64encode(f.read()).decode()
    except OSError:
        return ("data:image/svg+xml;base64," + base64.b64encode(
            b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"/>').decode())


def hero_img(avatar: str, state: str = "normal") -> str:
    return img_uri(f"heroes/{avatar}{'' if state == 'normal' else '_' + state}.svg")


def monster_img(name: str, state: str = "normal") -> str:
    return img_uri(f"monsters/{name}{'' if state == 'normal' else '_' + state}.svg")


def _h(s: str) -> str:
    """รวมเป็นบรรทัดเดียว กัน Markdown ตีความบรรทัดว่าง/ย่อหน้าเป็น code block"""
    return "".join(line.strip() for line in s.splitlines())


def html(s: str, target=None):
    (target or st).markdown(_h(s), unsafe_allow_html=True)


COIN = ('<svg class="ic" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="#ffd34d" stroke="#f0a91f" stroke-width="2"/>'
        '<circle cx="12" cy="12" r="6" fill="none" stroke="#f0a91f" stroke-width="1.6"/><path d="M12 8v8M10 10h3a1.5 1.5 0 010 3h-3" stroke="#f0a91f" stroke-width="1.4" fill="none"/></svg>')
STAR = ('<svg class="ic" viewBox="0 0 24 24"><polygon points="12,2 15,9 22,9.5 16.5,14 18.5,21 12,17 5.5,21 7.5,14 2,9.5 9,9" '
        'fill="#ffe27a" stroke="#f0b93c" stroke-width="1.6" stroke-linejoin="round"/></svg>')
STAR_OFF = STAR.replace("#ffe27a", "#eadff5").replace("#f0b93c", "#cdbfe0")
BOLT = ('<svg class="ic" viewBox="0 0 24 24"><path d="M13 2L4 14h6l-1 8 9-12h-6z" fill="#b79cff" stroke="#8a6fe0" stroke-width="1.6" stroke-linejoin="round"/></svg>')


def stars_html(n: int, total: int = 3) -> str:
    return "".join(STAR if i < n else STAR_OFF for i in range(total))


CSS = """
@import url('https://fonts.googleapis.com/css2?family=Mali:wght@400;600;700&display=swap');
:root{--ink:#4a3560;--pink:#ff9fc7;--pink-d:#f06fa6;--lav:#b79cff;--mint:#a8e6cf;--sky:#a8d8ff;--sun:#ffe27a;}
.stApp{background:linear-gradient(180deg,#e8f4ff 0%,#f5ebff 48%,#ffe9f3 100%);color:var(--ink);
  font-family:'Mali','Kanit','Sarabun','Noto Sans Thai',system-ui,sans-serif;}
.stApp [data-testid="stHeader"]{background:transparent;}
.block-container{max-width:1080px;padding-top:1.2rem;padding-bottom:3rem;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#fff0f7,#efe7ff);}
h1,h2,h3,h4{color:var(--ink)!important;font-family:'Mali','Kanit',system-ui,sans-serif!important;letter-spacing:0;}
.ic{width:1.15em;height:1.15em;vertical-align:-.2em;}
.pagehead{display:flex;align-items:center;gap:.8rem;margin:.2rem 0 .6rem;}
.pagehead img{width:64px;animation:bob 3s ease-in-out infinite;}
.pagehead h2{margin:0;font-size:clamp(1.3rem,4vw,2rem);}
.pagehead p{margin:0;color:#8a6fb0;font-weight:600;}

.stButton>button,.stDownloadButton>button{border-radius:999px;border:3px solid #fff;min-height:3rem;font-weight:700;
  background:linear-gradient(180deg,#fff,#ffeaf4);color:var(--ink);box-shadow:0 4px 0 #f2c2da,0 8px 16px rgba(180,120,200,.15);
  transition:transform .12s,box-shadow .12s;font-family:inherit;}
.stButton>button:hover,.stDownloadButton>button:hover{transform:translateY(-2px);border-color:#fff;color:var(--ink);}
.stButton>button:active{transform:translateY(3px);box-shadow:0 1px 0 #f2c2da;}
.stButton>button:disabled{opacity:.55;}
.stButton>button[kind="primary"],.stButton>button[data-testid="stBaseButton-primary"]{
  background:linear-gradient(180deg,#ffb7d6,#ff86b8);color:#fff;box-shadow:0 4px 0 #e0629b,0 8px 16px rgba(240,111,166,.3);}
.stButton>button[kind="primary"]:hover{color:#fff;}
[data-testid="stExpander"] details{background:rgba(255,255,255,.7);border:3px solid #fff;border-radius:22px;}
.stTabs [data-baseweb="tab"]{font-weight:700;}
[data-testid="stAlert"]{border-radius:18px;}
[data-testid="stDialog"] div[role="dialog"]{border-radius:28px;background:linear-gradient(180deg,#fff,#fff4fa);}
.stProgress>div>div>div>div{background:linear-gradient(90deg,#ffb3d9,#b79cff);}

.hud{display:flex;align-items:center;gap:.8rem;flex-wrap:wrap;background:rgba(255,255,255,.85);border:3px solid #fff;border-radius:26px;
  padding:.55rem .9rem;box-shadow:0 6px 18px rgba(170,120,210,.18);margin:.1rem 0 .9rem;}
.hud .av{width:58px;height:58px;border-radius:50%;background:linear-gradient(180deg,#ffe3f0,#e6dcff);border:3px solid #fff;overflow:hidden;flex:none;}
.hud .av img{width:100%;height:100%;object-fit:cover;object-position:50% 22%;transform:scale(1.5);transform-origin:50% 30%;}
.hud .lv{flex:1 1 180px;min-width:150px;}.hud .lv b{font-size:1.1rem;}
.xpbar{height:14px;border-radius:99px;background:#efe5fa;overflow:hidden;border:2px solid #fff;margin:.2rem 0;}
.xpbar>i{display:block;height:100%;background:linear-gradient(90deg,#ffb3d9,#b79cff);border-radius:99px;transition:width .8s ease;}
.hud small{color:#8a6fb0;}
.chip{display:inline-flex;align-items:center;gap:.35rem;background:#fff;border-radius:999px;padding:.35rem .8rem;font-weight:700;border:2px solid #f6e5ff;}

.worldbanner{position:relative;border-radius:30px;border:5px solid #fff;overflow:hidden;box-shadow:0 10px 28px rgba(160,110,200,.25);
  aspect-ratio:3/1;background-size:cover;background-position:center;margin-bottom:.9rem;container-type:inline-size;}
.worldbanner .tx{position:absolute;left:4%;top:12%;background:rgba(255,255,255,.88);border-radius:22px;padding:.4rem 1rem;max-width:62%;}
.worldbanner .tx b{display:block;font-size:clamp(13px,3.6cqw,26px);}
.worldbanner .tx span{font-size:clamp(10px,2.1cqw,15px);color:#8a6fb0;font-weight:600;}
.worldbanner .rider{position:absolute;right:8%;bottom:4%;width:15cqw;animation:bob 2.4s ease-in-out infinite;}
.worldbanner .rider.m{right:24%;width:13cqw;}

.stagecard{position:relative;background:rgba(255,255,255,.88);border:4px solid #fff;border-radius:26px;text-align:center;padding:.7rem .5rem .6rem;
  box-shadow:0 6px 16px rgba(170,120,210,.18);transition:transform .15s;margin-bottom:.4rem;}
.stagecard:hover{transform:translateY(-4px) rotate(-.6deg);}
.stagecard .no{position:absolute;top:.5rem;left:.6rem;width:2rem;height:2rem;border-radius:50%;background:linear-gradient(180deg,#ffb7d6,#ff86b8);color:#fff;font-weight:700;
  display:flex;align-items:center;justify-content:center;border:3px solid #fff;}
.stagecard img.mon{width:min(70%,130px);animation:bob 3.2s ease-in-out infinite;}
.stagecard .nm{font-weight:700;font-size:1.05rem;}.stagecard .tt{font-size:.82rem;color:#8a6fb0;}
.stagecard.locked img.mon{filter:grayscale(1) opacity(.5);animation:none;}
.stagecard.locked{background:rgba(240,235,250,.8);}
.stagecard.current{border-color:var(--pink);box-shadow:0 0 0 4px rgba(255,159,199,.35),0 6px 16px rgba(170,120,210,.18);}
.stagecard .tag{display:inline-block;margin-top:.2rem;background:#f3e9ff;border-radius:99px;padding:.1rem .7rem;font-size:.78rem;font-weight:700;}
.stagecard.cleared .tag{background:#dff7e8;}
.stagecard.current .tag{background:#ffe3ef;color:var(--pink-d);}

.hcard{background:rgba(255,255,255,.88);border:4px solid #fff;border-radius:26px;text-align:center;padding:.6rem .5rem .7rem;box-shadow:0 6px 16px rgba(170,120,210,.18);margin-bottom:.4rem;}
.hcard img{width:min(100%,120px);animation:bob 3.2s ease-in-out infinite;}
.hcard.sel{border-color:var(--pink);box-shadow:0 0 0 4px rgba(255,159,199,.35),0 6px 16px rgba(170,120,210,.18);}
.hcard.locked img{filter:grayscale(.85) opacity(.6);animation:none;}
.hcard .nm{font-weight:700;}.hcard .tg{font-size:.8rem;color:#8a6fb0;}.hcard .pk{font-size:.78rem;margin-top:.2rem;background:#f3e9ff;border-radius:14px;padding:.15rem .5rem;}

.scene{position:relative;container-type:inline-size;aspect-ratio:16/10;border-radius:30px;border:5px solid #fff;overflow:hidden;
  background:linear-gradient(180deg,var(--s1),var(--s2) 62%,var(--s3) 62.5%);box-shadow:0 10px 28px rgba(160,110,200,.25);}
.scene:before{content:"";position:absolute;inset:0;background:radial-gradient(ellipse 12% 8% at 18% 16%,#fff 60%,transparent 62%),
  radial-gradient(ellipse 16% 9% at 70% 22%,#fff 60%,transparent 62%),radial-gradient(ellipse 9% 6% at 44% 10%,#fff 60%,transparent 62%);opacity:.8;}
.scene .ground{position:absolute;left:0;right:0;bottom:0;height:38%;background:radial-gradient(ellipse 60% 45% at 25% 30%,rgba(255,255,255,.5),transparent),
  radial-gradient(ellipse 60% 45% at 78% 30%,rgba(255,255,255,.5),transparent);}
.actor{position:absolute;bottom:12%;width:25%;}.actor img{width:100%;display:block;}
.actor.hero{left:9%;}.actor.mon{right:9%;width:27%;}
.actor.hero img,.actor.mon img{animation:bob 3s ease-in-out infinite;}
.bars{position:absolute;top:3.5%;left:3%;right:3%;display:flex;justify-content:space-between;gap:3%;z-index:5;}
.bar{flex:1;max-width:46%;background:rgba(255,255,255,.9);border-radius:99px;padding:.18rem .6rem .22rem;border:3px solid #fff;}
.bar .t{display:flex;justify-content:space-between;font-weight:700;font-size:clamp(9px,2.1cqw,15px);}
.bar .tr{height:clamp(8px,1.8cqw,14px);background:#f0e6f8;border-radius:99px;overflow:hidden;}
.bar .tr i{display:block;height:100%;border-radius:99px;transition:width 1s ease .5s;}
.bar.me .tr i{background:linear-gradient(90deg,#ff8fb0,#ffc2d6);}
.bar.mn .tr i{background:linear-gradient(90deg,#8fe0b5,#c6f5a6);}
.bar.low .tr i{background:linear-gradient(90deg,#ff7a7a,#ffb199);}
.spell{position:absolute;left:26%;bottom:34%;width:7cqw;height:7cqw;border-radius:50%;z-index:7;opacity:0;
  background:radial-gradient(circle,#fff 0 25%,var(--spell) 26% 62%,transparent 64%);box-shadow:0 0 18px 8px var(--spell);animation:fly .75s ease-in forwards;}
.spell.fizz{animation:fizz .8s ease-out forwards;}
.burst{position:absolute;right:18%;bottom:38%;width:14cqw;height:14cqw;z-index:7;opacity:0;animation:burst .5s ease-out .72s forwards;
  background:radial-gradient(circle,#fff 0 18%,var(--spell) 19% 44%,transparent 46%);border-radius:50%;}
.floatnum{position:absolute;z-index:8;font-weight:700;font-size:clamp(18px,5.5cqw,44px);color:#fff;-webkit-text-stroke:2px var(--ink);paint-order:stroke fill;opacity:0;animation:rise 1.1s ease-out forwards;}
.floatnum.hit{right:24%;bottom:56%;animation-delay:.8s;color:#fff3a0;}
.floatnum.me{left:16%;bottom:56%;animation-delay:.9s;color:#ffd0d8;}
.floatnum.miss{left:28%;bottom:48%;animation-delay:.5s;color:#e8ddff;}
.atk .hero{animation:lunge .6s ease-out;}.atk .mon img{animation:hurt .6s ease-out .72s both;}
.fail .hero img{animation:hurt .5s ease-out 1s both;}.fail .mon{animation:lungeL .6s ease-in-out .6s;}
.ko .mon{animation:kofloat 2.4s ease-in-out infinite;bottom:16%;}.ko .mon img{animation:none;}
.ko .hero img{animation:jump 1s ease-in-out infinite;}
.lose .hero img{animation:none;transform:translateY(8%);}.lose .mon img{animation:jump 1s ease-in-out infinite;}
.flash{position:absolute;inset:0;background:#ff9db8;opacity:0;z-index:6;pointer-events:none;}.fail .flash{animation:flash .6s ease-out 1s;}
.banner{position:absolute;left:50%;top:44%;transform:translate(-50%,-50%);z-index:9;text-align:center;background:rgba(255,255,255,.93);border:4px solid #fff;
  border-radius:26px;padding:.5rem 1.3rem;box-shadow:0 8px 22px rgba(120,80,160,.25);animation:pop .6s cubic-bezier(.3,1.6,.5,1) .3s both;max-width:86%;}
.banner b{display:block;font-size:clamp(14px,4.2cqw,32px);}.banner span{font-size:clamp(10px,2.4cqw,18px);color:#8a6fb0;font-weight:600;}
.zzz{position:absolute;right:15%;top:22%;z-index:8;font-weight:700;color:#8a6fb0;font-size:clamp(14px,4cqw,32px);animation:zzz 2s ease-in-out infinite;}
.conf{position:absolute;top:-6%;width:2.2cqw;height:3.4cqw;border-radius:3px;z-index:8;opacity:0;animation:conf 2.6s linear infinite;}

.qcard{background:#fff;border:4px solid #fff;border-radius:24px;padding:.9rem 1.1rem;margin:.7rem 0;box-shadow:0 6px 16px rgba(170,120,210,.15);}
.qcard .lb{font-size:.75rem;font-weight:700;letter-spacing:1px;color:#b79cff;}.qcard .q{font-size:clamp(1.05rem,2.6vw,1.35rem);font-weight:700;margin-top:.2rem;}
.combo{display:inline-flex;gap:.4rem;align-items:center;background:linear-gradient(90deg,#ffe3a3,#ffc2d9);border-radius:99px;padding:.15rem .8rem;font-weight:700;}
.rewards{display:flex;flex-wrap:wrap;gap:.7rem;justify-content:center;margin:.6rem 0;}
.rcard{background:#fff;border:4px solid #fff;border-radius:24px;padding:.7rem 1.1rem;text-align:center;min-width:120px;box-shadow:0 6px 16px rgba(170,120,210,.2);animation:pop2 .6s cubic-bezier(.3,1.6,.5,1) both;}
.rcard:nth-child(2){animation-delay:.15s}.rcard:nth-child(3){animation-delay:.3s}.rcard:nth-child(4){animation-delay:.45s}
.rcard .big{font-size:1.8rem;font-weight:700;display:block;}.rcard .ic{width:1.5rem;height:1.5rem;}
.glass{background:rgba(255,255,255,.8);border:4px solid #fff;border-radius:26px;padding:.8rem 1.1rem;box-shadow:0 6px 18px rgba(170,120,210,.15);margin:.4rem 0;}
.dlg-mon{display:block;margin:0 auto;width:min(60%,200px);animation:bob 3s ease-in-out infinite;}
.tagrow{display:flex;flex-wrap:wrap;gap:.4rem;margin:.4rem 0;justify-content:center;}
.tagrow .tg2{background:#f3e9ff;border-radius:99px;padding:.15rem .7rem;font-size:.85rem;font-weight:700;}
.reviewbox{background:#fff;border-left:8px solid #ff9fc7;border-radius:18px;padding:.6rem .9rem;margin:.4rem 0;}
.reviewbox.ok{border-left-color:#8fe0b5;}
.empty{text-align:center;padding:1rem;}.empty img{width:120px;animation:bob 2.6s ease-in-out infinite;}

@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-4%)}}
@keyframes fly{0%{opacity:1;transform:translate(0,0) scale(.6)}100%{opacity:1;transform:translate(46cqw,-4cqw) scale(1.1)}}
@keyframes fizz{0%{opacity:1;transform:translate(0,0) scale(.6)}60%{opacity:1;transform:translate(22cqw,-6cqw) scale(1)}100%{opacity:0;transform:translate(26cqw,6cqw) scale(.2)}}
@keyframes burst{0%{opacity:1;transform:scale(.3)}100%{opacity:0;transform:scale(1.7)}}
@keyframes rise{0%{opacity:0;transform:translateY(0) scale(.6)}20%{opacity:1;transform:translateY(-6%) scale(1.15)}100%{opacity:0;transform:translateY(-70%) scale(1)}}
@keyframes lunge{0%{transform:translateX(0)}35%{transform:translateX(7cqw)}100%{transform:translateX(0)}}
@keyframes lungeL{0%{transform:translateX(0)}45%{transform:translateX(-30cqw)}100%{transform:translateX(0)}}
@keyframes hurt{0%{transform:translateX(0)}15%{transform:translateX(-5%) rotate(-4deg);filter:brightness(1.5)}30%{transform:translateX(5%) rotate(4deg)}45%{transform:translateX(-4%)}60%{transform:translateX(3%)}100%{transform:translateX(0);filter:none}}
@keyframes flash{0%{opacity:.55}100%{opacity:0}}
@keyframes pop{0%{opacity:0;transform:translate(-50%,-50%) scale(.3)}100%{opacity:1;transform:translate(-50%,-50%) scale(1)}}
@keyframes pop2{0%{opacity:0;transform:scale(.3)}100%{opacity:1;transform:scale(1)}}
@keyframes kofloat{0%,100%{transform:translateY(0) rotate(-3deg)}50%{transform:translateY(-8%) rotate(3deg)}}
@keyframes jump{0%,100%{transform:translateY(0)}50%{transform:translateY(-10%)}}
@keyframes zzz{0%{opacity:0;transform:translateY(10px)}50%{opacity:1}100%{opacity:0;transform:translateY(-16px)}}
@keyframes conf{0%{opacity:1;transform:translateY(0) rotate(0)}100%{opacity:.9;transform:translateY(70cqw) rotate(540deg)}}
@media (prefers-reduced-motion:reduce){*{animation-duration:.01ms!important;animation-iteration-count:1!important;transition:none!important}}
@media (max-width:640px){.block-container{padding-left:.7rem;padding-right:.7rem}.hud .av{width:46px;height:46px}.worldbanner{aspect-ratio:2/1}}
"""


def inject_css():
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def page_head(title: str, sub: str, hero: str = "bunny", state: str = "normal"):
    html(f'<div class="pagehead"><img src="{hero_img(hero, state)}" alt=""><div><h2>{title}</h2><p>{sub}</p></div></div>')


def hud(user: dict, avatars: dict):
    pct = int(user["xp"] / max(1, user["max_xp"]) * 100)
    sel = user["selected_avatar"]
    html(f"""
    <div class="hud">
      <div class="av"><img src="{hero_img(sel)}" alt=""></div>
      <div class="lv"><b>Lv.{user['level']}</b> · {avatars[sel]['name']}
        <div class="xpbar"><i style="width:{pct}%"></i></div><small>XP {user['xp']}/{user['max_xp']}</small></div>
      <span class="chip">{COIN} {user['coins']}</span>
      <span class="chip">{STAR} {user["stars"]}/{MAX_STARS}</span>
    </div>""")


def world_banner(avatar: str, quiz_title: str):
    sub = f"บทเรียนที่เลือก: {quiz_title}" if quiz_title else "เลือกบทเรียนแล้วท้าประลองมอนสเตอร์ทีละด่าน"
    html(f"""
    <div class="worldbanner" style="background-image:url('{img_uri('map.svg')}')">
      <div class="tx"><b>แดนขนมเวทมนตร์</b><span>{sub}</span></div>
      <img class="rider m" src="{monster_img('slime')}" alt="">
      <img class="rider" src="{hero_img(avatar, 'cheer')}" alt="">
    </div>""")


def stage_card(sid: int, m: dict, state: str, stars: int) -> str:
    """state: locked | open | current | cleared"""
    img = monster_img(m["img"], "ko" if state == "cleared" else "normal")
    tag = {"locked": "🔒 ยังล็อก", "open": "พร้อมท้าประลอง", "current": "ด่านถัดไป!", "cleared": "ผ่านแล้ว"}[state]
    st_html = f'<div>{stars_html(stars)}</div>' if state != "locked" else ""
    return _h(f"""
    <div class="stagecard {state}"><div class="no">{sid}</div>
      <img class="mon" src="{img}" alt="{m['name']}">
      <div class="nm">{m['name']}</div><div class="tt">{m['place']}</div>{st_html}<span class="tag">{tag}</span></div>""")


def hero_card(aid: str, a: dict, owned: bool, selected: bool) -> str:
    cls = ("sel " if selected else "") + ("" if owned else "locked ")
    return _h(f"""
    <div class="hcard {cls}"><img src="{hero_img(aid)}" alt="{a['name']}">
      <div class="nm">{a['name']}</div><div class="tg">{a['class']}</div>
      <div class="tg">เวท: {a['skill']}</div><div class="pk">{a['perk']}</div></div>""")


_CONF = ["#ff9fc7", "#ffe27a", "#a8d8ff", "#b79cff", "#a8e6cf"]


def confetti(n: int = 16) -> str:
    return "".join(f'<i class="conf" style="left:{(i * 53) % 96}%;background:{_CONF[i % 5]};animation-delay:{(i % 7) * .25:.2f}s"></i>'
                   for i in range(n))


def battle_scene(b: dict, monster: dict, avatar_id: str, avatar: dict) -> str:
    """b: สถานะการต่อสู้ (monster_hp, player_hp, last, done)"""
    s1, s2, s3 = SKY[monster["img"]]
    last, done = b.get("last"), b.get("done")
    mode, hs, ms, fx, banner = "", "normal", "normal", "", ""
    if done == "win":
        mode, hs, ms = "ko", "cheer", "ko"
        fx = confetti() + '<div class="zzz">Z z z</div>'
        banner = f'<div class="banner"><b>ผนึกเวทสำเร็จ!</b><span>{monster["name"]}ง่วงนอนแล้ว หลับฝันดีไปเลย</span></div>'
    elif done == "lose":
        mode, hs = "lose", "tired"
        banner = '<div class="banner"><b>พลังหมดแล้ว…</b><span>พักก่อนนะ แล้วลองใหม่ได้เสมอ!</span></div>'
    elif last and last["ok"]:
        mode, hs, ms = "atk", "cheer", "hurt"
        fx = f'<div class="spell"></div><div class="burst"></div><div class="floatnum hit">-{last["dmg"]}</div>'
    elif last:
        mode = "fail"
        fx = (f'<div class="spell fizz"></div><div class="floatnum miss">พลาด!</div>'
              f'<div class="floatnum me">-{last["dmg"]}</div><div class="flash"></div>')
    hp_p, hp_m, mx = b["player_hp"], b["monster_hp"], b["monster_max"]
    pm = int(hp_m / mx * 100)
    return _h(f"""
    <div class="scene {mode}" style="--s1:{s1};--s2:{s2};--s3:{s3};--spell:{avatar['color']}">
      <div class="bars">
        <div class="bar me {'low' if hp_p <= 40 else ''}"><div class="t"><span>{avatar['name']}</span><span>{hp_p}/100</span></div><div class="tr"><i style="width:{hp_p}%"></i></div></div>
        <div class="bar mn"><div class="t"><span>{monster['name']}</span><span>{hp_m}/{mx}</span></div><div class="tr"><i style="width:{pm}%"></i></div></div>
      </div>
      <div class="ground"></div>
      <div class="actor hero"><img src="{hero_img(avatar_id, hs)}" alt="{avatar['name']}"></div>
      <div class="actor mon"><img src="{monster_img(monster['img'], ms)}" alt="{monster['name']}"></div>
      {fx}{banner}
    </div>""")


def rewards_html(xp: int, coins: int, stars: int | None = None, level: int | None = None) -> str:
    cards = [f'<div class="rcard"><span class="big">+{xp}</span>XP</div>',
             f'<div class="rcard"><span class="big">{COIN} +{coins}</span>เหรียญ</div>']
    if stars is not None:
        cards.append(f'<div class="rcard"><span class="big">{stars_html(stars)}</span>ดาวรอบนี้</div>')
    if level:
        cards.append(f'<div class="rcard"><span class="big">Lv.{level}</span>เลเวลอัป!</div>')
    return _h('<div class="rewards">' + "".join(cards) + "</div>")
