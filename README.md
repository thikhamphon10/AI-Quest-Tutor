# 🎮 AI Quest Tutor
**Learn. Play. Level Up.**

เว็บแอป Gamification + AI สำหรับทบทวนบทเรียน: อัปโหลด PDF / วางโน้ต → Gemini สร้างคำถาม → เล่น Battle Quest ⚔️ / Speed Run ⚡ → วิเคราะห์จุดอ่อน → Weakness Training 🔥

## ติดตั้ง
```bash
pip install -r requirements.txt
```

## ใส่ Gemini API Key
ขอ key ที่ https://aistudio.google.com/apikey แล้วตั้งเป็น environment variable (ห้าม hard-code ลงโค้ด)

```bash
export GEMINI_API_KEY="your_api_key_here"      # macOS / Linux
```
ไฟล์ `.env.example` เป็นแค่ตัวอย่างชื่อตัวแปร

## Run
```bash
streamlit run app.py
```

## Deploy บน Replit
1. สร้าง Repl ใหม่ (Python) แล้วอัปโหลดไฟล์ทั้งหมดในโฟลเดอร์นี้ (เก็บโครงสร้าง `games/` ไว้)
2. เปิด **Secrets** (🔒) เพิ่ม `GEMINI_API_KEY` = key ของคุณ
3. ใน Shell: `pip install -r requirements.txt`
4. ตั้งค่า Run command เป็น (ไฟล์ `.replit`):
   ```
   run = "streamlit run app.py --server.port 8080 --server.address 0.0.0.0"
   ```
5. กด **Run** แล้วเปิดผ่าน Webview หรือกด Deploy

## โครงสร้าง
```
app.py            UI + สลับหน้า (entry point)
ai_engine.py      Gemini service (ใช้ร่วมทั้ง 3 เกม)
pdf_processor.py  อ่าน PDF ด้วย PyPDF
game_engine.py    Session State, History, Weakness Logic
utils.py          ตัวช่วยแสดงผล
games/            battle.py, speed_run.py, weakness.py
```


## ภาพตัวละคร / มอนสเตอร์ (แก้ปัญหารูปไม่แสดง)

ภาพทั้งหมดเป็นไฟล์ SVG ในโฟลเดอร์ `assets/` (กระต่าย แมว หมี จิ้งจอก + มอนสเตอร์ 6 ตัว + แผนที่) แอปอ่านไฟล์แล้วฝังลงหน้าเว็บเป็น data URI
**ไม่มีลิงก์รูปภายนอกเลย** จึงแสดงได้ทั้งบนเครื่องและ Streamlit Cloud (ต้อง commit โฟลเดอร์ `assets/` ขึ้น GitHub ด้วย)
แก้สี/รูปทรงได้ที่ `tools/make_assets.py` แล้วรัน `python tools/make_assets.py`

## ระบบเกม
- แผนที่ 6 ด่าน: คลิกการ์ดมอนสเตอร์เพื่อดูรายละเอียดแล้วเริ่มภารกิจ (ด่านสุดท้ายต้องมีดาวครบตามเงื่อนไข)
- ต่อสู้: ตอบถูก = ตัวละครร่ายเวทโจมตี ลด HP มอนสเตอร์ / ตอบผิด = เวทพลาดและเสียพลัง พร้อมคำอธิบาย
- รางวัล: XP, เหรียญ, ดาว (1-3 ตามความแม่นยำ), เลเวล, ปลดล็อกด่านถัดไปและตัวละครใหม่ (ใช้เหรียญ)
- สรุปหลังจบด่าน: หัวข้อที่ควรทบทวน + เฉลยทุกข้อ
- บันทึกอัตโนมัติ: เก็บไว้ที่ `saves/<id>.json` โดย id อยู่ใน URL (`?p=...`) รีเฟรชแล้วยังอยู่
  (Streamlit Cloud อาจล้างไฟล์เมื่อรีสตาร์ท จึงมีปุ่มดาวน์โหลด/กู้คืนไฟล์เซฟในเมนูด้านข้าง)
- คลังข้อสอบ: ชุดที่สร้างแล้วเก็บใน `saved_quizzes/` เล่นซ้ำได้โดยไม่ใช้โควตา API

## โครงสร้าง (เพิ่มเติม)
```
visuals.py        ธีม CSS + ตัวสร้าง HTML (HUD, การ์ดด่าน, ฉากต่อสู้, รางวัล)
storage.py        บันทึก/โหลดไฟล์เซฟ
assets/           ภาพ SVG ตัวละคร มอนสเตอร์ แผนที่
tools/            สคริปต์สร้างภาพ
tests/            ชุดทดสอบ (pytest)
```
