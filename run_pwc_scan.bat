@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (py -3 pwc_scan.py) else (python pwc_scan.py)
if errorlevel 1 pause
