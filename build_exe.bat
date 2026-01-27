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
:: Excluding unnecessary heavy packages
pyinstaller --noconfirm --onefile --noconsole --name "LabsAutoTool" ^
    --exclude-module torch ^
    --exclude-module torchvision ^
    --exclude-module torchaudio ^
    --exclude-module matplotlib ^
    --exclude-module scipy ^
    --exclude-module numpy.distutils ^
    --exclude-module IPython ^
    --exclude-module jupyter ^
    --exclude-module notebook ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "cv2" ^
    --hidden-import "pandas" ^
    --hidden-import "openpyxl" ^
    --hidden-import "openpyxl.cell._writer" ^
    --collect-submodules "cv2" ^
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
