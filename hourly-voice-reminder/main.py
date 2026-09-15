#!/usr/bin/env python3
"""Hourly voice reminder — tkinter UI (macOS + Windows)."""

from __future__ import annotations

import json
import os
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

CONFIG_PATH = Path(__file__).with_name("config.json")
DEFAULT_MESSAGE = "ส่งเรทรีเซลเล่อ"
DEFAULT_HOURS = list(range(24))
MAC_VOICE = "Kanya"


def default_voice() -> str:
    return MAC_VOICE if sys.platform == "darwin" else "System"


def voice_label() -> str:
    if sys.platform == "darwin":
        return f"เสียง: {MAC_VOICE} (ไทย · macOS)"
    return "เสียง: ระบบ Windows (SAPI · เลือกไทยอัตโนมัติถ้ามี)"


def default_config() -> dict:
    return {
        "message": DEFAULT_MESSAGE,
        "hours": DEFAULT_HOURS.copy(),
        "voice": default_voice(),
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
        if isinstance(data.get("voice"), str) and data["voice"].strip():
            cfg["voice"] = data["voice"].strip()
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def speak_macos(message: str, voice: str) -> None:
    say_path = shutil.which("say")
    if not say_path:
        raise RuntimeError("ไม่พบคำสั่ง `say`")
    result = subprocess.run(
        [say_path, "-v", voice or MAC_VOICE, message],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(
            f"`say` ล้มเหลว (exit {result.returncode})"
            + (f": {err}" if err else "")
        )


def speak_windows(message: str) -> None:
    """ใช้ Windows SAPI ผ่าน PowerShell — ไม่ต้องติดตั้ง package เพิ่ม."""
    # เขียนข้อความลงไฟล์ชั่วคราว กันปัญหา quote / ภาษาไทย
    tmp = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8-sig", suffix=".txt", delete=False
    )
    try:
        tmp.write(message)
        tmp.close()
        path = tmp.name.replace("'", "''")
        script = f"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$thai = $s.GetInstalledVoices() |
  Where-Object {{ $_.VoiceInfo.Culture.Name -like 'th*' }} |
  Select-Object -First 1
if ($thai) {{ $s.SelectVoice($thai.VoiceInfo.Name) }}
$text = Get-Content -LiteralPath '{path}' -Raw -Encoding UTF8
$s.Speak($text)
"""
        kwargs: dict = {"capture_output": True, "text": True}
        if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
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
                f"พูดบน Windows ไม่สำเร็จ"
                + (f": {err}" if err else "")
            )
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def speak(message: str, voice: str | None = None) -> None:
    if sys.platform == "darwin":
        speak_macos(message, voice or MAC_VOICE)
    elif sys.platform == "win32":
        speak_windows(message)
    else:
        raise RuntimeError("รองรับเฉพาะ macOS และ Windows")


def next_selected_hour(
    hours: list[int], after: datetime | None = None
) -> datetime | None:
    """คืนเวลา :00 ของชั่วโมงถัดไปที่อยู่ใน hours (วนข้ามวันได้)."""
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
        self.root.minsize(420, 480)

        self.cfg = load_config()
        self.running = False
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

        self.message_var = tk.StringVar(value=self.cfg["message"])
        self.status_var = tk.StringVar(value="พร้อม — กดเริ่มเพื่อรอแจ้งเตือน")
        self.hour_vars = [
            tk.BooleanVar(value=(h in self.cfg["hours"])) for h in range(24)
        ]
        self._save_after_id: str | None = None

        self._build_ui()
        self.message_var.trace_add("write", lambda *_: self._schedule_autosave())
        for var in self.hour_vars:
            var.trace_add("write", lambda *_: self._schedule_autosave())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        pad = {"padx": 12, "pady": 6}
        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="ข้อความแจ้งเตือน").pack(anchor=tk.W)
        msg_row = ttk.Frame(frm)
        msg_row.pack(fill=tk.X, **pad)
        self.message_entry = ttk.Entry(msg_row, textvariable=self.message_var)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
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
            frm, text="ชั่วโมงที่ต้องการแจ้งเตือน (ติ๊กไว้ก่อนครบ 24 ชม.)"
        ).pack(anchor=tk.W, pady=(8, 0))
        grid = ttk.Frame(frm)
        grid.pack(fill=tk.BOTH, expand=True, pady=6)
        for h in range(24):
            r, c = divmod(h, 6)
            label = f"{h:02d}:00"
            ttk.Checkbutton(grid, text=label, variable=self.hour_vars[h]).grid(
                row=r, column=c, sticky=tk.W, padx=4, pady=2
            )

        btns = ttk.Frame(frm)
        btns.pack(fill=tk.X, pady=(8, 4))
        self.start_btn = ttk.Button(btns, text="เริ่ม", command=self._on_start)
        self.start_btn.pack(side=tk.LEFT)
        self.stop_btn = ttk.Button(
            btns, text="หยุด", command=self._on_stop, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(8, 0))

        ttk.Label(frm, textvariable=self.status_var, wraplength=400).pack(
            anchor=tk.W, pady=(8, 0)
        )
        ttk.Label(frm, text=voice_label(), foreground="#555").pack(anchor=tk.W)

    def _selected_hours(self) -> list[int]:
        return [h for h in range(24) if self.hour_vars[h].get()]

    def _current_config(self) -> dict:
        return {
            "message": self.message_var.get().strip() or DEFAULT_MESSAGE,
            "hours": self._selected_hours(),
            "voice": default_voice(),
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
            messagebox.showwarning(
                "ยังไม่มีข้อความ", "กรอกข้อความก่อน แล้วกดเทสเสียง"
            )
            return

        self.test_btn.configure(state=tk.DISABLED)

        def run() -> None:
            try:
                self._set_status(f"กำลังเทสเสียง: {msg}")
                speak(msg, self.cfg.get("voice"))
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
        self.running = True
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _on_stop(self) -> None:
        self._stop.set()
        self.running = False
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.status_var.set("หยุดแล้ว")

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
                speak(msg, cfg.get("voice"))
            except Exception as exc:
                self._set_status(f"ผิดพลาด: {exc}")
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
    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.2)
    except tk.TclError:
        pass
    ReminderApp(root)
    root.mainloop()
    return 0


def _crash_log(exc: BaseException) -> None:
    log = Path(__file__).with_name("launch-error.txt")
    try:
        log.write_text(
            f"[{datetime.now().isoformat()}] {type(exc).__name__}: {exc}\n",
            encoding="utf-8",
        )
    except OSError:
        pass
    try:
        import tkinter as _tk
        from tkinter import messagebox as _mb

        r = _tk.Tk()
        r.withdraw()
        _mb.showerror("Hourly Voice Reminder", f"เปิดไม่สำเร็จ:\n{exc}")
        r.destroy()
    except Exception:
        pass


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        _crash_log(exc)
        raise
