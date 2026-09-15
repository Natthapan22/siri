#!/usr/bin/env python3
"""Hourly voice reminder — one file, macOS + Windows."""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# --- ตั้งค่าตรงนี้ ---
REMINDER_MESSAGE = (
    "ครบหนึ่งชั่วโมงแล้วครับพี่ พักสายตาสักหน่อย "
    "ลุกเดิน ยืดตัว แล้วกลับมาทำงานต่อได้แล้วครับ"
)
INTERVAL_SECONDS = 60 * 60
SPEAK_ON_START = False
# ---------------------

_thai_voice_warned = False


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def setup_logging() -> logging.Logger:
    log_dir = app_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "hourly-reminder.log"

    logger = logging.getLogger("hourly_reminder")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter(
        "%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    if not getattr(sys, "frozen", False):
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(fmt)
        logger.addHandler(sh)
    return logger


def _speak_macos(text: str) -> None:
    say = shutil.which("say")
    if not say:
        raise RuntimeError("ไม่พบคำสั่ง say (ต้องใช้บน macOS)")
    result = subprocess.run(
        [say, "-v", "Kanya", text], capture_output=True, text=True
    )
    if result.returncode != 0:
        result = subprocess.run([say, text], capture_output=True, text=True)
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(f"say ล้มเหลว: {err or result.returncode}")


def _ps_kwargs() -> dict:
    kwargs: dict = {"capture_output": True, "text": True}
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return kwargs


def _speak_windows(text: str) -> None:
    global _thai_voice_warned
    list_script = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.GetInstalledVoices() | ForEach-Object { "
        "$_.VoiceInfo.Name + '|' + $_.VoiceInfo.Culture.Name }"
    )
    voices = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            list_script,
        ],
        **_ps_kwargs(),
    )
    raw = voices.stdout or ""
    has_thai = "th-th" in raw.lower() or any(
        "|th-" in line.lower() for line in raw.splitlines()
    )
    log = logging.getLogger("hourly_reminder")
    if not has_thai and not _thai_voice_warned:
        _thai_voice_warned = True
        msg = (
            "ไม่มีเสียงภาษาไทยบน Windows — ใช้เสียงเริ่มต้น "
            "(Settings → Time & language → Speech เพื่อเพิ่มเสียงไทย)"
        )
        log.warning(msg)

    tmp = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8-sig", suffix=".txt", delete=False
    )
    try:
        tmp.write(text)
        tmp.close()
        path = tmp.name.replace("'", "''")
        select = ""
        if has_thai:
            select = (
                "$thai = $s.GetInstalledVoices() | "
                "Where-Object { $_.VoiceInfo.Culture.Name -like 'th*' } | "
                "Select-Object -First 1; "
                "if ($thai) { $s.SelectVoice($thai.VoiceInfo.Name) }; "
            )
        script = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"{select}"
            f"$t = Get-Content -LiteralPath '{path}' -Raw -Encoding UTF8; "
            "$s.Speak($t)"
        )
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            **_ps_kwargs(),
        )
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(f"Windows TTS ล้มเหลว: {err or result.returncode}")
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def speak(text: str) -> None:
    if not text or not str(text).strip():
        return
    system = platform.system()
    if system == "Darwin":
        _speak_macos(str(text))
    elif system == "Windows":
        _speak_windows(str(text))
    else:
        raise RuntimeError(f"ไม่รองรับ: {system}")


def wait_interruptible(seconds: float) -> None:
    end = time.monotonic() + seconds
    while True:
        remaining = end - time.monotonic()
        if remaining <= 0:
            return
        time.sleep(min(0.5, remaining))


def main() -> int:
    logger = setup_logging()
    logger.info("Hourly Voice Reminder started")
    logger.info(
        "interval=%ss speak_on_start=%s", INTERVAL_SECONDS, SPEAK_ON_START
    )

    if SPEAK_ON_START:
        try:
            logger.info("Speaking reminder (on start)")
            speak(REMINDER_MESSAGE)
        except Exception as exc:
            logger.exception("Speak failed on start: %s", exc)
            return 1

    try:
        while True:
            wait_interruptible(INTERVAL_SECONDS)
            try:
                logger.info("Speaking reminder")
                speak(REMINDER_MESSAGE)
            except Exception as exc:
                logger.exception("Speak failed: %s", exc)
    except KeyboardInterrupt:
        logger.info("Stopped by user (Ctrl+C)")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
