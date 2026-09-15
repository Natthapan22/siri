# Hourly Voice Reminder

แจ้งเตือนด้วยเสียงตามชั่วโมง — **คลิกเดียวจบ**

| เครื่อง | กดไฟล์นี้ |
|---------|-----------|
| **Mac** | **`เปิดแอป.command`** |
| **Windows** | **`เปิดแอป.bat`** |

### Windows — ในไฟล์ `.bat` มีคำสั่งติดตั้ง Python อยู่แล้ว

```bat
curl -L -o "%TEMP%\python-3.12.7-amd64.exe" https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe

"%TEMP%\python-3.12.7-amd64.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_tcltk=1 Include_pip=1 Include_launcher=1 AssociateFiles=0 Shortcuts=0
```

Flow: ตรวจ Python → ไม่มีก็ติดตั้ง 3.12.7 → เปิดหน้า UI

### ในหน้า UI
- กรอกข้อความ + **เทสเสียง**
- ติ๊กชั่วโมง 00–23 (เริ่มต้นติ๊กครบ)
- **เริ่ม** / **หยุด**

Log: `logs/`
