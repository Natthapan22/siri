@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"
title Hourly Voice Reminder

REM ============================================================
REM  คลิกเดียวจบ — ขั้นตอนอัตโนมัติ:
REM    1) ตรวจ Python 3.12 + tkinter (สำหรับหน้า UI)
REM    2) ถ้าไม่มี → ดาวน์โหลด + ติดตั้ง Python 3.12.7
REM    3) เปิดหน้าต่าง UI (เหมือน Mac)
REM
REM  คำสั่งติดตั้ง Python (รันอัตโนมัติใน run.ps1):
REM    URL:  https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe
REM    ติดตั้ง: python-3.12.7-amd64.exe /quiet InstallAllUsers=0 PrependPath=1 Include_tcltk=1 Include_pip=1
REM ============================================================

if not exist "main.py" (
  echo [ERROR] ไม่พบ main.py — ต้องคัดลอกทั้งโฟลเดอร์ hourly-voice-reminder
  pause
  exit /b 1
)

REM รัน flow ทั้งหมดผ่าน PowerShell (ติดตั้ง Python + เปิด UI)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1"
set "ERR=%ERRORLEVEL%"
if not "%ERR%"=="0" (
  echo.
  echo เปิดไม่สำเร็จ — ดู logs\launch.log
  if exist "logs\launch.log" type "logs\launch.log"
  pause
  exit /b %ERR%
)
exit /b 0
