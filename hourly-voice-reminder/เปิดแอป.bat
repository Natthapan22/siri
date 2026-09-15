@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title Hourly Voice Reminder

REM ============================================================
REM  คำสั่งติดตั้ง Python 3.12.7 (รันอัตโนมัติถ้ายังไม่มี)
REM
REM  ดาวน์โหลด:
REM    curl -L -o "%TEMP%\python-3.12.7-amd64.exe" ^
REM      https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe
REM
REM  ติดตั้งเงียบ (มี tcl/tk สำหรับหน้า UI):
REM    "%TEMP%\python-3.12.7-amd64.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_tcltk=1 Include_pip=1 Include_launcher=1 AssociateFiles=0 Shortcuts=0
REM ============================================================

set "PY_VER=3.12.7"
set "PY_URL=https://www.python.org/ftp/python/%PY_VER%/python-%PY_VER%-amd64.exe"
set "PY_SETUP=%TEMP%\python-%PY_VER%-amd64.exe"
set "PYW=%LocalAppData%\Programs\Python\Python312\pythonw.exe"
set "PYE=%LocalAppData%\Programs\Python\Python312\python.exe"

if not exist "main.py" (
  echo [ERROR] ไม่พบ main.py — คัดลอกทั้งโฟลเดอร์ hourly-voice-reminder มาด้วย
  pause
  exit /b 1
)

echo.
echo === Hourly Voice Reminder ===
echo ขั้นที่ 1/3 — ตรวจ Python...
echo.

set "PYTHON="
call :FindPython
if defined PYTHON goto :LaunchUI

echo ไม่พบ Python — จะติดตั้ง Python %PY_VER% ให้อัตโนมัติ
echo ขั้นที่ 2/3 — ดาวน์โหลด + ติดตั้ง (ต้องมีเน็ต รอ 1-3 นาที)
echo URL: %PY_URL%
echo.

echo กำลังดาวน์โหลด...
curl -L --retry 3 --retry-delay 2 -o "%PY_SETUP%" "%PY_URL%"
if errorlevel 1 (
  echo curl ไม่สำเร็จ — ลองด้วย PowerShell...
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PY_URL%' -OutFile '%PY_SETUP%' -UseBasicParsing"
  if errorlevel 1 (
    echo [ERROR] ดาวน์โหลด Python ไม่สำเร็จ
    echo เปิดลิงก์นี้แล้วติดตั้งเอง: %PY_URL%
    start "" "%PY_URL%"
    pause
    exit /b 1
  )
)

if not exist "%PY_SETUP%" (
  echo [ERROR] ไม่พบไฟล์ติดตั้งหลังดาวน์โหลด
  pause
  exit /b 1
)

echo กำลังติดตั้ง Python %PY_VER% (เงียบ)...
"%PY_SETUP%" /quiet InstallAllUsers=0 PrependPath=1 Include_tcltk=1 Include_pip=1 Include_test=0 Include_doc=0 Include_launcher=1 AssociateFiles=0 Shortcuts=0
set "INST_ERR=%ERRORLEVEL%"
del /f /q "%PY_SETUP%" >nul 2>&1

if not "%INST_ERR%"=="0" (
  echo [ERROR] ติดตั้ง Python ไม่สำเร็จ ^(exit %INST_ERR%^)
  echo ติดตั้งเอง: %PY_URL%
  echo ติ๊ก Add python.exe to PATH
  pause
  exit /b 1
)

echo ติดตั้งเสร็จ — รอสักครู่...
timeout /t 4 /nobreak >nul

REM รีเฟรช PATH ใน session นี้
set "PATH=%LocalAppData%\Programs\Python\Python312;%LocalAppData%\Programs\Python\Python312\Scripts;%PATH%"

set "PYTHON="
call :FindPython
if not defined PYTHON (
  echo [ERROR] ติดตั้งแล้วแต่ยังหา Python ไม่เจอ
  echo ลองปิดแล้วเปิด เปิดแอป.bat อีกครั้ง หรือรีสตาร์ทเครื่อง
  pause
  exit /b 1
)

:LaunchUI
echo.
echo ขั้นที่ 3/3 — เปิดหน้าต่าง UI...
echo ใช้: %PYTHON%
echo.

REM เปิด UI ด้วย pythonw (ไม่มีหน้าต่างดำ) — เหมือน Mac
start "" "%PYTHON%" "%~dp0main.py"
exit /b 0

REM ---------- หา Python + tkinter ----------
:FindPython
if exist "%PYW%" (
  "%PYW%" -c "import tkinter" >nul 2>&1
  if not errorlevel 1 (
    set "PYTHON=%PYW%"
    goto :eof
  )
)
if exist "%PYE%" (
  "%PYE%" -c "import tkinter" >nul 2>&1
  if not errorlevel 1 (
    set "PYTHON=%PYE%"
    goto :eof
  )
)
where pythonw >nul 2>&1
if not errorlevel 1 (
  for /f "delims=" %%I in ('where pythonw 2^>nul') do (
    "%%I" -c "import tkinter" >nul 2>&1
    if not errorlevel 1 (
      set "PYTHON=%%I"
      goto :eof
    )
  )
)
where python >nul 2>&1
if not errorlevel 1 (
  for /f "delims=" %%I in ('where python 2^>nul') do (
    echo %%I | find /i "WindowsApps" >nul
    if errorlevel 1 (
      "%%I" -c "import tkinter" >nul 2>&1
      if not errorlevel 1 (
        set "PYTHON=%%I"
        goto :eof
      )
    )
  )
)
where py >nul 2>&1
if not errorlevel 1 (
  for /f "delims=" %%I in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do (
    if exist "%%~dpIpythonw.exe" (
      "%%~dpIpythonw.exe" -c "import tkinter" >nul 2>&1
      if not errorlevel 1 (
        set "PYTHON=%%~dpIpythonw.exe"
        goto :eof
      )
    )
    "%%I" -c "import tkinter" >nul 2>&1
    if not errorlevel 1 (
      set "PYTHON=%%I"
      goto :eof
    )
  )
)
goto :eof
