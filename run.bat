@echo off

:start
cls

cd .\venv\Scripts
CALL activate.bat
cd ..\..\src
python main.py

pause
exit