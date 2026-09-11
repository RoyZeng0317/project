# 開發用小工具：手機上傳照片用的小型 HTTP 伺服器(對應 mobile_frame_sender.html)。
# 手機瀏覽器選照片，POST 上傳到這裡直接存進 photos/ 資料夾；電腦端 components/GUI.py 的
# 「推送到相框」如果正在跑，下一輪輪播就會自動送去 ESP32-S3-CAM 顯示。
# 不用 Web Bluetooth，所以不挑瀏覽器(Samsung Internet 等非 Chrome 瀏覽器也能用)、不用裝 App、
# 不用處理 HTTPS 憑證警告；只開放 GET 這個頁面本身跟 POST /upload 兩條路，不像
# http.server 預設那樣把整個資料夾(含 .env 等機密檔案)都攤出去給區網任何人瀏覽
# 2026-09-09：改連同一區網的 http LAN IP 手機連不上(可能是路由器開了 AP isolation 擋掉同網段裝置互連，
# 或 Windows 防火牆擋掉區網來源)，改用 Tailscale(100.x.x.x)，同一個 tailnet 底下手機/電腦直接互通，
# 不受路由器/實體網路環境影響；電腦跟手機都要先裝好 Tailscale 且登入同一個帳號
# 用法：python server.py，終端機會印出手機要打開的網址
import http.server
import os
import re
import shutil
import socket
import subprocess
import time
from urllib.parse import unquote

PORT = 8000
ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE_FILE = os.path.join(ROOT, "mobile_frame_sender.html")
PHOTOS_DIR = os.path.join(ROOT, "photos")
os.makedirs(PHOTOS_DIR, exist_ok=True)


def find_tailscale():
    found = shutil.which("tailscale")
    if found:
        return found
    default = r"C:\Program Files\Tailscale\tailscale.exe"
    return default if os.path.exists(default) else None


def get_server_ip():
    # 優先用 Tailscale IP(100.x.x.x)，手機跟電腦不用同一個實體網路也能連；
    # 沒裝 Tailscale 或指令失敗就 fallback 回同區網 IP(舊方法，路由器沒開 AP isolation 的話還是能用)
    tailscale = find_tailscale()
    if tailscale:
        try:
            out = subprocess.run([tailscale, "ip", "-4"], capture_output=True, text=True, check=True)
            ip = out.stdout.strip()
            if ip:
                return ip
        except Exception:
            pass

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/mobile_frame_sender.html"):
            self.send_error(404)
            return
        with open(PAGE_FILE, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != "/upload":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            self.send_error(400, "沒有檔案內容")
            return
        raw_name = unquote(self.headers.get("X-Filename", "photo.jpg"))
        safe_name = re.sub(r"[^\w.\-一-鿿]", "_", os.path.basename(raw_name)) or "photo.jpg"
        name = f"{time.time_ns()}_{safe_name}"  # 奈秒級時間戳，避免多檔連續上傳落在同一秒導致檔名撞掉前一張
        with open(os.path.join(PHOTOS_DIR, name), "wb") as f:
            f.write(self.rfile.read(length))

        body = f"已上傳: {name}".encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ip = get_server_ip()
    print(f"手機瀏覽器打開: http://{ip}:{PORT}/mobile_frame_sender.html")
    http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
