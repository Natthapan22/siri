@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM 1) มี .exe แล้ว → เปิดเลย (เครื่องไม่มี Python ก็ได้)
if exist "HourlyVoiceReminder.exe" (
  start "" "HourlyVoiceReminder.exe"
  exit /b 0
)
if exist "dist\HourlyVoiceReminder.exe" (
  start "" "dist\HourlyVoiceReminder.exe"
  exit /b 0
)

REM 2) มี Python → รันทันที
where py >nul 2>&1 && (
  echo เริ่มโปรแกรม ^(กด Ctrl+C เพื่อหยุด^)
  py -3 main.py
  exit /b %ERRORLEVEL%
)
where python >nul 2>&1 && (
  echo เริ่มโปรแกรม ^(กด Ctrl+C เพื่อหยุด^)
  python main.py
  exit /b %ERRORLEVEL%
)

REM 3) ไม่มีทั้ง exe และ Python
echo.
echo ยังไม่มี HourlyVoiceReminder.exe และยังไม่มี Python
echo.
echo ทำอย่างใดอย่างหนึ่ง:
echo   ก. ได้ไฟล์ HourlyVoiceReminder.exe มาแล้ว → วางในโฟลเดอร์นี้ แล้วดับเบิลคลิก เปิดแอป.bat อีกครั้ง
echo   ข. เครื่องนี้มีเน็ตและจะสร้างเอง → ติดตั้ง Python จาก python.org ^(ติ๊ก Add to PATH^)
echo      แล้วดับเบิลคลิก สร้าง.exe.bat จากนั้นกด เปิดแอป.bat อีกครั้ง
echo.
pause
exit /b 1
