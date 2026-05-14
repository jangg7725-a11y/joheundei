# 로컬에서 사주 웹앱 실행 (PowerShell)
# 사용법: 프로젝트 폴더에서  .\run_local.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$venv = Join-Path $PSScriptRoot ".venv"
if (-not (Test-Path $venv)) {
    Write-Host "[사주] 가상환경 생성: .venv" -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "venv 생성 실패: Python을 확인하세요." -ForegroundColor Red
        exit 1
    }
}

& (Join-Path $venv "Scripts\Activate.ps1")

Write-Host "[사주] 의존성 설치 중..." -ForegroundColor Cyan
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "pip 실패" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " 브라우저: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host " 종료: Ctrl+C" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
