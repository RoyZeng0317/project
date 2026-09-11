# Pico 開機後自動執行的主程式：接收 HC-06 藍牙或 USB 有線傳來的天氣/時間/圖片並顯示在螢幕上，
# 開機時也會先播放已預先燒進內建 flash 的本地快取圖(見 pico_flash_photos.py)當預設畫面，
# 收到任何即時資料時會立刻覆蓋播放，藍牙/USB 兩種來源同時監聽、哪邊先到就處理哪邊
# 通訊協定(電腦端 bt_frame_sender.py / usb_frame_sender.py 對應送出，順序皆為 big-endian)：
#   'W' + 1 byte 長度 + ascii 文字             -> 更新畫面右上角天氣文字
#   'T' + 2 byte 年 + 月1 + 日1 + 時1 + 分1 + 秒1 -> 校正時鐘(Pico 內建軟體時鐘，斷電歸零)
#   'I' + 2 byte 寬 + 2 byte 高 + RGB565 原始像素 -> 在狀態列下方顯示一張圖(相片或影片其中一格)
import os
import time
import micropython
from machine import RTC
import ili9481_parallel as tft
import font8x8
from bt_uart_rx import BtUartRx
from usb_uart_rx import UsbUartRx

WHITE, BLACK = 0xFFFF, 0x0000
SCALE = 2
BAR_H = 8 * SCALE + 4  # 狀態列高度，下方留給圖片(對應電腦端 CANVAS 高度 = 480 - BAR_H)
CANVAS_W, CANVAS_H = 320, 480 - BAR_H  # 2026-09 向左旋轉90度改直式；跟電腦端 bt_frame_sender.py 的 CANVAS 常數保持一致
PHOTO_DWELL = 5  # 本地快取圖每張顯示秒數，跟電腦端 PHOTO_DWELL 常數一致

tft.init()
rx_bt = BtUartRx(pin=27, baud=115200)  # 需先用 hc06_at_tool.py 送 AT+BAUD8 把 HC-06 改成同樣鮑率
rx_usb = UsbUartRx()
rtc = RTC()
weather_text = ""


def read_exact(read_byte, n):
    return bytes(read_byte() for _ in range(n))


def _byte_fill(read_byte):
    # 藍牙/USB 只能一次讀一個位元組，包成 tft.draw_stream 要的 fill_chunk(buf)->已填位元組數 介面
    def fill(buf):
        for i in range(len(buf)):
            buf[i] = read_byte()
        return len(buf)
    return fill


def handle_message(read_byte, fill_chunk=None):
    # 不管資料是從藍牙還是 USB 來的，都是同一套協定，共用這個函式解析；圖片資料改用
    # fill_chunk 整段讀(USB 傳 rx_usb.read_into，比逐位元組快很多，避免中途逾時、畫面
    # 顯示一下子就斷掉)，藍牙沒有整段介面(PIO FIFO 限制)，不傳 fill_chunk 時沿用 _byte_fill
    global weather_text
    tag = read_byte()
    if tag == ord("W"):
        n = read_byte()
        weather_text = read_exact(read_byte, n).decode()
        redraw_bar()
    elif tag == ord("T"):
        b = read_exact(read_byte, 7)
        rtc.datetime(((b[0] << 8) | b[1], b[2], b[3], 0, b[4], b[5], b[6], 0))
        redraw_bar()
    elif tag == ord("I"):
        b = read_exact(read_byte, 4)
        w, h = (b[0] << 8) | b[1], (b[2] << 8) | b[3]
        tft.draw_stream(0, BAR_H, w, h, fill_chunk or _byte_fill(read_byte))


def draw_cached(path):
    # 播放燒在本地 flash 的圖(固定 CANVAS_W x CANVAS_H 的原始 RGB565)，file 物件的 readinto
    # 剛好符合 draw_stream 要的 fill_chunk(buf)->已填位元組數 介面，一次搬一段直接交給 DMA，
    # 不用像以前那樣逐位元組跑 Python 迴圈，也不用把整張圖(約 288000 bytes)一次讀進 RAM
    with open(path, "rb") as f:
        tft.draw_stream(0, BAR_H, CANVAS_W, CANVAS_H, f.readinto)


try:
    cached_photos = ["/photos_cache/" + f for f in sorted(os.listdir("/photos_cache")) if f.endswith(".bin")]
except OSError:
    cached_photos = []  # 還沒燒過本地快取圖，正常情況，等即時資料就好
photo_idx = 0


def redraw_bar():
    _, mo, d, _, h, mi, s, _ = rtc.datetime()
    clock_str = "{:02d}:{:02d}:{:02d}".format(h, mi, s)
    tft.fill_rect(0, 0, 319, BAR_H - 1, BLACK)
    font8x8.draw_text(tft, 4, 2, clock_str, WHITE, BLACK, SCALE)
    x = 320 - 4 - font8x8.text_width(weather_text, SCALE)
    font8x8.draw_text(tft, x, 2, weather_text, WHITE, BLACK, SCALE)


redraw_bar()
last_tick = time.ticks_ms()
last_photo_tick = time.ticks_ms()
while True:
    # 暫時診斷用：HC-06 模組故障還沒換新的接上，GP27 目前浮接，會被旁邊 LCD 排線雜訊誤觸發，
    # 導致 rx_bt.available() 幾乎一直回傳有資料、主迴圈卡在下面這個分支等後續資料，永遠輪不到
    # 下面的相片/時鐘更新；換新模組接上 GP27 後拿掉 "False and " 這幾個字就好
    if False and rx_bt.available():
        # GP27 雜訊誤觸發訊息開頭卻沒有後續資料時，read_byte 逾時(見 bt_uart_rx.py)會丟例外，
        # 接住讓迴圈繼續跑，不然沒接 Ctrl-C 保護的這條路徑會直接卡死整個主控台
        try:
            handle_message(rx_bt.read_byte)
        except OSError:
            pass
    elif rx_usb.available():
        # 讀 USB 二進位訊息期間關掉 Ctrl-C，避免內容剛好出現 0x03 誤觸中斷；讀完立刻恢復，
        # 平常閒置時保持能用 Ctrl-C，電腦端才能隨時用 mpremote 重新連上 REPL 燒錄新程式。
        # 用 try/finally 包住：訊息讀到一半卡住逾時(見 usb_uart_rx.py)也保證恢復 Ctrl-C，
        # 不然 mpremote 會抓不到 raw repl
        micropython.kbd_intr(-1)
        try:
            handle_message(rx_usb.read_byte, rx_usb.read_into)
        except OSError:
            pass
        finally:
            micropython.kbd_intr(3)
    else:
        now = time.ticks_ms()
        # 暫時診斷用：關閉這裡每秒的狀態列重繪，測試圖片消失是否跟這個有關，
        # 確認完問題原因後要復原(拿掉這行 if False and 就好)
        if False and time.ticks_diff(now, last_tick) >= 1000:
            last_tick = now
            redraw_bar()
        if cached_photos and time.ticks_diff(now, last_photo_tick) >= PHOTO_DWELL * 1000:
            last_photo_tick = now
            draw_cached(cached_photos[photo_idx % len(cached_photos)])
            photo_idx += 1
        time.sleep_ms(20)
