@echo off
echo =========================================================
echo    PUSHING TO: https://github.com/AnilPlayz/youtube-automation-bot.git
echo =========================================================
echo.

where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Git is not installed or not found in PATH!
    echo Please download and install Git from: https://git-scm.com/download/win
    echo Then run this script again.
    pause
    exit /b 1
)

if not exist ".git" (
    git init
)

git config user.name "AnilPlayz"
git config user.email "anilplayz@users.noreply.github.com"

git add main.py src/ scripts/ config/ data/ assets/skins/ .github/ requirements.txt README.md .gitignore .env.example
git commit -m "AI Minecraft Shorts Automation with Custom Skin & Watermark"

git branch -M main
git remote remove origin 2>nul
git remote add origin https://github.com/AnilPlayz/youtube-automation-bot.git
git push -u origin main

echo.
echo =========================================================
echo  PUSH COMPLETED!
echo =========================================================
pause
