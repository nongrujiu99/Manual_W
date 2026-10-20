#!/bin/bash
cd "$(dirname "$0")"

echo "========================================================"
echo "   AI 本地代理 - 启动中"
echo "========================================================"
echo

if command -v python3 >/dev/null 2>&1; then
    python3 "AI本地代理.py"
elif command -v python >/dev/null 2>&1; then
    python "AI本地代理.py"
else
    echo "没有找到 Python 3。"
    echo "macOS 可安装：brew install python3"
    echo "或直接到 https://www.python.org/downloads/ 下载安装。"
    echo
    read -p "按回车键关闭..."
    exit 1
fi

echo
echo "代理已停止。"
