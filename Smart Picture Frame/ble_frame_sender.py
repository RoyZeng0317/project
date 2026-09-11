# 電腦端：透過 ESP32-S3 內建 BLE(取代 Pico 版外接的 HC-06)傳天氣/時間/圖片，協定
# 跟 bt_frame_sender.py/usb_frame_sender.py 完全一樣(對應韌體 ESP32-S3-CAM/SmartFrame/protocol.cpp)，
# 圖片轉檔邏輯(to_rgb565)直接從 bt_frame_sender.py 匯入重用，避免同一段像素轉換邏輯寫兩次；
# 但 bleak 是 async 函式庫，沒辦法直接沿用 bt_frame_sender.py 裡 ser.write() 那種同步阻塞寫法，
# 送資料的部分另外用 async 寫一份，每次 write_gatt_char 都切成不超過 CHUNK 的大小送出
# 使用前：pip install bleak，並確認 ESP32-S3 韌體已開機廣播(裝置名稱 SmartFrame-ESP32S3)
import asyncio
import re
import time
from bleak import BleakClient, BleakScanner
from PIL import Image, ImageSequence
from components import photo, weather
from bt_frame_sender import to_rgb565, CANVAS, WEATHER_LOCATION, CWA_API_KEY, \
    WEATHER_INTERVAL, TIME_INTERVAL, PHOTO_DWELL, GIF_FRAME_DWELL

DEVICE_NAME = "SmartFrame-ESP32S3"
CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # 需與韌體 ble_service.cpp 的 CHARACTERISTIC_UUID 一致
CHUNK = 180  # 留一點餘裕給 BLE 封包表頭，實際可用大小依雙方協商到的 MTU 而定，之後可再調大


async def _send(client, payload: bytes):
    # 2026-09-09：response=True(等對方確認) 在 Windows 這邊會直接炸(WinError -2147023673)，
    # 連線後第一個封包就炸掉，代表不是資料量大/擁塞的問題，是這個 Windows BLE 堆疊搭配
    # 這顆 ESP32 的 GATT 特徵值本來就不支援穩定的「等確認寫入」，改回 response=False，
    # 但加封包間隔(避免寫入佇列塞爆，這才是實際上常見的掉包原因)+失敗重試，換一種方式補可靠性
    for i in range(0, len(payload), CHUNK):
        chunk = payload[i:i + CHUNK]
        for attempt in range(3):
            try:
                await client.write_gatt_char(CHAR_UUID, chunk, response=False)
                break
            except Exception as e:
                if attempt == 2:
                    raise
                print(f"封包送失敗，重試中({attempt + 1}/3): {e}")
                await asyncio.sleep(0.05)
        await asyncio.sleep(0.004)


async def send_image(client, img):
    w, h = CANVAS
    await _send(client, b"I" + bytes([w >> 8, w & 0xFF, h >> 8, h & 0xFF]) + to_rgb565(img))


async def send_weather(client):
    text = weather.fetch_weather(WEATHER_LOCATION, CWA_API_KEY)
    m = re.search(r"(\d+)~(\d+).+?(\d+)%", text)
    ascii_text = f"{m.group(1)}-{m.group(2)}C {m.group(3)}%" if m else "NO DATA"
    payload = ascii_text.encode()
    await _send(client, b"W" + bytes([len(payload)]) + payload)


async def send_time(client):
    now = time.localtime()
    await _send(client, b"T" + bytes([now.tm_year >> 8, now.tm_year & 0xFF, now.tm_mon, now.tm_mday,
                                       now.tm_hour, now.tm_min, now.tm_sec]))


async def send_capture(client):
    # 觸發 ESP32 本機拍照顯示，只送 1 byte 指令，不受 BLE 頻寬限制(對應韌體 'C' tag)
    await _send(client, b"C")


async def send_record(client):
    # 觸發 ESP32 錄音(固定5秒)，一樣只送 1 byte 指令(對應韌體 'R' tag)；
    # 錄音結果資料量大，韌體固定只透過 USB 序列傳回(見 usb_frame_sender.py 的 check_recording)，
    # 不會透過這個 BLE 連線收到，所以這裡送出指令後就直接返回，不等結果
    await _send(client, b"R")


async def trigger_capture():
    # 給 components/GUI.py 的「拍照」按鈕用：單次連線送出拍照指令就斷線，不用像 main() 一樣長駐
    device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10)
    if not device:
        print(f"找不到裝置 {DEVICE_NAME}")
        return
    async with BleakClient(device) as client:
        await send_capture(client)


async def trigger_record():
    # 給 components/GUI.py 的「錄音」按鈕用，用法比照 trigger_capture()
    device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10)
    if not device:
        print(f"找不到裝置 {DEVICE_NAME}")
        return
    async with BleakClient(device) as client:
        await send_record(client)


async def main(stop_event=None):
    # stop_event: components/GUI.py 的「推送到相框」按鈕用來喊停(threading.Event)；
    # 獨立執行(python ble_frame_sender.py)不傳就維持原本永遠跑下去的行為
    device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10)
    if not device:
        print(f"找不到裝置 {DEVICE_NAME}，確認 ESP32-S3 已開機且在範圍內")
        return

    async with BleakClient(device) as client:
        last_time = last_weather = 0
        while not (stop_event and stop_event.is_set()):
            if time.time() - last_time > TIME_INTERVAL:
                await send_time(client)
                last_time = time.time()

            if time.time() - last_weather > WEATHER_INTERVAL:
                await send_weather(client)
                last_weather = time.time()

            # 2026-09-09：改回一律送資料夾全部照片，不要用 get_selected()——那份手動選片清單(最多3張)
            # 是為 Pico 版 flash 容量上限設計的，ESP32-S3-CAM 這邊是即時 BLE 串流不佔本機儲存空間，
            # 沒有那個限制；套用選片清單只會讓手機上傳的新照片被忽略(沒被加進清單就永遠不會推送)
            for name in photo.list_photos():
                if stop_event and stop_event.is_set():
                    break
                path = f"{photo.path}/{name}"
                try:
                    if name.lower().endswith(".gif"):
                        for frame in ImageSequence.Iterator(Image.open(path)):
                            await send_image(client, frame)
                            await asyncio.sleep(GIF_FRAME_DWELL)
                    else:
                        await send_image(client, Image.open(path))
                        await asyncio.sleep(PHOTO_DWELL)
                except Exception as e:
                    # 手機/截圖工具偶爾會把 HEIC 等 Pillow 讀不懂的檔案存成 .png/.jpg 副檔名，
                    # 讀失敗就跳過這張，不要讓一張壞檔卡死整個輪播
                    print(f"跳過無法讀取的圖片 {name}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
