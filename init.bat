@echo off

:start
cls

python -m venv .\venv
cd .\venv\Scripts
CALL activate.bat
pip install selenium==3.141.0

pause
exit