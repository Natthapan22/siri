#!/bin/bash
cd "$(dirname "$0")" || exit 1
echo "เริ่ม Hourly Voice Reminder (กด Ctrl+C เพื่อหยุด)"
if command -v python3 >/dev/null 2>&1; then
  exec python3 main.py
fi
osascript -e 'display alert "ไม่พบ Python 3" message "ติดตั้งจาก python.org แล้วดับเบิลคลิก เปิดแอป.command อีกครั้ง"'
exit 1
