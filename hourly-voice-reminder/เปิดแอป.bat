@echo off
cd /d "%~dp0"
REM เปิดแบบเงียบ ไม่ค้างที่ Press any key — error โชว์เป็น MessageBox จาก run.ps1
start "" /min powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0run.ps1"
exit
