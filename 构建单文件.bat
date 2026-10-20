@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================================
echo    打包单文件 - src + vendor 合并为 说明书编辑器-v2.html
echo ========================================================
echo.

where python >nul 2>nul
if %errorlevel%==0 (
    python "build.py" %*
    goto :end
)
where python3 >nul 2>nul
if %errorlevel%==0 (
    python3 "build.py" %*
    goto :end
)
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 "build.py" %*
    goto :end
)

echo 没有找到 Python。
echo 请先安装 Python 3（https://www.python.org/downloads/），
echo 安装时务必勾选 "Add Python to PATH"。
echo.
pause
exit /b 1

:end
echo.
echo 打包结束。直接双击根目录的 说明书编辑器-v2.html 即可使用。
pause
