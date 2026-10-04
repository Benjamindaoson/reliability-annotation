@echo off
chcp 65001 >nul
REM ==========================================
REM 一键启动标注系统 + ngrok 内网穿透
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
    echo [OK] streamlit 安装完成
) else (
    echo [OK] streamlit 已安装
)

REM 检查 ngrok
where ngrok >nul 2>&1
if errorlevel 1 (
    echo.
    echo [提示] 未找到 ngrok
    echo 请下载 ngrok: https://ngrok.com/download
    echo 下载后把 ngrok.exe 放到此文件夹，或添加到系统 PATH
    echo.
    echo 按任意键继续启动标注工具（不含 ngrok）...
    pause >nul
    goto :START_STREAMLIT
)

REM 检查 ngrok 配置
ngrok config check >nul 2>&1
if errorlevel 1 (
    echo.
    echo [配置] ngrok 需要配置 authtoken
    echo 请运行: ngrok config add-authtoken YOUR_TOKEN
    echo 获取 token: https://dashboard.ngrok.com/get-started/your-authtoken
    echo.
    echo 按任意键继续启动标注工具（不含 ngrok）...
    pause >nul
    goto :START_STREAMLIT
)

:START_STREAMLIT
echo.
echo ==========================================
echo 启动标注工具中...
echo ==========================================
echo.
echo 标注工具将在浏览器中打开
echo.

REM 启动 streamlit
start "" cmd /c "cd /d "%~dp0" && streamlit run annotation_tool\app_chinese.py"

REM 等待一下
timeout /t 3 /nobreak >nul

:CHECK_NGROK
REM 检查 ngrok
where ngrok >nul 2>&1
if errorlevel 1 (
    echo.
    echo [提示] ngrok 未安装，无法创建公网链接
    echo 请手动配置 ngrok 或使用 Streamlit Cloud 部署
    goto :END
)

REM 启动 ngrok
echo.
echo ==========================================
echo 启动 ngrok 内网穿透...
echo ==========================================
echo.
echo 按 Ctrl+C 停止，或关闭此窗口停止所有服务
echo.

ngrok http 8501

:END
pause
