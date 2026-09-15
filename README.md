# Hourly Voice Reminder

แอปแจ้งเตือนรายชั่วโมง พูดภาษาไทยด้วยเสียง **Microsoft Premwadee** (ผู้หญิง)

## วิธีใช้ (เครื่องใหม่)

1. ดาวน์โหลด `HourlyVoiceReminder.exe`
2. ดับเบิลคลิกเปิดเลย — **ไม่ต้องติดตั้งเสียง Windows / ไม่ต้องรันสคริปต์**
3. กด **เทสเสียง** แล้วกด **เริ่ม**

ต้องมีอินเทอร์เน็ตตอนพูดเสียง (ใช้ Edge online TTS)

## ไฟล์

| ไฟล์ | ความหมาย |
|------|----------|
| `HourlyVoiceReminder.exe` | ตัวแอป |
| `config.json` | ข้อความ + ชั่วโมงที่เลือก (สร้างอัตโนมัติหลังใช้งาน) |

## สร้าง exe เอง

```powershell
pip install edge-tts pyinstaller
pyinstaller --noconfirm --onefile --windowed --name HourlyVoiceReminder hourly_voice_reminder.py
```
