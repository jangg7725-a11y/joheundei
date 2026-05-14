#!/usr/bin/env bash
# ============================================================
#  사주 분석 서버 — 로컬 실행 스크립트 (Mac / Linux)
#  사용법:
#    chmod +x run_local.sh
#    ./run_local.sh
# ============================================================

set -euo pipefail

# 스크립트 위치로 이동
cd "$(dirname "$0")"

URL="http://localhost:8000"

# ── Python 탐색 ────────────────────────────────────────────
PYRUN=""
for cmd in python3 python py; do
  if command -v "$cmd" &>/dev/null; then
    PYRUN="$cmd"
    break
  fi
done

if [[ -z "$PYRUN" ]]; then
  echo ""
  echo "[ERROR] Python을 찾을 수 없습니다."
  echo "  Mac:   brew install python  또는  https://www.python.org/downloads/"
  echo "  Linux: sudo apt install python3  또는  sudo dnf install python3"
  echo ""
  exit 1
fi

echo ""
echo "[1/3] Python: $($PYRUN --version)"
echo "[2/3] 패키지 설치 중 (requirements-dev.txt)..."
echo ""

"$PYRUN" -m pip install -r requirements-dev.txt --quiet

echo ""
echo "============================================================"
echo "  서버 주소: $URL"
echo "  중지하려면: Ctrl+C"
echo "============================================================"
echo ""

# ── 브라우저 자동 열기 (백그라운드, 3초 대기) ──────────────
open_browser() {
  sleep 3
  if command -v open &>/dev/null; then       # macOS
    open "$URL"
  elif command -v xdg-open &>/dev/null; then # Linux (X11 / Wayland)
    xdg-open "$URL"
  elif command -v wslview &>/dev/null; then  # WSL
    wslview "$URL"
  fi
}
open_browser &

# ── 서버 실행 ─────────────────────────────────────────────
"$PYRUN" -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
