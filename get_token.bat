@echo off
title YouTube Token Generator
echo Starting YouTube Token Generator...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Get-YouTubeToken.ps1"
pause
