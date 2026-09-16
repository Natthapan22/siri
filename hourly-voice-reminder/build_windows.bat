@echo off
REM Build HourlyVoiceReminder.exe on Windows (developer machine only)
chcp 65001 >nul
cd /d "%~dp0"
python -m pip install -q --upgrade pip pyinstaller -r requirements.txt
python scripts/download_voice.py
python -m PyInstaller --noconfirm --clean HourlyVoiceReminder.spec
echo.
echo สร้างแล้ว: dist\HourlyVoiceReminder.exe
echo ดับเบิลคลิกเพื่อเปิด — ไม่ต้องมี Python
pause
