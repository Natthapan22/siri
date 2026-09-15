# -*- coding: utf-8 -*-
"""Hourly Voice Reminder — Thai TTS via Edge (Premwadee), no Windows voice setup."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import threading
import time
import tkinter as tk
from ctypes import windll
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

import edge_tts

APP_TITLE = "Hourly Voice Reminder"
VOICE = "th-TH-PremwadeeNeural"
CONFIG_NAME = "config.json"


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def config_path() -> Path:
    return app_dir() / CONFIG_NAME


def load_config() -> dict:
    path = config_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data.get("hours"), list) and isinstance(data.get("message"), str):
                return {
                    "message": data["message"],
                    "hours": sorted({int(h) for h in data["hours"] if 0 <= int(h) <= 23}),
                }
        except Exception:
            pass
    return {"message": "ส่งเรทreseller", "hours": list(range(24))}


def save_config(message: str, hours: list[int]) -> None:
    data = {"message": message, "hours": sorted(hours)}
    config_path().write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def play_mp3(path: str) -> None:
    alias = "hvr_tts"
    winmm = windll.winmm
    # Normalize for MCI
    p = os.path.abspath(path).replace("/", "\\")
    winmm.mciSendStringW(f'close {alias}', None, 0, None)
    err = winmm.mciSendStringW(f'open "{p}" type mpegvideo alias {alias}', None, 0, None)
    if err:
        raise RuntimeError(f"เปิดไฟล์เสียงไม่สำเร็จ (MCI {err})")
    try:
        err = winmm.mciSendStringW(f"play {alias} wait", None, 0, None)
        if err:
            raise RuntimeError(f"เล่นเสียงไม่สำเร็จ (MCI {err})")
    finally:
        winmm.mciSendStringW(f"close {alias}", None, 0, None)


async def synthesize_to_file(text: str, out_path: str) -> None:
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(out_path)


def speak(text: str) -> None:
    text = (text or "").strip()
    if not text:
        raise ValueError("ข้อความว่าง")
    fd, tmp = tempfile.mkstemp(prefix="hvr_", suffix=".mp3")
    os.close(fd)
    try:
        asyncio.run(synthesize_to_file(text, tmp))
        play_mp3(tmp)
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.resizable(False, False)
        self.running = False
        self._spoken_slot: str | None = None
        self._busy = False

        cfg = load_config()
        self.message_var = tk.StringVar(value=cfg["message"])
        self.hour_vars = {h: tk.BooleanVar(value=(h in cfg["hours"])) for h in range(24)}
        self.status_var = tk.StringVar(value="พร้อมใช้งาน — กดเทสเสียงหรือเริ่มได้เลย")
        self.engine_var = tk.StringVar(
            value="เสียง: Microsoft Premwadee (ไทย ผู้หญิง) — ไม่ต้องติดตั้งเสียง Windows"
        )

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(500, self._tick)

    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 6}
        root = ttk.Frame(self, padding=12)
        root.grid(row=0, column=0, sticky="nsew")

        ttk.Label(root, text="ข้อความแจ้งเตือน").grid(row=0, column=0, sticky="w")
        row1 = ttk.Frame(root)
        row1.grid(row=1, column=0, sticky="ew", **pad)
        entry = ttk.Entry(row1, textvariable=self.message_var, width=42)
        entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(row1, text="เทสเสียง", command=self._on_test).grid(
            row=0, column=1, padx=(8, 0)
        )
        row1.columnconfigure(0, weight=1)

        ttk.Label(root, text="ชั่วโมงที่ต้องการแจ้งเตือน").grid(row=2, column=0, sticky="w")
        hours = ttk.Frame(root)
        hours.grid(row=3, column=0, sticky="w", **pad)
        for h in range(24):
            r, c = divmod(h, 6)
            ttk.Checkbutton(
                hours, text=f"{h:02d}:00", variable=self.hour_vars[h]
            ).grid(row=r, column=c, sticky="w", padx=4, pady=2)

        btns = ttk.Frame(root)
        btns.grid(row=4, column=0, sticky="w", **pad)
        self.start_btn = ttk.Button(btns, text="เริ่ม", command=self._on_start)
        self.start_btn.grid(row=0, column=0, padx=(0, 8))
        self.stop_btn = ttk.Button(btns, text="หยุด", command=self._on_stop, state="disabled")
        self.stop_btn.grid(row=0, column=1)

        ttk.Label(root, textvariable=self.status_var).grid(row=5, column=0, sticky="w", pady=(8, 0))
        ttk.Label(root, textvariable=self.engine_var, foreground="#444").grid(
            row=6, column=0, sticky="w"
        )

    def _selected_hours(self) -> list[int]:
        return [h for h, v in self.hour_vars.items() if v.get()]

    def _persist(self) -> None:
        save_config(self.message_var.get().strip(), self._selected_hours())

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    def _run_speak(self, text: str, done_msg: str) -> None:
        if self._busy:
            return
        self._busy = True

        def worker() -> None:
            try:
                speak(text)
                self.after(0, lambda: self._set_status(done_msg))
            except Exception as exc:  # noqa: BLE001
                msg = str(exc)
                self.after(
                    0,
                    lambda: self._set_status(f"เล่นเสียงไม่สำเร็จ: {msg}"),
                )
                self.after(
                    0,
                    lambda: messagebox.showerror(
                        APP_TITLE,
                        "พูดข้อความไม่สำเร็จ\nตรวจเน็ตแล้วลองใหม่\n\n" + msg,
                    ),
                )
            finally:
                self._busy = False

        threading.Thread(target=worker, daemon=True).start()

    def _on_test(self) -> None:
        self._persist()
        text = self.message_var.get().strip()
        if not text:
            messagebox.showwarning(APP_TITLE, "กรุณากรอกข้อความแจ้งเตือน")
            return
        self._set_status("กำลังเทสเสียง...")
        self._run_speak(text, "เทสเสียงเสร็จแล้ว — กดเริ่มเมื่อพร้อม")

    def _on_start(self) -> None:
        hours = self._selected_hours()
        if not hours:
            messagebox.showwarning(APP_TITLE, "เลือกอย่างน้อย 1 ชั่วโมง")
            return
        if not self.message_var.get().strip():
            messagebox.showwarning(APP_TITLE, "กรุณากรอกข้อความแจ้งเตือน")
            return
        self._persist()
        self.running = True
        self._spoken_slot = None
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._set_status(f"กำลังทำงาน — จะแจ้งเตือนตอน {', '.join(f'{h:02d}:00' for h in hours)}")

    def _on_stop(self) -> None:
        self.running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self._set_status("หยุดแล้ว — กดเริ่มเมื่อพร้อม")

    def _tick(self) -> None:
        if self.running and not self._busy:
            now = datetime.now()
            if now.hour in self._selected_hours() and now.minute == 0:
                slot = now.strftime("%Y-%m-%d %H")
                if slot != self._spoken_slot:
                    self._spoken_slot = slot
                    text = self.message_var.get().strip()
                    self._set_status(f"กำลังแจ้งเตือน {now.strftime('%H:%M')}...")
                    self._run_speak(
                        text,
                        f"แจ้งเตือนล่าสุด {now.strftime('%H:%M')} — รอชั่วโมงถัดไป",
                    )
        self.after(1000, self._tick)

    def _on_close(self) -> None:
        try:
            self._persist()
        finally:
            self.destroy()


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
