@echo off
REM Deploy to Streamlit Cloud - Windows Batch Script
REM Usage: deploy.bat

echo ======================================
echo Deploying to Streamlit Cloud
echo ======================================
echo.

REM Check if git is initialized
if not exist ".git" (
    echo Initializing git...
    git init
    git add -A
    git commit -m "Initial commit"
)

echo.
echo Next steps:
echo.
echo 1. Create a GitHub repository at https://github.com/new
echo    - Repository name: reliability-annotation
echo    - Make it Public
echo.
echo 2. Connect your local repo to GitHub:
echo    git remote add origin https://github.com/YOUR_USERNAME/reliability-annotation.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo 3. Deploy to Streamlit Cloud:
echo    - Go to https://share.streamlit.io
echo    - Click 'New app'
echo    - Select your repository: YOUR_USERNAME/reliability-annotation
echo    - Branch: main
echo    - Main file path: annotation_tool/app_chinese.py
echo    - Click 'Deploy!'
echo.
echo 4. Share the deployed URL with your annotators!
echo.
echo ======================================
pause
