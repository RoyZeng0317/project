# ILI9481 3.5吋面板 16-bit 並列(8080)驅動，接線:
# 2026-09 向左旋轉90度改直式輸出 320x480(原本橫向 480x320，改法見下方 MADCTL 註解)
# DB0~DB15=GP0~GP15, RS=GP16, WR=GP17, CS=GP18, RST=GP19
# 註解不可刪除
#
# 2026-09 改版：DB0~DB15+WR 改由 PIO(sm_id=4，PIO1 區塊，跟 bt_uart_rx.py 用的 PIO0
# sm_id=0 分開，避免搶同一顆 PIO)搭配 DMA 直接把整段緩衝區推給面板，取代原本逐像素
# 呼叫 mem32/Pin.value() 的 Python 迴圈，藉此消除「整張圖被逐像素刷出來」的視覺效果，
# 換圖速度也會大幅加快。這段 PIO/DMA 設定值(freq、bswap)是依規格書推算、還沒上機驗證，
# 燒錄後若畫面花掉/顏色不對，先試著調低 _sm 的 freq(例如 15_000_000)
from machine import Pin
from rp2 import PIO, StateMachine, asm_pio, DMA
import time

try:
    from typing_extensions import TYPE_CHECKING  # type: ignore
except ImportError:
    TYPE_CHECKING = False
if TYPE_CHECKING:
    # 只給編輯器做型別檢查用，Pico 實機執行時 TYPE_CHECKING 一定是 False、這段不會跑到；
    # out/pins/nop 這些是 @asm_pio 用位元碼分析出來的 DSL 關鍵字，不是真的函式呼叫，
    # 寫法照 bt_uart_rx.py 同樣的方式 import
    from rp2.asm_pio import *

_RS = Pin(16, Pin.OUT)
_CS = Pin(18, Pin.OUT)
_RST = Pin(19, Pin.OUT)


@asm_pio(out_init=[PIO.OUT_LOW] * 16, sideset_init=PIO.OUT_LOW,
          out_shiftdir=PIO.SHIFT_RIGHT, autopull=True, pull_thresh=16)
def _lcd_tx16():
    # 每次從 FIFO 取 16 位元資料同時輸出到 DB0~DB15，WR 用 sideset 自動配合每個指令
    # 翻轉一次(低電位時把資料放上匯流排、高電位時鎖存)，取代原本手動 Pin.value() 拉線
    out(pins, 16)   .side(0)
    nop()           .side(1)


_SM_ID = 4  # 4~7 是 PIO1 的 SM0~3，這裡用的是 PIO1 SM0
_sm = StateMachine(_SM_ID, _lcd_tx16, freq=25_000_000, out_base=Pin(0), sideset_base=Pin(17))
_sm.active(1)
_dma = DMA()
# pack_ctrl 的 treq_sel 只吃整數 DREQ 編號，不能直接傳 StateMachine 物件(會丟
# TypeError: can't convert StateMachine to int)，公式取自 RP2040 SDK pio_get_dreq()：
# PIO0 TX0~3=0~3，PIO1 TX0~3=8~11(即 pio編號*8 + PIO內的sm編號)
_TREQ_SEL = (_SM_ID // 4) * 8 + (_SM_ID % 4)


def _write_bus(value):
    # 單次寫入(初始化序列、CASET/PASET 這類低頻指令用)，直接塞進 PIO 的 FIFO，
    # FIFO 滿的話會自動卡住等待，指令這麼少不影響速度
    _sm.put(value)


def _blast(buf):
    # 整段緩衝區(w*h*2 bytes 以內)透過 DMA 一次推給 PIO，CPU 不用逐像素介入；
    # buf 沿用 to_rgb565() 既有的 (hi, lo) 大端排列，用 bswap 讓 DMA 幫忙把每 16 位元
    # 內的位元組序調整成 PIO 需要的順序，不用另外花 Python 時間重排
    n = len(buf)
    _dma.config(
        read=buf, write=_sm, count=n // 2,
        ctrl=_dma.pack_ctrl(size=1, inc_read=True, inc_write=False, bswap=True, treq_sel=_TREQ_SEL),
        trigger=True,
    )
    # 2026-09 診斷加註：這裡原本是無逾時死等，狀態機卡住不消耗 FIFO 時 DMA 會永遠等不到
    # 下一次 DREQ、CPU 就跟著整個卡死且不丟例外(截圖畫面卡住但序列埠沒錯誤訊息就是這裡)。
    # 加逾時把靜默卡死轉成明確報錯，方便定位是哪一段傳輸卡住；確認穩定後可以拿掉
    t0 = time.ticks_ms()
    while _dma.active():
        if time.ticks_diff(time.ticks_ms(), t0) > 1000:
            raise OSError("lcd dma timeout")


def write_cmd(cmd):
    _RS.value(0)
    _write_bus(cmd)


def write_data(data):
    _RS.value(1)
    _write_bus(data)


def reset():
    _RST.value(0)
    time.sleep_ms(20)
    _RST.value(1)
    time.sleep_ms(150)


# ILI9481 初始化序列(取自 TFT_eSPI 函式庫 ILI9481_INIT_1，經大量硬體驗證；0x11 Sleep Out 在 init() 內單獨處理)
_INIT_SEQ = (
    (0xD0, (0x07, 0x42, 0x18)),  # Power Setting
    (0xD1, (0x00, 0x07, 0x10)),  # VCOM Control
    (0xD2, (0x01, 0x02)),  # Power Setting for Normal Mode
    (0xC0, (0x10, 0x3B, 0x00, 0x02, 0x11)),  # Panel Driving Setting
    (0xC5, (0x03,)),  # Frame Rate
    (0xC8, (0x00, 0x32, 0x36, 0x45, 0x06, 0x16, 0x37, 0x75, 0x77, 0x54, 0x0C, 0x00)),  # Gamma
    (0x36, (0x48,)),  # MADCTL 直向顯示(2026-09 向左旋轉90度改版，原本 0x28 橫向 480x320)；
                       # 原本 0x68 文字左右鏡像(反字)，改 0x28 修正只翻轉左右，0x48 沿用同一組
                       # MX/BGR 只是拿掉 MV(橫向)位元、換成直向。若方向轉錯(轉成右轉或上下顛倒)，
                       # 改試 0x88(等同再多轉 180 度)；其他候選值: 0x08/0xA8/0xE8
    (0x3A, (0x55,)),  # 16-bit 色彩介面
)


def init():
    _CS.value(0)  # 面板只有一片，CS 全程拉低即可
    reset()
    write_cmd(0x11)  # Sleep Out
    time.sleep_ms(20)
    for cmd, params in _INIT_SEQ:
        write_cmd(cmd)
        for p in params:
            write_data(p)
    time.sleep_ms(120)
    write_cmd(0x29)  # Display On
    time.sleep_ms(25)


def set_window(x0, y0, x1, y1):
    write_cmd(0x2A)  # CASET
    write_data(x0 >> 8); write_data(x0 & 0xFF)
    write_data(x1 >> 8); write_data(x1 & 0xFF)
    write_cmd(0x2B)  # PASET
    write_data(y0 >> 8); write_data(y0 & 0xFF)
    write_data(y1 >> 8); write_data(y1 & 0xFF)
    write_cmd(0x2C)  # RAMWR


_CHUNK_BYTES = 2048  # 每段 DMA 搬運量(1024 個像素)，夠大能攤提 DMA 設定開銷、又不會佔太多 RAM


def draw_stream(x0, y0, w, h, fill_chunk):
    # fill_chunk(buf) 要把 buf(一個 memoryview)填滿最多 len(buf) bytes 資料，回傳實際
    # 填入的位元組數，0 代表沒有更多資料了；本地 flash 快取檔案可以直接傳 file 物件的
    # readinto 方法進來(見 main.py draw_cached)，藍牙/USB 這種一次只能讀一個位元組的
    # 來源則需要包一層轉接函式(見 main.py handle_message)。
    # 全程不整張圖存進 RAM，只搬 _CHUNK_BYTES 這麼大一段就透過 DMA 推給面板，避免大圖
    # 把記憶體塞爆，也讓 CPU 不用逐像素介入面板寫入
    set_window(x0, y0, x0 + w - 1, y0 + h - 1)
    _RS.value(1)
    remaining = w * h * 2
    buf = bytearray(min(_CHUNK_BYTES, remaining))
    while remaining > 0:
        view = memoryview(buf)[:min(len(buf), remaining)]
        got = fill_chunk(view)
        if not got:
            break
        _blast(view[:got] if got != len(view) else view)
        remaining -= got


def _solid_fill(x0, y0, x1, y1, color565):
    pair = bytes((color565 >> 8, color565 & 0xFF))

    def fill(buf):
        n = (len(buf) // 2) * 2
        buf[:n] = pair * (n // 2)
        return n

    draw_stream(x0, y0, x1 - x0 + 1, y1 - y0 + 1, fill)


def fill_screen(color565):
    _solid_fill(0, 0, 319, 479, color565)  # 320x480 直向(向左旋轉90度後)


def fill_rect(x0, y0, x1, y1, color565):
    # 局部填色(畫狀態列背景、清除小區塊用)，範圍可自訂，用法跟 fill_screen 一樣
    _solid_fill(x0, y0, x1, y1, color565)


if __name__ == "__main__":
    init()
    fill_screen(0xF800)  # 測試接線用：整片畫面填紅色，確認沒接錯線
