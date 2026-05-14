#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로컬에서 사주 웹 서버 실행.

  python run_local.py

브라우저에서 http://127.0.0.1:8000 을 열면 입력 폼을 사용할 수 있습니다.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQ = ROOT / "requirements.txt"


def main() -> None:
    if not REQ.is_file():
        print("requirements.txt 없음:", REQ, file=sys.stderr)
        sys.exit(1)

    print("[사주] 의존성 설치 중...")
    r = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(REQ), "--quiet"],
        cwd=str(ROOT),
    )
    if r.returncode != 0:
        sys.exit(r.returncode)

    print("[사주] 서버 시작 → http://127.0.0.1:8000 (Ctrl+C 종료)\n")
    os_ret = subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--reload",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        cwd=str(ROOT),
    )
    sys.exit(os_ret.returncode)


if __name__ == "__main__":
    main()
