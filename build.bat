@echo off
setlocal enabledelayedexpansion
cd /d %~dp0

echo ============================================================
echo  LiveSubtitle Windows - Build Script
echo ============================================================

REM 1. Python venv
where py >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python launcher "py" not found. Please install Python 3.10+ from python.org.
    exit /b 1
)
if not exist .venv (
    echo [step] Creating virtualenv .venv ...
    py -3 -m venv .venv || goto :err
)
call .venv\Scripts\activate.bat || goto :err

REM 2. Install deps
echo [step] Upgrading pip & installing requirements ...
python -m pip install --upgrade pip || goto :err
python -m pip install -r requirements.txt || goto :err
python -m pip install pyinstaller==6.10.0 || goto :err

REM 3. Pre-download models (skipped if already present)
echo [step] Downloading models (Vosk en + Argos en->zh) ...
python download_models.py || goto :err

REM 4. Clean & build with PyInstaller
if exist build rmdir /s /q build
if exist dist\LiveSubtitle rmdir /s /q dist\LiveSubtitle
if exist dist\LiveSubtitleSetup.exe del /q dist\LiveSubtitleSetup.exe

echo [step] PyInstaller build ...
pyinstaller --noconfirm --clean LiveSubtitle.spec || goto :err

REM 5. Inno Setup
set "ISCC1=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
set "ISCC2=%ProgramFiles%\Inno Setup 6\ISCC.exe"
set "ISCC="
if exist "%ISCC1%" set "ISCC=%ISCC1%"
if exist "%ISCC2%" set "ISCC=%ISCC2%"
if "%ISCC%"=="" (
    echo.
    echo [WARN] Inno Setup 6 not found. PyInstaller output is at dist\LiveSubtitle\
    echo        Install Inno Setup 6 from https://jrsoftware.org/isinfo.php and re-run.
    goto :portable_done
)

echo [step] Inno Setup compile ...
"%ISCC%" installer.iss || goto :err

echo.
echo ============================================================
echo  Done! Installer:  %CD%\dist\LiveSubtitleSetup.exe
echo ============================================================
goto :eof

:portable_done
echo.
echo ============================================================
echo  Portable build:  %CD%\dist\LiveSubtitle\LiveSubtitle.exe
echo  (Send the whole 'dist\LiveSubtitle' folder as a zip.)
echo ============================================================
goto :eof

:err
echo.
echo [BUILD FAILED]
exit /b 1
