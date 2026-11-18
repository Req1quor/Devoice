@echo off
echo ==============================================
echo        Devoice - Windows Build Script
echo ==============================================

if not exist venv (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate

echo [INFO] Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo [INFO] Building executable with PyInstaller...
pyinstaller packaging\devoice.spec --noconfirm

echo ==============================================
if exist dist\Devoice\Devoice.exe (
    echo [SUCCESS] Build finished successfully!
    echo Application located at: dist\Devoice\Devoice.exe
) else (
    echo [ERROR] Build failed. Check the logs above.
)
echo ==============================================
pause
