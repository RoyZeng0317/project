# 電腦端：改用 USB 排線直接接 Raspberry Pi Pico / ESP32-S3-CAM 原生的 USB 序列埠，
# 把 photos/ 資料夾裡的照片/GIF動畫、天氣、時間送過去；ESP32-S3-CAM 版還多了錄音回傳
# ('A'+4byte長度+PCM，對應 ESP32-S3-CAM/SmartFrame/protocol.cpp 的 'R'指令觸發)，
# Pico 版不會送這個訊息，check_recording() 只是每次都順手非阻塞檢查一下，不影響 Pico 原本行為
# 通訊協定跟 bt_frame_sender.py 完全一樣，這裡直接重用 bt_frame_sender.py 裡的轉檔/送資料函式，
# 避免同一套邏輯寫兩次
# 使用前先接上 USB 線，到「裝置管理員 > 連接埠(COM與LPT)」找到裝置的
# 「USB 序列裝置(COMx)」，填入下面的 USB_PORT
import os
import time
import wave
from PIL import Image, ImageSequence
import serial
from components import photo
from bt_frame_sender import to_rgb565, send_image, send_weather, send_time, CANVAS, TIME_INTERVAL

USB_PORT = "COM9"        # 依實際裝置在裝置管理員顯示的 COM 埠修改
BAUD = 115200             # 走真正的 USB CDC，鮑率數值不影響傳輸速度，維持慣例填常見值即可
WEATHER_INTERVAL = 1800  # 天氣多久重查一次(秒)，同 bt_frame_sender.py
PHOTO_DWELL = 5          # 靜態相片每張顯示秒數
GIF_FRAME_DWELL = 0.15   # GIF 動畫每格間隔秒數
RECORDINGS_DIR = os.path.join(os.path.dirname(__file__), "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)


def check_recording(ser):
    # 非阻塞檢查有沒有 ESP32-S3-CAM 傳回來的錄音，沒有資料就立刻返回，不拖慢輪播節奏
    if ser.in_waiting == 0 or ser.read(1) != b"A":
        return
    n = int.from_bytes(ser.read(4), "big")
    pcm = ser.read(n)
    path = os.path.join(RECORDINGS_DIR, f"{int(time.time())}.wav")
    with wave.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(16000)
        f.writeframes(pcm)
    print(f"錄音已存檔: {path}")


def main():
    ser = serial.Serial(USB_PORT, BAUD, timeout=5)
    last_time = last_weather = 0
    while True:
        if time.time() - last_time > TIME_INTERVAL:
            send_time(ser)
            last_time = time.time()

        if time.time() - last_weather > WEATHER_INTERVAL:
            send_weather(ser)
            last_weather = time.time()

        check_recording(ser)

        for name in photo.list_photos():
            path = f"{photo.path}/{name}"
            try:
                if name.lower().endswith(".gif"):
                    for frame in ImageSequence.Iterator(Image.open(path)):
                        send_image(ser, frame)
                        time.sleep(GIF_FRAME_DWELL)
                else:
                    send_image(ser, Image.open(path))
                    # 拆成 0.5 秒一段檢查一次錄音資料，避免錄音(160000 bytes)在序列埠緩衝區
                    # 悶著等超過 5 秒都沒人讀，被系統緩衝區容量上限截斷
                    for _ in range(int(PHOTO_DWELL / 0.5)):
                        check_recording(ser)
                        time.sleep(0.5)
            except Exception as e:
                # 手機/截圖工具偶爾會把 HEIC 等 Pillow 讀不懂的檔案存成 .png/.jpg 副檔名，
                # 讀失敗就跳過這張，不要讓一張壞檔卡死整個輪播
                print(f"跳過無法讀取的圖片 {name}: {e}")


if __name__ == "__main__":
    main()
