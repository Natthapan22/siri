@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo สร้าง HourlyVoiceReminder.exe (ครั้งเดียว บนเครื่องที่มี Python)
echo.

where py >nul 2>&1 && set "PY=py -3" || set "PY="
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY (
  echo ไม่พบ Python — ติดตั้งจาก https://www.python.org/downloads/ ติ๊ก Add to PATH
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" %PY% -m venv .venv
".venv\Scripts\pip.exe" install -q --upgrade pip pyinstaller
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --noconsole --name HourlyVoiceReminder main.py
if errorlevel 1 (
  echo สร้างไม่สำเร็จ
  pause
  exit /b 1
)

copy /Y "dist\HourlyVoiceReminder.exe" "HourlyVoiceReminder.exe" >nul
echo.
echo เสร็จแล้ว: HourlyVoiceReminder.exe
echo จากนี้ดับเบิลคลิก "เปิดแอป.bat" ได้เลย — เอาไฟล์ .exe ไปเครื่องอื่นที่ไม่มี Python ก็ได้
echo.
pause
