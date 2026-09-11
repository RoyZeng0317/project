# 用 PIO 軟體模擬 UART，接收 HC-06 藍牙模組傳來的資料
# 顯示器 16-bit 並列排線已經用掉 GP0~GP19，麥克風用掉 GP20~GP22，Pico 實際能接的
# 排針只剩 GP26/27/28 這 3 支(GP23/24/25/29 沒有接出排針)，且都不是硬體 UART 腳位，
# 所以改用 PIO 狀態機模擬。Pico 只需要「接收」手機/電腦傳來的資料、不用回傳，
# 因此只接 1 支腳(接 HC-06 的 TX 腳)：
#   HC-06 TX -> Pico GP27
#   HC-06 RX -> 不用接
#   HC-06 VCC -> 3.3V (或依模組規格接 5V)，GND -> GND
# PIO 寫法取自 MicroPython 官方範例 examples/rp2/pio_uart_rx.py 的 uart_rx_mini
# (只接收、不檢查 stop bit，換取程式碼簡短；一般短距離接線在合理鮑率下足夠穩定)
import time
from machine import Pin
from rp2 import PIO, StateMachine, asm_pio

try:
    from typing_extensions import TYPE_CHECKING  # type: ignore
except ImportError:
    TYPE_CHECKING = False
if TYPE_CHECKING:
    # 只給編輯器做型別檢查用，Pico 實機執行時 TYPE_CHECKING 一定是 False、這段不會跑到；
    # wait/set/jmp/label/in_/pins/pin/x/x_dec 這些是 @asm_pio 用位元碼分析出來的 DSL 關鍵字，
    # 不是真的函式呼叫，寫法照 typings/rp2/asm_pio_rp2040.pyi 裡指定的方式 import
    from rp2.asm_pio import *


@asm_pio(autopush=True, push_thresh=8, in_shiftdir=PIO.SHIFT_RIGHT, fifo_join=PIO.JOIN_RX)
def _uart_rx_mini():
    wait(0, pin, 0)  # 等待起始位元(線路被拉低)
    set(x, 7)              [10]  # 準備收 8 個位元，延遲到第一個資料位元的中央
    label("bitloop")
    in_(pins, 1)  # 取樣一個位元
    jmp(x_dec, "bitloop")  [6]  # 每輪剛好 8 個時脈週期


class BtUartRx:
    def __init__(self, pin=27, baud=9600, sm_id=0):
        # HC-06 出廠預設鮑率是 9600，若之後用 AT+BAUDx 改過鮑率，這裡要跟著改
        self._sm = StateMachine(
            sm_id, _uart_rx_mini, freq=8 * baud,
            in_base=Pin(pin, Pin.IN, Pin.PULL_UP),
        )
        self._sm.active(1)

    def available(self):
        # 目前 RX FIFO 裡累積了幾個位元組，非阻塞查詢用
        return self._sm.rx_fifo()

    def read_byte(self, timeout_ms=1000):
        # 沒資料時會卡住等待，要先用 available() 確認有資料再呼叫；GP27 沒接 HC-06 或
        # 被旁邊 LCD 排線雜訊干擾時，可能誤觸發訊息開頭卻沒有後續資料，這裡的阻塞讀取
        # 不受 Ctrl-C 影響，逾時就丟例外，避免整個主控台被卡死連 mpremote 都連不上
        t0 = time.ticks_ms()
        while self._sm.rx_fifo() == 0:
            if time.ticks_diff(time.ticks_ms(), t0) > timeout_ms:
                raise OSError("bt rx timeout")
        return self._sm.get() >> 24


if __name__ == "__main__":
    # 單獨測試用：手機藍牙終端機 App 連上 HC-06 後傳幾個文字過來，這裡會即時印出來
    print("BtUartRx 啟動，等待 HC-06 資料(GP27)...")
    rx = BtUartRx()
    while True:
        if rx.available():
            print(chr(rx.read_byte()), end="")
