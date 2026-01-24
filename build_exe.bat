@echo off
echo ==========================================
echo      Labs Automation Tool Builder
echo ==========================================

echo [1/3] Installing/Updating PyInstaller...
pip install pyinstaller --upgrade

echo [2/3] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

echo [3/3] Building EXE (Onefile)...
:: --onefile: Pack everything into single exe
:: --console: Keep console window for logs (Change to --noconsole to hide)
:: --name: Output filename
:: --add-data: Include app package source logic if needed or assets
:: --collect-all: Ensure complex libs like selenium/certifi are fully included

pyinstaller --noconfirm --onefile --console --name "LabsAutoTool" ^
    --hidden-import "PIL" ^
    --hidden-import "PIL._tkinter_finder" ^
    --collect-all "certifi" ^
    --collect-all "selenium" ^
    app/main.py

echo.
echo ==========================================
if exist "dist\LabsAutoTool.exe" (
    echo BUILD SUCCESSFUL!
    echo File location: dist\LabsAutoTool.exe
) else (
    echo BUILD FAILED!
)
echo ==========================================
pause
