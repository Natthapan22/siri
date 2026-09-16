#!/usr/bin/env python3
"""Download bundled offline Thai Piper voice (not committed to git — too large)."""

from __future__ import annotations

import urllib.request
from pathlib import Path

BASE = "https://huggingface.co/tranhuyluyen/piper-voices-thai/resolve/main"
NAME = "th_TH-mms_female-medium"
FILES = (f"{NAME}.onnx", f"{NAME}.onnx.json")


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
        urllib.request.urlretrieve(url, dest)
        print(f"saved {dest} ({dest.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
