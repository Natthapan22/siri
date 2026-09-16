#!/usr/bin/env python3
"""Download bundled offline Thai Piper voice (not committed to git — too large)."""

from __future__ import annotations

import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

BASE = "https://huggingface.co/tranhuyluyen/piper-voices-thai/resolve/main"
NAME = "th_TH-mms_female-medium"
FILES = (f"{NAME}.onnx", f"{NAME}.onnx.json")


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    curl = shutil.which("curl")
    if curl:
        subprocess.check_call(
            [
                curl,
                "-fL",
                "--retry",
                "5",
                "--retry-delay",
                "2",
                "-o",
                str(dest),
                url,
            ]
        )
        return
    urllib.request.urlretrieve(url, dest)


def main() -> int:
    out = Path(__file__).resolve().parent.parent / "voices"
    out.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        dest = out / name
        if dest.is_file() and dest.stat().st_size > 1000:
            print(f"skip (exists): {dest}")
            continue
        url = f"{BASE}/{name}"
        print(f"download {url}")
        try:
            _download(url, dest)
        except Exception as exc:
            if dest.exists():
                dest.unlink(missing_ok=True)
            print(f"FAILED {name}: {exc}", file=sys.stderr)
            return 1
        print(f"saved {dest} ({dest.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
