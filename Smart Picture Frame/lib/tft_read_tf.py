# 電腦端：TF 卡留在 ILI9481 面板上，透過 USB 序列埠向 Mega 要 SD 卡內容(見 MEGA2560_test.ino
# 的 'L'/'R' 指令)，不用拔卡插電腦讀卡機，供 mega_deploy_gui.py 呼叫。
# 檔名規則、CANVAS 尺寸都跟 mega_frame_sender.py / MEGA2560_test.ino 的 scanLocalPhotos() 一致，
# bytes_to_image() 是 mega_frame_sender.to_rgb565() 的逆運算，只用來預覽確認顏色/內容有沒有燒對
import time
import serial
from PIL import Image

CANVAS = (480, 296)  # Mega 面板扣掉狀態列後的可顯示區域，跟 mega_frame_sender.py 的 CANVAS 一致
BAUD = 500000  # 需與 MEGA2560_test.ino 的 SERIAL_BAUD 一致


def open_mega(port):
    # 開序列埠會觸發 Mega 自動重開機(setup() 重跑一次，含 SD 卡重新掛載)，先等它開機完成
    ser = serial.Serial(port, BAUD, timeout=5)
    time.sleep(2)
    ser.reset_input_buffer()
    return ser


def list_bin_photos(ser):
    # 'L' 指令：Mega 回傳開機時 scanLocalPhotos() 掃到的本地快取圖張數
    ser.reset_input_buffer()
    ser.write(b"L")
    n = ser.read(1)
    count = n[0] if n else 0
    return [f"P{i:03d}.BIN" for i in range(count)]


def read_bin_photo(ser, name):
    # 'R' 指令：Mega 讀 SD 卡上的 name，回傳 4 bytes 大端檔案大小(0 代表沒有此檔)接原始位元組
    ser.reset_input_buffer()
    payload = name.encode()
    ser.write(b"R" + bytes([len(payload)]) + payload)
    header = ser.read(4)
    if len(header) != 4:
        return None
    size = int.from_bytes(header, "big")
    if size == 0:
        return None
    data = ser.read(size)
    return data if len(data) == size else None


def bytes_to_image(data, size=CANVAS):
    w, h = size
    img = Image.new("RGB", (w, h))
    i = 0
    for y in range(h):
        for x in range(w):
            v = (data[i] << 8) | data[i + 1]
            img.putpixel((x, y), ((v >> 11 & 0x1F) << 3, (v >> 5 & 0x3F) << 2, (v & 0x1F) << 3))
            i += 2
    return img
