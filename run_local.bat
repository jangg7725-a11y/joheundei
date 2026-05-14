@echo off
REM ============================================================
REM  사주 분석 서버 — 로컬 실행 스크립트 (Windows)
REM  더블클릭 or:  PowerShell -> .\run_local.bat
REM ============================================================

cd /d "%~dp0"

set "PYRUN="

where python >nul 2>&1 && set "PYRUN=python" && goto :found
where py     >nul 2>&1 && set "PYRUN=py"     && goto :found

if exist "%LocalAppData%\Programs\Python\Launcher\py.exe" (
  set "PYRUN=%LocalAppData%\Programs\Python\Launcher\py.exe"
  goto :found
)
for %%V in (314 313 312 311 310) do (
  if exist "%LocalAppData%\Programs\Python\Python%%V\python.exe" (
    set "PYRUN=%LocalAppData%\Programs\Python\Python%%V\python.exe"
    goto :found
  )
  if exist "%ProgramFiles%\Python%%V\python.exe" (
    set "PYRUN=%ProgramFiles%\Python%%V\python.exe"
    goto :found
  )
)

echo.
echo [ERROR] Python을 찾을 수 없습니다.
echo.
echo  1) https://www.python.org/downloads/ 에서 설치하세요.
echo     설치 시 "Add python.exe to PATH" 를 반드시 체크하세요.
echo  2) 이 창을 닫고 새 터미널에서 다시 실행하세요.
echo.
pause
exit /b 1

:found
echo.
echo [1/3] Python: %PYRUN%
echo [2/3] 패키지 설치 중 (requirements-dev.txt)...
echo.

"%PYRUN%" -m pip install -r requirements-dev.txt --quiet
if errorlevel 1 (
  echo.
  echo [ERROR] 패키지 설치 실패.  오류 메시지를 확인하세요.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo   서버 주소: http://localhost:8000
echo   중지하려면: Ctrl+C
echo ============================================================
echo.

REM 브라우저를 3초 후 자동으로 열기 (서버 기동 시간 확보)
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:8000"

"%PYRUN%" -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

echo.
pause
