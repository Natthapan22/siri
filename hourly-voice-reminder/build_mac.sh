#!/bin/bash
# Build HourlyVoiceReminder.app on macOS
set -euo pipefail
cd "$(dirname "$0")"
python3 -m pip install -q --upgrade pip pyinstaller edge-tts
python3 -m PyInstaller --noconfirm --clean HourlyVoiceReminder.spec
echo ""
echo "สร้างแล้ว: dist/HourlyVoiceReminder.app"
echo "ดับเบิลคลิกเพื่อเปิด — ไม่ต้องมี Python"
