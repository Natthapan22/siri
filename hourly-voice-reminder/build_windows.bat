@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo === Hourly Voice Reminder — Windows build ===
echo หมายเหตุ: สคริปต์นี้รันบนเครื่อง BUILD เท่านั้น (ต้องมี Python)
echo เครื่องปลายทางไม่ต้องมี Python — ใช้ไฟล์ .exe ที่ได้
echo.

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  set "PY=py -3"
) else (
  where python >nul 2>&1
  if %ERRORLEVEL%==0 (
    set "PY=python"
  ) else (
    echo [ERROR] ไม่พบ Python บนเครื่อง build
    echo ติดตั้งจาก https://www.python.org/downloads/
    echo ติ๊ก "Add python.exe to PATH" และ Tcl/tk
    echo จากนั้นรัน build_windows.bat อีกครั้ง
    pause
    exit /b 1
  )
)

echo [1/5] Python:
%PY% --version
if errorlevel 1 (
  echo [ERROR] เรียก Python ไม่สำเร็จ
  pause
  exit /b 1
)

echo [2/5] สร้าง virtual environment .venv ...
if not exist ".venv\Scripts\python.exe" (
  %PY% -m venv .venv
  if errorlevel 1 (
    echo [ERROR] สร้าง venv ไม่สำเร็จ
    pause
    exit /b 1
  )
)

set "VPY=.venv\Scripts\python.exe"
set "VPIP=.venv\Scripts\pip.exe"

echo [3/5] ติดตั้ง PyInstaller ...
"%VPIP%" install --upgrade pip pyinstaller
if errorlevel 1 (
  echo [ERROR] ติดตั้ง PyInstaller ไม่สำเร็จ
  pause
  exit /b 1
)

echo [4/5] Build HourlyVoiceReminder.exe ...
REM --noconsole: ไม่เปิดหน้าต่างดำ (เหมาะกับ background reminder)
REM log เขียนที่ logs\hourly-reminder.log ข้างไฟล์ .exe
"%VPY%" -m PyInstaller --noconfirm --clean --onefile --noconsole --name HourlyVoiceReminder main.py
if errorlevel 1 (
  echo [ERROR] PyInstaller build ล้มเหลว
  pause
  exit /b 1
)

echo [5/5] เสร็จแล้ว
echo.
echo ไฟล์ exe:
echo   %cd%\dist\HourlyVoiceReminder.exe
echo.
echo นำไปเครื่อง Windows ปลายทาง: คัดลอกแค่ HourlyVoiceReminder.exe
echo ดับเบิลคลิกเพื่อรัน — ไม่ต้องติดตั้ง Python
echo (ถ้าต้องการเปิดตอน开机: รัน install_startup.bat หลังวางไฟล์ exe แล้ว)
echo.
pause
endlocal
