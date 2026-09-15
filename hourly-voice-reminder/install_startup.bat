@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo === ติดตั้งให้เปิดตอน Windows startup (ทางเลือก) ===
echo.

set "EXE=%~dp0dist\HourlyVoiceReminder.exe"
if not exist "%EXE%" set "EXE=%~dp0HourlyVoiceReminder.exe"

if not exist "%EXE%" (
  echo [ERROR] ไม่พบ HourlyVoiceReminder.exe
  echo วางไฟล์ .exe ไว้ในโฟลเดอร์นี้ หรือ build ด้วย build_windows.bat ก่อน
  echo คาดหวังที่:
  echo   %~dp0dist\HourlyVoiceReminder.exe
  echo   หรือ %~dp0HourlyVoiceReminder.exe
  pause
  exit /b 1
)

set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "LINK=%STARTUP%\HourlyVoiceReminder.lnk"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $sc = $ws.CreateShortcut('%LINK%'); ^
   $sc.TargetPath = '%EXE%'; ^
   $sc.WorkingDirectory = [System.IO.Path]::GetDirectoryName('%EXE%'); ^
   $sc.WindowStyle = 7; ^
   $sc.Description = 'Hourly Voice Reminder'; ^
   $sc.Save()"

if errorlevel 1 (
  echo [ERROR] สร้าง shortcut ไม่สำเร็จ
  pause
  exit /b 1
)

echo สร้าง shortcut แล้ว:
echo   %LINK%
echo ชี้ไปที่:
echo   %EXE%
echo.
echo ครั้งถัดไปที่ล็อกอิน Windows โปรแกรมจะเริ่มเอง
echo ถ้าต้องการยกเลิก: ลบไฟล์ shortcut ในโฟลเดอร์ Startup
echo.
pause
endlocal
