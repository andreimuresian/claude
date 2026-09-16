@echo off
REM ============================================================
REM  MZM Studio launcher: pull the latest code, then start the GUI.
REM  Double-click this file, or run it with a .s2p path:
REM      update_and_run.bat "D:\data\line_7.s2p"
REM ============================================================
cd /d "%~dp0"

where git >nul 2>&1
if errorlevel 1 (
    echo [!] git is not installed or not on PATH - skipping the update.
    echo     Install it from https://git-scm.com/download/win and re-run.
    goto :launch
)

echo Checking for updates...
git pull --ff-only
if errorlevel 1 (
    echo.
    echo [!] Could not fast-forward. You probably have local edits.
    echo     Keep them:     git stash  ^&^&  git pull --ff-only  ^&^&  git stash pop
    echo     Discard them:  git reset --hard origin/Lumerical-Interconnect
    echo     Launching the version you already have.
    echo.
)

:launch
python run_mzm_studio.py %*
if errorlevel 1 pause
