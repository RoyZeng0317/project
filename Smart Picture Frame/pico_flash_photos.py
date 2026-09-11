# 電腦端：把 photos/ 資料夾裡的靜態圖片轉成 Pico 面板看得懂的 RGB565 原始格式，
# 透過 mpremote(pip install mpremote，已加進 requirements.txt) 經 USB 燒進 Pico 內建 flash
# 的 /photos_cache/ 資料夾，開機後 Pico 端 main.py 會自動輪播這些「本地快取圖」當預設畫面，
# 不用等電腦即時傳輸；GIF 動畫不燒錄(張數太多會塞爆 flash)，動畫仍走即時傳輸(bt/usb_frame_sender.py)
# Pico 內建 flash 扣掉 MicroPython 韌體後可用空間有限(約 1MB 上下)，每張圖固定
# 320x460 RGB565 = 294400 bytes(2026-09 向左旋轉90度改直式，原本 480x300)，
# 用 MAX_PHOTOS 限制最多燒幾張，避免塞爆
# 用法：接上 USB 線，到「裝置管理員 > 連接埠(COM與LPT)」找到 Pico 的 COM 埠後執行:
#   python pico_flash_photos.py COM6
import os
import subprocess
import sys
import tempfile
from PIL import Image
from components import photo
from bt_frame_sender import to_rgb565

MAX_PHOTOS = 3  # 依 Pico 實際可用 flash 容量調整；每張 294400 bytes，3 張約 863KB


def flash(port):
    pool = photo.get_selected() or photo.list_photos()
    candidates = [n for n in pool if not n.lower().endswith(".gif")]
    if not candidates:
        print("photos/ 資料夾裡沒有可燒錄的靜態圖片")
        return

    subprocess.run(["mpremote", "connect", port, "fs", "mkdir", ":/photos_cache"], check=False)
    burned = 0
    with tempfile.TemporaryDirectory() as tmp:
        for name in candidates:
            if burned >= MAX_PHOTOS:
                break
            try:
                # 手機/截圖工具偶爾會把 HEIC 等 Pillow 讀不懂的檔案存成 .png/.jpg 副檔名，
                # 讀失敗就跳過這張，不要讓一張壞檔卡死整批燒錄
                data = to_rgb565(Image.open(os.path.join(photo.path, name)))
            except Exception as e:
                print(f"跳過無法讀取的圖片 {name}: {e}")
                continue
            local_bin = os.path.join(tmp, f"{burned:02d}.bin")
            with open(local_bin, "wb") as f:
                f.write(data)
            remote = f":/photos_cache/{burned:02d}.bin"
            print(f"燒錄 {name} -> {remote}")
            subprocess.run(["mpremote", "connect", port, "fs", "cp", local_bin, remote], check=True)
            burned += 1
    print(f"完成，共燒錄 {burned} 張圖到 Pico 內建 flash" if burned else "沒有成功燒錄任何圖片(全部讀取失敗)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python pico_flash_photos.py <COM埠>，例如 python pico_flash_photos.py COM6")
        sys.exit(1)
    flash(sys.argv[1])
