@echo off
set "PYTHONPATH=%~dp0"
pip install requests selenium webdriver-manager customtkinter pillow opencv-python pandas openpyxl
python app/main.py
pause
