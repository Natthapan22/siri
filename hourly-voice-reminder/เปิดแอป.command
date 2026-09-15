#!/bin/bash
cd "$(dirname "$0")" || exit 1

pick_python() {
  for py in \
    "$PWD/.venv/bin/python3" \
    /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 \
    /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 \
    /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 \
    /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
    /opt/homebrew/bin/python3 \
    /usr/local/bin/python3 \
    /usr/bin/python3
  do
    if [ -x "$py" ] && "$py" -c "import sys" 2>/dev/null; then
      echo "$py"
      return 0
    fi
  done
  return 1
}

PY="$(pick_python || true)"
if [ -z "$PY" ]; then
  if command -v brew >/dev/null 2>&1; then
    osascript -e 'display alert "กำลังติดตั้ง Python" message "ไม่พบ Python — จะใช้ Homebrew ติดตั้งให้อัตโนมัติ (ต้องมีเน็ต)"'
    brew install python
    PY="$(pick_python || true)"
  fi
fi

if [ -z "$PY" ]; then
  osascript -e 'display alert "ไม่พบ Python 3" message "ติดตั้งจาก https://www.python.org/downloads/ แล้วดับเบิลคลิก เปิดแอป.command อีกครั้ง"'
  open "https://www.python.org/downloads/"
  exit 1
fi

echo "เริ่ม Hourly Voice Reminder (กด Ctrl+C เพื่อหยุด)"
exec "$PY" main.py
