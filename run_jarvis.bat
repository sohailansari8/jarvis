@echo off
title JARVIS — AI Desktop Assistant
cd /d "%~dp0"
echo.
echo  ==========================================================
echo   JARVIS AI Desktop Assistant — Starting...
echo  ==========================================================
echo.
echo  If prompted for an API key, go to:
echo  https://aistudio.google.com/app/apikey
echo  (Key MUST start with: AIza...)
echo.
python -W ignore main.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo  !! JARVIS exited with an error (code %ERRORLEVEL%)
    echo  Check the output above for details.
)
echo.
pause

