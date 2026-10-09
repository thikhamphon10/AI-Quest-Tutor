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


## Character rendering

ตัวละครและมอนสเตอร์ใช้ Emoji + CSS ภายใน Streamlit ไม่ต้องโหลดรูปจาก URL ภายนอกและไม่ต้องมีโฟลเดอร์ assets จึงลดปัญหารูปไม่แสดงบน Streamlit Cloud
