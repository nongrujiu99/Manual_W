#!/bin/bash
# 打包单文件：src + vendor 合并为 说明书编辑器-v2.html
cd "$(dirname "$0")" || exit 1

echo "========================================================"
echo "   打包单文件 - src + vendor 合并"
echo "========================================================"

if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo "没有找到 Python 3。请先安装，或改用浏览器打开现有单文件。"
    exit 1
fi

"$PY" build.py "$@"
STATUS=$?
echo
echo "打包结束。直接打开根目录的 说明书编辑器-v2.html 即可使用。"
exit $STATUS
