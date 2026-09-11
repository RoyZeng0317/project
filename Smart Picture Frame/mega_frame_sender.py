# 電腦端：透過 USB 序列埠傳照片/天氣/時間給 Mega2560(MEGA2560_test.ino)。
# 協定 tag 格式('I'/'T'/'W')跟 bt_frame_sender.py 完全一樣，但畫面尺寸不同——Mega 這片是橫向
# 480x320(見 MEGA2560_test.ino 的 SCREEN_ROTATION=1)，狀態列 BAR_H=24，可顯示區 480x296，
# 跟 Pico/ESP32-S3-CAM 用的直向 320x460 不一樣，所以不能直接沿用 bt_frame_sender.py 的 CANVAS，
# 另外開一份；像素轉換演算法(to_rgb565)保持一致，Mega 端 pushPixelsBytes() 一樣是「高位元組在前」
# 使用前先接上 USB 線，到「裝置管理員 > 連接埠(COM與LPT)」找到板子的
# 「USB 序列裝置(COMx)」，填入下面的 MEGA_PORT
import re
import time
from PIL import Image, ImageSequence
import serial
from components import photo, weather

MEGA_PORT = "COM8"       # 裝置管理員顯示為 "Arduino Mega 2560 (COM8)"
BAUD = 500000             # 2026-09-09：切換速度已經改用本地 TF 卡輪播解決(見 mega_flash_sd.py +
                          # MEGA2560_test.ino 的 scanLocalPhotos/showLocalPhoto)，這支程式現在只負責
                          # 天氣/時間/偶爾一張新照片這種低頻即時推播，不用衝高鮑率；
                          # 曾試過 2000000，這片板子的 USB-序列晶片撐不住會掉包，500000 實測穩定；
                          # 需與 MEGA2560_test.ino 的 SERIAL_BAUD 一致
CANVAS = (480, 296)       # 對應 Mega 面板扣掉狀態列後的可顯示區域(480 x (320 - BAR_H))
WEATHER_LOCATION = "雲林縣"
CWA_API_KEY = ""          # 同 components/weather.py，需先到 https://opendata.cwa.gov.tw 申請
WEATHER_INTERVAL = 1800   # 天氣多久重查一次(秒)
TIME_INTERVAL = 60        # 時間多久重新校正一次(秒)，Mega 是軟體時鐘，重開機/斷電/重燒都會歸零
PHOTO_DWELL = 5           # 靜態相片每張顯示秒數
GIF_FRAME_DWELL = 0.15    # GIF 動畫每格間隔秒數


def to_rgb565(img):
    # 等比縮放後置中貼到黑底畫布，避免變形；再逐像素轉成 RGB565 大端 bytes，邏輯照抄 bt_frame_sender.py
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


def send_image(ser, img, name="(unnamed)"):
    # 2026-09-09：原本送完直接回傳，靠 PHOTO_DWELL(5秒)硬等，但115200鮑率光傳一張圖就要
    # 25秒左右，圖片一直堆積在緩衝區、畫面就像沒在切換；改成主動等韌體回傳
    # "[ACK] Image OK"(見 MEGA2560_test.ino 的 handleImagePacket)，確定這張真的收完再送下一張
    # 2026-09-09：成功也印一行，之前只印失敗，遠端看 log 完全分不出「正常切換中」跟「卡住」
    w, h = CANVAS
    ser.reset_input_buffer()  # 清掉開機訊息等舊資料，避免誤讀成這次的回應
    ser.write(b"I" + bytes([w >> 8, w & 0xFF, h >> 8, h & 0xFF]) + to_rgb565(img))
    reply = ser.readline().decode(errors="replace").strip()
    if reply.startswith("[ACK]"):
        print(f"已顯示: {name}")
    else:
        print(f"圖片傳輸可能失敗({name}): {reply or '(逾時無回應)'}")


def send_weather(ser):
    text = weather.fetch_weather(WEATHER_LOCATION, CWA_API_KEY)
    m = re.search(r"(\d+)~(\d+).+?(\d+)%", text)
    ascii_text = f"{m.group(1)}-{m.group(2)}C {m.group(3)}%" if m else "NO DATA"
    payload = ascii_text.encode()
    ser.write(b"W" + bytes([len(payload)]) + payload)


def send_time(ser):
    now = time.localtime()
    ser.write(b"T" + bytes([now.tm_year >> 8, now.tm_year & 0xFF, now.tm_mon, now.tm_mday,
                             now.tm_hour, now.tm_min, now.tm_sec]))


def main(stop_event=None):
    # stop_event: components/GUI.py 的「推送到相框」按鈕用來喊停(threading.Event)；
    # 獨立執行(python mega_frame_sender.py)不傳就維持永遠跑下去的行為
    ser = serial.Serial(MEGA_PORT, BAUD, timeout=10)  # 留夠餘裕等 [ACK]，即使鮑率不對/接錯線也不會卡死
    time.sleep(2)  # 開序列埠會觸發 Mega 自動重開機，沒等開機跑完就送圖，第一張會被開機橫幅蓋掉、傳輸中斷
    ser.reset_input_buffer()
    last_time = last_weather = 0

    def resync():
        # 2026-09-09：原本只在「跑完整個 photos/ 資料夾一輪」後才檢查要不要校時/查天氣，
        # 照片一多或剛好卡在大 GIF，實際校時間隔會遠超過 TIME_INTERVAL，Mega 端時鐘越飄越多；
        # 改成每張圖、每個 GIF 格傳送前都檢查一次，確保不管卡在哪張圖都準時校正
        nonlocal last_time, last_weather
        if time.time() - last_time > TIME_INTERVAL:
            send_time(ser)
            last_time = time.time()
        if time.time() - last_weather > WEATHER_INTERVAL:
            send_weather(ser)
            last_weather = time.time()

    try:
        while not (stop_event and stop_event.is_set()):
            for name in photo.list_photos():
                if stop_event and stop_event.is_set():
                    break
                resync()
                path = f"{photo.path}/{name}"
                try:
                    if name.lower().endswith(".gif"):
                        for frame in ImageSequence.Iterator(Image.open(path)):
                            resync()
                            send_image(ser, frame, name)
                            time.sleep(GIF_FRAME_DWELL)
                    else:
                        send_image(ser, Image.open(path), name)
                        time.sleep(PHOTO_DWELL)
                except Exception as e:
                    # 遇到損毀或 Pillow 仍讀不懂的檔案，讀失敗就跳過這張，不要讓一張壞檔卡死整個輪播
                    print(f"跳過無法讀取的圖片 {name}: {e}")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
