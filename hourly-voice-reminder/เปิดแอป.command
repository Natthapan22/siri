#!/bin/bash
cd "$(dirname "$0")" || exit 1
ROOT="$(pwd)"

candidates=(
  "$ROOT/.venv/bin/python3"
  /Library/Frameworks/Python.framework/Versions/3.11/bin/python3
  /Library/Frameworks/Python.framework/Versions/Current/bin/python3
  /opt/homebrew/bin/python3
  /usr/local/bin/python3
  /usr/bin/python3
)

PY=""
for c in "${candidates[@]}"; do
  if [ -x "$c" ] && "$c" -c "import tkinter" 2>/dev/null; then
    PY="$c"
    break
  fi
done

if [ -z "$PY" ]; then
  osascript -e 'display alert "ไม่พบ Python 3 + tkinter"'
  exit 1
fi

# เปิด UI แยกจาก Terminal แล้วปิดหน้าต่าง Terminal
nohup "$PY" "$ROOT/main.py" >/dev/null 2>&1 &
osascript -e 'tell application "Terminal" to close front window' >/dev/null 2>&1 || true
exit 0
