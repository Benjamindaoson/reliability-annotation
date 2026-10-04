@echo off
chcp 65001 >nul
REM ==========================================
REM 一键启动标注工具（本地）
REM ==========================================

echo.
echo ==========================================
echo   长程 AI Agent 可靠性标注系统
echo ==========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python 已安装

REM 检查 streamlit
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [安装] 正在安装 streamlit...
    pip install streamlit -q
)

REM 启动 streamlit
echo.
echo 正在启动标注工具...
echo 浏览器将自动打开标注界面
echo.

cd /d "%~dp0"
streamlit run annotation_tool\app_chinese.py

pause
