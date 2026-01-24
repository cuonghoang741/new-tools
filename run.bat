@echo off
set "PYTHONPATH=%~dp0"
pip install requests selenium webdriver-manager
python app/main.py
pause
