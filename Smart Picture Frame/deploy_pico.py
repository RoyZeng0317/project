# 電腦端：一次把 Raspberry pi pico/ 資料夾下所有 MicroPython 原始檔 + photos/ 本地快取圖
# 透過 mpremote 燒進 Pico 內建 flash，取代逐一手動輸入 mpremote 指令；快取圖部分沿用
# pico_flash_photos.py 既有的轉檔/燒錄邏輯，避免同一套流程寫兩次。全部燒完會自動 reset，
# Pico 直接以新程式重新開機，不用再手動拔插 USB
# 用法：接上 USB 線，到「裝置管理員 > 連接埠(COM與LPT)」找到 Pico 的 COM 埠後執行:
#   python deploy_pico.py COM6
# 注意：若出現 PermissionError/could not open port，通常是 Thonny、mpremote 或另一個
# usb_frame_sender.py 還佔用著同一個 COM 埠，先把它們關閉再重試
import os, subprocess, sys
from pico_flash_photos import flash as flash_photos

PICO_DIR = os.path.join(os.path.dirname(__file__), "Raspberry pi pico")
SOURCE_FILES = ["main.py", "ili9481_parallel.py", "font8x8.py", "bt_uart_rx.py", "usb_uart_rx.py", "Conversation.py"]


def deploy(port):
    for name in SOURCE_FILES:
        local = os.path.join(PICO_DIR, name)
        print(f"上傳 {name} -> :{name}")
        subprocess.run(["mpremote", "connect", port, "fs", "cp", local, f":{name}"], check=True)
    flash_photos(port)
    subprocess.run(["mpremote", "connect", port, "reset"], check=True)
    print("燒錄完成，Pico 已重新開機執行新程式")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python deploy_pico.py <COM埠>，例如 python deploy_pico.py COM6")
        sys.exit(1)
    deploy(sys.argv[1])
