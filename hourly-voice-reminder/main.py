#!/usr/bin/env python3
"""Hourly voice reminder — tkinter UI (macOS + Windows)."""

from __future__ import annotations

import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import messagebox, ttk

DEFAULT_MESSAGE = "ส่งเรทรีเซลเล่อ"
DEFAULT_HOURS = list(range(24))
MAC_VOICE = "Kanya"
_thai_voice_warned = False


def app_dir() -> Path:
    """Folder for config/logs — next to .exe / next to .app / next to main.py."""
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve()
        # macOS .app: .../HourlyVoiceReminder.app/Contents/MacOS/HourlyVoiceReminder
        if exe.parent.name == "MacOS" and exe.parent.parent.name == "Contents":
            return exe.parent.parent.parent.parent
        return exe.parent
    return Path(__file__).resolve().parent


CONFIG_PATH = app_dir() / "config.json"
LOG = logging.getLogger("hourly_reminder")


def setup_logging() -> None:
    log_dir = app_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    LOG.setLevel(logging.INFO)
    LOG.handlers.clear()
    fmt = logging.Formatter(
        "%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    fh = logging.FileHandler(log_dir / "hourly-reminder.log", encoding="utf-8")
    fh.setFormatter(fmt)
    LOG.addHandler(fh)


def default_config() -> dict:
    return {
        "message": DEFAULT_MESSAGE,
        "hours": DEFAULT_HOURS.copy(),
    }


def load_config() -> dict:
    cfg = default_config()
    if not CONFIG_PATH.exists():
        return cfg
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(data.get("message"), str) and data["message"].strip():
            cfg["message"] = data["message"].strip()
        hours = data.get("hours")
        if isinstance(hours, list):
            cleaned = sorted(
                {
                    int(h)
                    for h in hours
                    if isinstance(h, (int, float)) and 0 <= int(h) <= 23
                }
            )
            if cleaned:
                cfg["hours"] = cleaned
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _ps_kwargs() -> dict:
    kwargs: dict = {"capture_output": True, "text": True}
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return kwargs


def _speak_macos(text: str) -> None:
    say = shutil.which("say")
    if not say:
        raise RuntimeError("ไม่พบคำสั่ง say (ต้องใช้บน macOS)")
    result = subprocess.run(
        [say, "-v", MAC_VOICE, text], capture_output=True, text=True
    )
    if result.returncode != 0:
        result = subprocess.run([say, text], capture_output=True, text=True)
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(f"say ล้มเหลว: {err or result.returncode}")


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
    if not has_thai and not _thai_voice_warned:
        _thai_voice_warned = True
        LOG.warning(
            "ไม่มีเสียงภาษาไทยบน Windows — ใช้เสียงเริ่มต้น "
            "(Settings → Time & language → Speech)"
        )

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


def voice_label() -> str:
    if platform.system() == "Darwin":
        return f"เสียง: {MAC_VOICE} (macOS)"
    return "เสียง: Windows SAPI (เลือกไทยอัตโนมัติถ้ามี)"


def next_selected_hour(
    hours: list[int], after: datetime | None = None
) -> datetime | None:
    if not hours:
        return None
    now = after or datetime.now()
    base = now.replace(minute=0, second=0, microsecond=0)
    for offset in range(0, 25):
        candidate = base + timedelta(hours=offset)
        if candidate <= now:
            continue
        if candidate.hour in hours:
            return candidate
    return None


class ReminderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Hourly Voice Reminder")
        self.root.geometry("460x520+120+80")
        self.root.minsize(420, 480)

        self.cfg = load_config()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._save_after_id: str | None = None

        self.message_var = tk.StringVar(value=self.cfg["message"])
        self.status_var = tk.StringVar(value="พร้อม — กดเริ่มเพื่อรอแจ้งเตือน")
        self.hour_vars = [
            tk.BooleanVar(value=(h in self.cfg["hours"])) for h in range(24)
        ]

        self._build_ui()
        self.message_var.trace_add("write", lambda *_: self._schedule_autosave())
        for var in self.hour_vars:
            var.trace_add("write", lambda *_: self._schedule_autosave())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(200, self._bring_to_front)

    def _bring_to_front(self) -> None:
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.root.attributes("-topmost", True)
            self.root.after(500, lambda: self.root.attributes("-topmost", False))
        except tk.TclError:
            pass

    def _build_ui(self) -> None:
        pad = {"padx": 12, "pady": 6}
        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="ข้อความแจ้งเตือน").pack(anchor=tk.W)
        msg_row = ttk.Frame(frm)
        msg_row.pack(fill=tk.X, **pad)
        ttk.Entry(msg_row, textvariable=self.message_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        self.test_btn = ttk.Button(msg_row, text="เทสเสียง", command=self._on_test)
        self.test_btn.pack(side=tk.LEFT, padx=(8, 0))

        row = ttk.Frame(frm)
        row.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(row, text="ติ๊กครบ 24 ชม.", command=self._select_all).pack(
            side=tk.LEFT
        )
        ttk.Button(row, text="เอาติ๊กออกทั้งหมด", command=self._clear_all).pack(
            side=tk.LEFT, padx=(8, 0)
        )
        ttk.Label(row, text="บันทึกอัตโนมัติ", foreground="#555").pack(
            side=tk.LEFT, padx=(12, 0)
        )

        ttk.Label(
            frm, text="ชั่วโมงที่ต้องการแจ้งเตือน (ค่าเริ่มต้นติ๊กครบ)"
        ).pack(anchor=tk.W, pady=(8, 0))
        grid = ttk.Frame(frm)
        grid.pack(fill=tk.BOTH, expand=True, pady=6)
        for h in range(24):
            r, c = divmod(h, 6)
            ttk.Checkbutton(
                grid, text=f"{h:02d}:00", variable=self.hour_vars[h]
            ).grid(row=r, column=c, sticky=tk.W, padx=4, pady=2)

        btns = ttk.Frame(frm)
        btns.pack(fill=tk.X, pady=(8, 4))
        self.start_btn = ttk.Button(btns, text="เริ่ม", command=self._on_start)
        self.start_btn.pack(side=tk.LEFT)
        self.stop_btn = ttk.Button(
            btns, text="หยุด", command=self._on_stop, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(frm, textvariable=self.status_var, wraplength=420).pack(
            anchor=tk.W, pady=(8, 0)
        )
        ttk.Label(frm, text=voice_label(), foreground="#555").pack(anchor=tk.W)

    def _selected_hours(self) -> list[int]:
        return [h for h in range(24) if self.hour_vars[h].get()]

    def _current_config(self) -> dict:
        return {
            "message": self.message_var.get().strip() or DEFAULT_MESSAGE,
            "hours": self._selected_hours(),
        }

    def _set_status(self, text: str) -> None:
        self.root.after(0, lambda: self.status_var.set(text))

    def _select_all(self) -> None:
        for var in self.hour_vars:
            var.set(True)

    def _clear_all(self) -> None:
        for var in self.hour_vars:
            var.set(False)

    def _schedule_autosave(self) -> None:
        if self._save_after_id is not None:
            self.root.after_cancel(self._save_after_id)
        self._save_after_id = self.root.after(300, self._autosave)

    def _autosave(self) -> None:
        self._save_after_id = None
        cfg = self._current_config()
        try:
            save_config(cfg)
            self.cfg = cfg
        except OSError as exc:
            self.status_var.set(f"บันทึกไม่สำเร็จ: {exc}")

    def _on_test(self) -> None:
        msg = self.message_var.get().strip()
        if not msg:
            messagebox.showwarning("ยังไม่มีข้อความ", "กรอกข้อความก่อน แล้วกดเทสเสียง")
            return
        self.test_btn.configure(state=tk.DISABLED)

        def run() -> None:
            try:
                self._set_status(f"กำลังเทสเสียง: {msg}")
                speak(msg)
                self._set_status("เทสเสียงเสร็จแล้ว — กดเริ่มเมื่อพร้อม")
            except Exception as exc:
                self.root.after(
                    0, lambda: messagebox.showerror("พูดไม่สำเร็จ", str(exc))
                )
            finally:
                self.root.after(
                    0, lambda: self.test_btn.configure(state=tk.NORMAL)
                )

        threading.Thread(target=run, daemon=True).start()

    def _on_start(self) -> None:
        cfg = self._current_config()
        if not cfg["hours"]:
            messagebox.showwarning(
                "ยังไม่เลือกชั่วโมง", "เลือกอย่างน้อย 1 ชั่วโมงก่อนเริ่ม"
            )
            return
        save_config(cfg)
        self.cfg = cfg
        self._stop.clear()
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        LOG.info("Reminder started hours=%s message=%r", cfg["hours"], cfg["message"])

    def _on_stop(self) -> None:
        self._stop.set()
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.status_var.set("หยุดแล้ว")
        LOG.info("Reminder stopped")

    def _loop(self) -> None:
        while not self._stop.is_set():
            cfg = self.cfg
            hours = set(cfg["hours"])
            target = next_selected_hour(sorted(hours))
            if target is None:
                self._set_status("ไม่มีชั่วโมงที่เลือก — หยุด")
                self.root.after(0, self._on_stop)
                return

            while not self._stop.is_set():
                cfg = self.cfg
                hours = set(cfg["hours"])
                if target.hour not in hours:
                    break
                remaining = (target - datetime.now()).total_seconds()
                if remaining <= 0:
                    break
                self._set_status(
                    f"กำลังรอ · รอบถัดไป {target.strftime('%H:%M')} "
                    f"(อีก {int(remaining)} วินาที) · {cfg['message']}"
                )
                self._stop.wait(timeout=min(1.0, remaining))

            if self._stop.is_set():
                break

            cfg = self.cfg
            hours = set(cfg["hours"])
            now = datetime.now()
            if now.hour not in hours:
                continue

            msg = cfg["message"]
            try:
                self._set_status(f"แจ้งเตือน {now.strftime('%H:%M')}: {msg}")
                LOG.info("Speaking reminder at %s", now.strftime("%H:%M"))
                speak(msg)
            except Exception as exc:
                self._set_status(f"ผิดพลาด: {exc}")
                LOG.exception("Speak failed: %s", exc)
                time.sleep(2)

            self._stop.wait(timeout=1.0)

        self._set_status("หยุดแล้ว")

    def _on_close(self) -> None:
        self._stop.set()
        try:
            save_config(self._current_config())
        except OSError:
            pass
        self.root.destroy()


def main() -> int:
    setup_logging()
    LOG.info("UI starting platform=%s python=%s", platform.system(), sys.executable)
    boot = app_dir() / "logs" / "ui-boot.txt"
    try:
        boot.write_text(f"starting {datetime.now().isoformat()}\n", encoding="utf-8")
    except OSError:
        pass

    try:
        root = tk.Tk()
    except Exception as exc:
        LOG.exception("Tk() failed: %s", exc)
        try:
            boot.write_text(f"Tk failed: {exc}\n", encoding="utf-8")
        except OSError:
            pass
        if platform.system() == "Windows":
            try:
                import ctypes

                ctypes.windll.user32.MessageBoxW(
                    0, f"เปิด UI ไม่สำเร็จ:\n{exc}", "Hourly Voice Reminder", 0x10
                )
            except Exception:
                pass
        return 1

    try:
        root.tk.call("tk", "scaling", 1.2)
    except tk.TclError:
        pass

    ReminderApp(root)
    try:
        boot.write_text(
            f"UI mainloop running {datetime.now().isoformat()}\n", encoding="utf-8"
        )
    except OSError:
        pass
    LOG.info("UI mainloop running")
    root.mainloop()
    LOG.info("UI closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
