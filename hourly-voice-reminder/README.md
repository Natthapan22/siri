# hourly-voice-reminder

แจ้งเตือนด้วยเสียงทุกช่วงเวลาที่ตั้งไว้  
รองรับ **macOS** (`say`) และ **Windows** (SAPI / System.Speech)  
เครื่อง Windows ปลายทางใช้ไฟล์ `.exe` — **ไม่ต้องติดตั้ง Python**

---

## สำหรับ User / เครื่อง Windows ปลายทาง

1. ดาวน์โหลด `HourlyVoiceReminder.exe`
2. ดับเบิลคลิก
3. โปรแกรมเริ่มทำงาน

ไม่ต้องติดตั้ง Python / pip / อะไรเพิ่ม

- Log อยู่ที่ `logs/hourly-reminder.log` (สร้างอัตโนมัติข้างไฟล์ `.exe`)
- หยุดโปรแกรม: Task Manager → จบการทำงาน `HourlyVoiceReminder.exe`  
  หรือถ้าเปิดจากคอนโซลระหว่างพัฒนา: กด `Ctrl+C`

### เปิดตอน Windows startup (ทางเลือก)

1. วาง `HourlyVoiceReminder.exe` และ `install_startup.bat` ในโฟลเดอร์เดียวกัน  
   (หรือใช้ `.exe` ในโฟลเดอร์ `dist\` หลัง build)
2. ดับเบิลคลิก `install_startup.bat`
3. จะสร้าง shortcut ใน Startup — ครั้งถัดไปล็อกอินแล้วโปรแกรมเริ่มเอง

ยกเลิก: ลบ shortcut `HourlyVoiceReminder.lnk` จากโฟลเดอร์ Startup

---

## สำหรับ Developer / เครื่อง Build

### macOS (รันจากซอร์ส)

```bash
cd hourly-voice-reminder
python3 main.py
```

ใช้เสียงระบบผ่านคำสั่ง `say` (แนะนำเสียง Kanya)

### ตั้งค่าใน `main.py`

```python
REMINDER_MESSAGE = "..."
INTERVAL_SECONDS = 60 * 60
SPEAK_ON_START = False
```

### สร้าง Windows `.exe` (ต้องทำบนเครื่อง Windows ที่มี Python)

1. ติดตั้ง Python จาก https://www.python.org/downloads/  
   (ติ๊ก Add to PATH)
2. คัดลอกโฟลเดอร์โปรเจกต์ไปเครื่อง Windows
3. ดับเบิลคลิก `build_windows.bat`
4. ได้ไฟล์ที่:

```text
dist/HourlyVoiceReminder.exe
```

คำสั่งภายในเทียบเท่า:

```text
pyinstaller --onefile --noconsole --name HourlyVoiceReminder main.py
```

ใช้ `--noconsole` เพราะเป็นโปรแกรมพื้นหลัง + เขียน log ลงไฟล์ ไม่ต้องมีหน้าต่างดำ

### โครงสร้าง

```text
hourly-voice-reminder/
├── main.py                 # reminder loop
├── tts.py                  # speak() — macOS / Windows
├── build_windows.bat       # สร้าง .exe บนเครื่อง build
├── install_startup.bat     # ทางเลือก: เปิดตอน startup
├── requirements.txt
├── README.md
└── .gitignore
```

---

## ข้อจำกัด Windows Thai TTS

- ใช้เสียงของ Windows แบบ offline เท่านั้น (ไม่ใช้ cloud API)
- ถ้าเครื่องมีเสียงภาษาไทย โปรแกรมจะเลือกให้อัตโนมัติ
- ถ้าไม่มีเสียงไทย จะใช้เสียงเริ่มต้นของระบบ และเขียน warning ลง log  
  เพิ่มเสียงไทยได้ที่: Settings → Time & language → Speech

---

## หมายเหตุการทดสอบ

- โค้ด TTS / build script ถูกเตรียมให้พร้อม build บน Windows
- **Windows EXE ยังไม่ได้ถูก execute จริง ถ้ากำลังพัฒนาจาก macOS** — ต้องรัน `build_windows.bat` บน Windows แล้วทดลองดับเบิลคลิก `.exe` บนเครื่องนั้น
