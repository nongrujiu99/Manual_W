#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
说明书编辑器 · AI 本地代理
--------------------------------------------------
作用：在你自己电脑上运行一个小服务，把浏览器的 AI 请求转发给通义千问。
      这样即使用 file:// 双击打开编辑器（浏览器的跨域限制会让请求挂住），
      AI 智能整理也能正常工作。

用法：
    1) 双击运行，或命令行执行：
         python3 AI本地代理.py          （macOS / Linux）
         python AI本地代理.py           （Windows）
    2) 看到 "代理已启动" 后，回到编辑器：
        「引擎与设置」→ 接口地址 填  http://127.0.0.1:8787/v1
    3) 正常点「AI 智能整理」即可，Key 不变。

只监听 127.0.0.1（仅本机能访问），不保存、不记录你的 Key 内容。
按 Ctrl+C 停止。
"""

import http.server
import json
import socketserver
import sys
import urllib.request
import urllib.error

import os

# 上游地址可用环境变量覆盖，方便换成自建网关或其他兼容接口
UPSTREAM = os.environ.get("AI_UPSTREAM", "https://dashscope.aliyuncs.com/compatible-mode/v1").rstrip("/")
PORT = int(os.environ.get("AI_PORT", "8787"))


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    # ---------- CORS：允许来自 file:// 的页面访问 ----------
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Max-Age", "86400")

    def do_OPTIONS(self):
        # 浏览器的预检请求：直接放行，不再转发给上游
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()
        self.log("OPTIONS 预检 → 已放行")

    def do_GET(self):
        # 健康检查：浏览器访问 http://127.0.0.1:8787/v1 应看到 OK
        body = b"OK - AI proxy is running. POST /v1/chat/completions"
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = self.rfile.read(length) if length else b"{}"
            auth = self.headers.get("Authorization") or ""

            url = UPSTREAM + self.path[len("/v1"):] if self.path.startswith("/v1") else UPSTREAM + self.path
            self.log(f"转发 {len(payload)} 字节 → {url}")

            req = urllib.request.Request(url, data=payload, method="POST")
            req.add_header("Content-Type", "application/json")
            if auth:
                req.add_header("Authorization", auth)

            try:
                resp = urllib.request.urlopen(req, timeout=300)
            except urllib.error.HTTPError as e:
                # 上游返回的错误（401 Key 无效 / 额度不足等）原样透传，便于编辑器提示
                raw = e.read()
                self.log(f"上游返回 HTTP {e.code}")
                self._reply(e.code, raw, e.headers.get("Content-Type", "application/json"))
                return

            ctype = resp.headers.get("Content-Type", "application/json")
            streaming = "event-stream" in ctype.lower()

            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", ctype)
            if streaming:
                self.send_header("Cache-Control", "no-cache")
                self.send_header("X-Accel-Buffering", "no")
                self.send_header("Transfer-Encoding", "chunked")
                self.end_headers()
                n = 0
                while True:
                    chunk = resp.read1(4096)      # 边收边转，模型吐字能实时显示
                    if not chunk:
                        break
                    n += len(chunk)
                    self.wfile.write(b"%x\r\n" % len(chunk) + chunk + b"\r\n")
                    self.wfile.flush()
                self.wfile.write(b"0\r\n\r\n")
                self.log(f"流式转发完成 {n} 字节")
            else:
                data = resp.read()
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                self.log(f"一次性转发完成 {len(data)} 字节")

        except Exception as exc:                   # noqa: BLE001
            self.log(f"本地异常: {exc}")
            try:
                body = json.dumps({"error": {"message": f"本地代理异常: {exc}"}}).encode()
                self._reply(502, body, "application/json")
            except Exception:
                pass

    def _reply(self, code, body, ctype):
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log(self, msg):
        sys.stderr.write(f"[{self.log_date_time_string()}] {msg}\n")
        sys.stderr.flush()

    def log_message(self, fmt, *args):   # 静音默认访问日志
        pass


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    port = PORT
    for i, a in enumerate(sys.argv):
        if a in ("-p", "--port") and i + 1 < len(sys.argv):
            try:
                port = int(sys.argv[i + 1])
            except ValueError:
                pass
    try:
        srv = Server(("127.0.0.1", port), Handler)
    except OSError as e:
        print(f"端口 {port} 启动失败：{e}\n可换端口运行：python3 AI本地代理.py --port 8899")
        return 1
    print("=" * 56)
    print("  AI 本地代理已启动")
    print(f"  监听：http://127.0.0.1:{port}/v1")
    print(f"  上游：{UPSTREAM}")
    print("")
    print("  请在编辑器「引擎与设置」里把接口地址填为：")
    print(f"      http://127.0.0.1:{port}/v1")
    print("")
    print("  只监听本机，按 Ctrl+C 停止")
    print("=" * 56)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
