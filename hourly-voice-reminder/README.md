# Hourly Voice Reminder

แอปแจ้งเตือนด้วยเสียงตามชั่วโมงที่เลือก — **ดับเบิลคลิกแล้วใช้ได้** ไม่ต้องติดตั้ง Python

## คนใช้ (แนะนำ)

โหลดจาก **GitHub Releases**:  
https://github.com/Natthapan22/siri/releases

| เครื่อง | ไฟล์ |
|---------|------|
| **Windows** | `HourlyVoiceReminder.exe` → ดับเบิลคลิก |
| **Mac** | `HourlyVoiceReminder-macOS.zip` → แตกไฟล์ → ดับเบิลคลิก `HourlyVoiceReminder.app` |

ครั้งแรกบน Mac ถ้าบล็อก: คลิกขวา → Open → Open

### ในหน้าต่าง
- กรอกข้อความ + **เทสเสียง**
- ติ๊กชั่วโมง 00–23 (เริ่มต้นติ๊กครบ)
- **เริ่ม** / **หยุด**
- บันทึกอัตโนมัติข้างไฟล์แอป (`config.json`)

---

## นักพัฒนา — สร้างแอปเอง

โค้ดชุดเดียว `main.py` (UI เหมือนกันทั้ง Mac / Windows)

```bash
# Mac
cd hourly-voice-reminder
./build_mac.sh
# ได้ dist/HourlyVoiceReminder.app

# Windows
build_windows.bat
# ได้ dist\HourlyVoiceReminder.exe
```

หรือ push tag `v1.0.0` ขึ้น GitHub → Actions จะ build ทั้งสองระบบให้อัตโนมัติ

```bash
git tag v1.0.0
git push origin v1.0.0
```
