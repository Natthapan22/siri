"""Cross-platform text-to-speech (macOS `say` / Windows SAPI)."""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile

logger = logging.getLogger(__name__)

_thai_voice_warned = False


def _speak_macos(text: str) -> None:
    say = shutil.which("say")
    if not say:
        raise RuntimeError("ไม่พบคำสั่ง `say` (ต้องใช้บน macOS)")
    # Prefer Thai voice when available
    voice = "Kanya"
    result = subprocess.run(
        [say, "-v", voice, text],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # Fallback without explicit voice
        result = subprocess.run([say, text], capture_output=True, text=True)
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(f"`say` ล้มเหลว: {err or result.returncode}")


def _list_windows_voices_ps() -> str:
    """Return PowerShell output listing installed SAPI voices."""
    script = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.GetInstalledVoices() | ForEach-Object { "
        "$_.VoiceInfo.Name + '|' + $_.VoiceInfo.Culture.Name "
        "}"
    )
    kwargs: dict = {"capture_output": True, "text": True}
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        **kwargs,
    )
    if result.returncode != 0:
        return ""
    return result.stdout or ""


def _speak_windows(text: str) -> None:
    global _thai_voice_warned

    voices_raw = _list_windows_voices_ps()
    has_thai = any(
        "|th-" in line.lower() or line.lower().endswith("|th")
        for line in voices_raw.splitlines()
    )
    if not has_thai:
        has_thai = "th-th" in voices_raw.lower()

    if not has_thai and not _thai_voice_warned:
        _thai_voice_warned = True
        msg = (
            "Windows เครื่องนี้ไม่มีเสียงภาษาไทย (Thai TTS) — "
            "จะใช้เสียงเริ่มต้นของระบบแทน "
            "(Settings → Time & language → Speech เพื่อเพิ่มเสียงไทย)"
        )
        logger.warning(msg)
        print(msg, file=sys.stderr)

    tmp = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8-sig", suffix=".txt", delete=False
    )
    try:
        tmp.write(text)
        tmp.close()
        path = tmp.name.replace("'", "''")
        select_thai = ""
        if has_thai:
            select_thai = (
                "$thai = $s.GetInstalledVoices() | "
                "Where-Object { $_.VoiceInfo.Culture.Name -like 'th*' } | "
                "Select-Object -First 1; "
                "if ($thai) { $s.SelectVoice($thai.VoiceInfo.Name) }; "
            )
        script = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"{select_thai}"
            f"$text = Get-Content -LiteralPath '{path}' -Raw -Encoding UTF8; "
            "$s.Speak($text)"
        )
        kwargs: dict = {"capture_output": True, "text": True}
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            **kwargs,
        )
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(
                f"Windows TTS ล้มเหลว: {err or result.returncode}"
            )
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def speak(text: str) -> None:
    """Speak `text` using the native TTS for the current OS."""
    if not text or not str(text).strip():
        return
    system = platform.system()
    if system == "Darwin":
        _speak_macos(str(text))
    elif system == "Windows":
        _speak_windows(str(text))
    else:
        raise RuntimeError(
            f"ไม่รองรับระบบปฏิบัติการ: {system} (รองรับ macOS และ Windows)"
        )
