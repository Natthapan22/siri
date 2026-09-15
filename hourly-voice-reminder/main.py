#!/usr/bin/env python3
"""Hourly voice reminder — macOS / Windows (bundleable as .exe)."""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from tts import speak

# --- configuration ---
REMINDER_MESSAGE = (
    "ครบหนึ่งชั่วโมงแล้วครับพี่ พักสายตาสักหน่อย "
    "ลุกเดิน ยืดตัว แล้วกลับมาทำงานต่อได้แล้วครับ"
)
INTERVAL_SECONDS = 60 * 60
SPEAK_ON_START = False
# ---------------------


def app_dir() -> Path:
    """Directory for logs next to the script or frozen .exe."""
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

    fmt = logging.Formatter("%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Also mirror to stderr when running from a console (dev / macOS)
    if not getattr(sys, "frozen", False):
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(fmt)
        logger.addHandler(sh)

    return logger


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
        "interval=%ss speak_on_start=%s message=%r",
        INTERVAL_SECONDS,
        SPEAK_ON_START,
        REMINDER_MESSAGE,
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
