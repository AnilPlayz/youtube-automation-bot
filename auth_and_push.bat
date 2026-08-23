@echo off
title GitHub 1-Click Login & Push
echo =========================================================
echo    AUTHENTICATING WITH GITHUB & PUSHING CODE
echo =========================================================
echo.

set "GH_PATH=C:\Program Files\GitHub CLI\gh.exe"
set "GIT_PATH=C:\Program Files\Git\cmd\git.exe"

echo 1. Logging into GitHub...
echo A code will appear below and your browser will open.
echo Enter the one-time code in your browser to authorize.
echo.

"%GH_PATH%" auth login --web -h github.com -p https

echo.
echo 2. Setting up Git credentials...
"%GH_PATH%" auth setup-git

echo.
echo 3. Pushing code to https://github.com/AnilPlayz/youtube-automation-bot.git ...
"%GIT_PATH%" push -u origin main --force

echo.
echo =========================================================
echo  SUCCESS! ALL FILES HAVE BEEN PUSHED TO YOUR REPOSITORY!
echo =========================================================
echo.
echo You can now refresh your GitHub Actions page and run the workflow!
pause
