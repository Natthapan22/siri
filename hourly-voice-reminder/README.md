# Hourly Voice Reminder

แจ้งเตือนด้วยเสียงทุก 1 ชั่วโมง — **กดไฟล์เดียวจบ**

| เครื่อง | กดไฟล์นี้ |
|---------|-----------|
| **Mac** | **`เปิดแอป.command`** |
| **Windows** | **`เปิดแอป.bat`** |

หยุด: Mac / หน้าต่างดำ → `Ctrl+C` · Windows ถ้าเป็น `.exe` → Task Manager จบงาน

---

## Windows ที่ไม่มี Python

1. บนเครื่องที่มี Python: กด **`สร้าง.exe.bat`** ครั้งเดียว  
2. ได้ไฟล์ **`HourlyVoiceReminder.exe`**  
3. เอาแค่ `.exe` (หรือทั้งโฟลเดอร์แล้วกด `เปิดแอป.bat`) ไปเครื่องอื่น → ดับเบิลคลิก

---

## เปลี่ยนข้อความ

แก้ใน `main.py` บรรทัด `REMINDER_MESSAGE` / `INTERVAL_SECONDS` แล้วบันทึก  
(ถ้าใช้ `.exe` ต้องกด `สร้าง.exe.bat` ใหม่)

Log: โฟลเดอร์ `logs/hourly-reminder.log`
