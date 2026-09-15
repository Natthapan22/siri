@echo off
chcp 65001 >nul
cd /d "%~dp0"

where powershell >nul 2>&1
if errorlevel 1 (
  echo ไม่พบ PowerShell
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launch-windows.ps1"
set ERR=%ERRORLEVEL%
if not "%ERR%"=="0" (
  echo.
  echo เปิดไม่สำเร็จ รหัส error: %ERR%
  if exist "%~dp0launch-error.txt" (
    echo ---- launch-error.txt ----
    type "%~dp0launch-error.txt"
    echo --------------------------
  )
  echo.
  echo ลองกด OpenApp.bat อีกครั้ง หรือส่งข้อความ error ด้านบนมาให้ช่วยดู
  pause
  exit /b %ERR%
)
