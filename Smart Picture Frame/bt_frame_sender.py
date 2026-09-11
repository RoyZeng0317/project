# 電腦端：把 photos/ 資料夾裡的照片/GIF動畫、天氣、時間，透過已配對的 HC-06
# 藍牙序列埠送給 Raspberry Pi Pico (對應 Pico 端 Raspberry pi pico/main.py 的協定)
# 使用前先在「裝置管理員 > 連接埠(COM與LPT)」找到 HC-06 配對後的
# 「標準序列 藍牙連結(COMx) 輸出」，填入下面的 BT_PORT
import re
import time
import serial
from PIL import Image, ImageSequence
from components import photo, weather

BT_PORT = "COM5"        # 依實際配對到的序號埠修改
BAUD = 115200            # 需與 HC-06 目前設定的鮑率一致，先用 hc06_at_tool.py 送 AT+BAUD8 改過再改這裡
CANVAS = (320, 460)      # 對應 Pico 端螢幕扣掉狀態列後的可顯示區域(320 x (480 - BAR_H))，2026-09 向左旋轉90度改直式
WEATHER_LOCATION = "雲林縣"
CWA_API_KEY = ""         # 同 components/weather.py，需先到 https://opendata.cwa.gov.tw 申請
WEATHER_INTERVAL = 1800  # 天氣多久重查一次(秒)
TIME_INTERVAL = 60       # 時間多久重新校正一次(秒)，Pico 是軟體時鐘，重開機/斷電/重燒都會歸零，需定期重送才能持續顯示真正的當前時間
PHOTO_DWELL = 5          # 靜態相片每張顯示秒數
GIF_FRAME_DWELL = 0.15   # GIF 動畫每格間隔秒數，多張圖輪播模擬「影片」效果


def to_rgb565(img):
    # 等比縮放後置中貼到黑底畫布，避免變形；再逐像素轉成 RGB565 大端 bytes
    img = photo.normalize_rgb(img)
    img.thumbnail(CANVAS)
    canvas = Image.new("RGB", CANVAS, (0, 0, 0))
    canvas.paste(img, ((CANVAS[0] - img.width) // 2, (CANVAS[1] - img.height) // 2))
    data = bytearray(CANVAS[0] * CANVAS[1] * 2)
    i = 0
    for r, g, b in canvas.getdata():
        v = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
        data[i], data[i + 1] = v >> 8, v & 0xFF
        i += 2
    return data


def send_image(ser, img):
    w, h = CANVAS
    ser.write(b"I" + bytes([w >> 8, w & 0xFF, h >> 8, h & 0xFF]) + to_rgb565(img))


def send_weather(ser):
    # 沿用 components/weather.py 既有的抓取邏輯，但面板沒有中文字型，只擷取數字部分送出
    text = weather.fetch_weather(WEATHER_LOCATION, CWA_API_KEY)
    m = re.search(r"(\d+)~(\d+).+?(\d+)%", text)
    ascii_text = f"{m.group(1)}-{m.group(2)}C {m.group(3)}%" if m else "NO DATA"
    payload = ascii_text.encode()
    ser.write(b"W" + bytes([len(payload)]) + payload)


def send_time(ser):
    now = time.localtime()
    ser.write(b"T" + bytes([now.tm_year >> 8, now.tm_year & 0xFF, now.tm_mon, now.tm_mday,
                             now.tm_hour, now.tm_min, now.tm_sec]))


def main():
    ser = serial.Serial(BT_PORT, BAUD, timeout=5)
    last_time = last_weather = 0
    while True:
        if time.time() - last_time > TIME_INTERVAL:
            send_time(ser)
            last_time = time.time()

        if time.time() - last_weather > WEATHER_INTERVAL:
            send_weather(ser)
            last_weather = time.time()

        for name in photo.list_photos():
            path = f"{photo.path}/{name}"
            try:
                if name.lower().endswith(".gif"):
                    for frame in ImageSequence.Iterator(Image.open(path)):
                        send_image(ser, frame)
                        time.sleep(GIF_FRAME_DWELL)
                else:
                    send_image(ser, Image.open(path))
                    time.sleep(PHOTO_DWELL)
            except Exception as e:
                # 手機/截圖工具偶爾會把 HEIC 等 Pillow 讀不懂的檔案存成 .png/.jpg 副檔名，
                # 讀失敗就跳過這張，不要讓一張壞檔卡死整個輪播
                print(f"跳過無法讀取的圖片 {name}: {e}")


if __name__ == "__main__":
    main()
