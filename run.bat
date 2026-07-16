@echo off
REM =============================================================================
REM Elysium-Bench One-Command Launcher (Windows)
REM =============================================================================

setlocal enabledelayedexpansion

echo.
echo   ============================================================
echo     Elysium-Bench v0.1.0 - Multi-Agent Self-Improvement Benchmark
echo   ============================================================
echo.

REM Parse arguments
set MODE=venv
set CATEGORY=
set CLEANUP=
set LIST_ONLY=0
set QUICK=0

:parse
if "%~1"=="" goto :check_python
if "%~1"=="--mode" (
    set MODE=%~2
    shift
    shift
    goto :parse
)
if "%~1"=="--category" (
    set CATEGORY=--category %~2
    shift
    shift
    goto :parse
)
if "%~1"=="-C" (
    set CATEGORY=--category %~2
    shift
    shift
    goto :parse
)
if "%~1"=="--no-cleanup" (
    set CLEANUP=--no-cleanup
    shift
    goto :parse
)
if "%~1"=="--list" (
    set LIST_ONLY=1
    shift
    goto :parse
)
if "%~1"=="--quick" (
    set QUICK=1
    shift
    goto :parse
)
if "%~1"=="--help" (
    echo Usage: run.bat [OPTIONS]
    echo   --mode venv^|docker   Execution mode (default: venv)
    echo   --category CAT_ID     Run only this category
    echo   --no-cleanup          Keep temp files after run
    echo   --list                List all tasks without running
    echo   --quick               Quick test
    echo   --help                Show this help
    exit /b 0
)
echo Unknown option: %~1
exit /b 1

:check_python
REM Find Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install from https://python.org
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo   Python: %PYVER%

REM Docker check
if "%MODE%"=="docker" (
    where docker >nul 2>&1
    if %errorlevel% neq 0 (
        echo   [WARN] Docker not found, falling back to venv mode
        set MODE=venv
    ) else (
        for /f "tokens=*" %%i in ('docker --version 2^>^&1') do set DVER=%%i
        echo   Docker: !DVER!
    )
)

REM Install
echo.
echo   [*] Installing dependencies...
if "%QUICK%"=="1" (
    python -m pip install -q pyyaml rich click pydantic httpx pytest fastapi >nul 2>&1
) else (
    python -m pip install -q -e . >nul 2>&1
)

if %errorlevel% neq 0 (
    echo   [WARN] Some dependencies may not have installed. Continuing...
)

REM List or run
if "%LIST_ONLY%"=="1" (
    echo.
    python -m elysium_bench.cli list-tasks
    exit /b 0
)

echo.
echo   [*] Running benchmark...
echo.

python -m elysium_bench.cli run --mode %MODE% %CATEGORY% %CLEANUP%

set EXIT_CODE=%errorlevel%

echo.
if %EXIT_CODE% equ 0 (
    echo   [OK] Benchmark completed successfully!
) else (
    echo   [FAIL] Benchmark failed with exit code %EXIT_CODE%
)

REM Show results
if exist results\ (
    for /f "tokens=*" %%i in ('dir /b /o-d results\*.json 2^>nul') do (
        echo   Results: results\%%i
        goto :end
    )
)

:end
exit /b %EXIT_CODE%
