@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================================
echo    AI 本地代理 - 启动中
echo ========================================================
echo.

REM 依次尝试常见的 Python 命令
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 "AI本地代理.py"
    goto :end
)
where python >nul 2>nul
if %errorlevel%==0 (
    python "AI本地代理.py"
    goto :end
)
where python3 >nul 2>nul
if %errorlevel%==0 (
    python3 "AI本地代理.py"
    goto :end
)

echo 没有找到 Python。
echo 请先安装 Python 3（https://www.python.org/downloads/）
echo 安装时务必勾选 "Add Python to PATH"。
echo.
pause

:end
echo.
echo 代理已停止。
pause
