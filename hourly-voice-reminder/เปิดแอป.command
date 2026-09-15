#!/bin/bash
cd "$(dirname "$0")" || exit 1

pick_python() {
  for py in \
    "$PWD/.venv/bin/python3" \
    /Library/Frameworks/Python.framework/Versions/3.13/Resources/Python.app/Contents/MacOS/Python \
    /Library/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python \
    /Library/Frameworks/Python.framework/Versions/3.11/Resources/Python.app/Contents/MacOS/Python \
    /Library/Frameworks/Python.framework/Versions/Current/Resources/Python.app/Contents/MacOS/Python \
    /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 \
    /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 \
    /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 \
    /opt/homebrew/bin/python3 \
    /usr/local/bin/python3 \
    /usr/bin/python3
  do
    if [ -x "$py" ] && "$py" -c "import tkinter" 2>/dev/null; then
      echo "$py"
      return 0
    fi
  done
  return 1
}

PY="$(pick_python || true)"
if [ -z "$PY" ]; then
  if command -v brew >/dev/null 2>&1; then
    osascript -e 'display alert "กำลังติดตั้ง Python" message "จะใช้ Homebrew ติดตั้ง Python + tkinter (ต้องมีเน็ต)"'
    brew install python python-tk
    PY="$(pick_python || true)"
  fi
fi

if [ -z "$PY" ]; then
  osascript -e 'display alert "ไม่พบ Python + tkinter" message "ติดตั้งจาก python.org แล้วดับเบิลคลิกอีกครั้ง"'
  open "https://www.python.org/downloads/"
  exit 1
fi

# เปิด UI โดยไม่ผูกกับหน้าต่าง Terminal
"$PY" main.py &>/dev/null &
disown
exit 0
