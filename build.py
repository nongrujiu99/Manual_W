# -*- coding: utf-8 -*-
"""
把 src/editor.src.html + vendor/*.js 打包成一个可离线双击的单文件 HTML。

用法：
    python build.py            构建，覆盖根目录的 说明书编辑器-v2.html
    python build.py --out x.html   指定输出路径
    python build.py --check    只校验占位是否都能解析，不写文件

设计约束：
- 全程 newline='' 读写，不做换行符转换，保证产物与拆分前逐字节一致。
- vendor 里的库保持原始形态，升级时直接替换文件，不用改模板。
"""

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'src', 'editor.src.html')
VENDOR = os.path.join(ROOT, 'vendor')
DEFAULT_OUT = os.path.join(ROOT, '说明书编辑器-v2.html')

RE_BLOCK = re.compile(r'/\* @vendor:([\w.\-]+) \*/')
RE_JSON = re.compile(r'"@@vendor-json:([\w.\-]+)@@"')


def read_text(path):
    with open(path, encoding='utf-8', newline='') as f:
        return f.read()


def load_vendor(name):
    path = os.path.join(VENDOR, name)
    if not os.path.isfile(path):
        raise SystemExit('缺少 vendor 文件: %s' % path)
    return read_text(path)


def js_string_literal(text):
    """把文本转成可安全放进 <script> 的 JS 双引号字符串字面量。"""
    lit = json.dumps(text, ensure_ascii=False)
    # 只有当内容真的会提前闭合 <script> 时才转义，否则保持原样，
    # 这样产物与拆分前的单文件逐字节一致。
    if '</script' in text.lower():
        lit = lit.replace('</', '<\\/')
    return lit


def build(template):
    used = []

    def block_sub(m):
        name = m.group(1)
        used.append(name)
        return load_vendor(name)

    def json_sub(m):
        name = m.group(1)
        used.append(name + ' (json)')
        return js_string_literal(load_vendor(name))

    out = RE_BLOCK.sub(block_sub, template)
    out = RE_JSON.sub(json_sub, out)
    return out, used


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=DEFAULT_OUT)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()

    if not os.path.isfile(SRC):
        raise SystemExit('找不到模板: %s' % SRC)

    template = read_text(SRC)
    out, used = build(template)

    leftover = RE_BLOCK.findall(out) + RE_JSON.findall(out)
    if leftover:
        raise SystemExit('仍有未解析的占位: %s' % ', '.join(leftover))

    print('模板      : %s (%.1f KB)' % (os.path.relpath(SRC, ROOT), len(template.encode('utf-8')) / 1024))
    for name in used:
        print('  注入 %-24s %8.1f KB' % (name, len(load_vendor(name.split(' ')[0]).encode('utf-8')) / 1024))
    print('产物      : %.1f KB' % (len(out.encode('utf-8')) / 1024))

    if args.check:
        print('校验通过（未写文件）')
        return 0

    with open(args.out, 'w', encoding='utf-8', newline='') as f:
        f.write(out)
    print('已写入    : %s' % os.path.relpath(args.out, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
