# 用 Pico 原生 USB 序列埠(CDC)接收電腦端 usb_frame_sender.py 透過 USB 排線直接送來的資料，
# 跟 bt_uart_rx.py 走藍牙 UART 是同一套協定、只是換一條實體通道，本來就要接 USB 供電，
# 不會多佔用任何 GPIO 排針(Pico 背面的 SWDIO/SWCLK 是晶片固定的除錯腳位，沒辦法拿來重配成
# UART，所以才改走 USB 序列埠這條本來就存在的通道)
# 影像資料流是二進位內容，剛好出現 0x03 這個位元組時 USB 序列埠預設會誤判成 Ctrl-C
# 中斷程式，所以讀取二進位訊息期間要暫時關掉這個行為(見 main.py 呼叫 kbd_intr 的地方)，
# 平常閒置時保持開啟，這樣電腦端才能隨時用 mpremote 的 Ctrl-C 拿回 REPL 重新燒錄
import sys
import select

_poll = select.poll()
_poll.register(sys.stdin, select.POLLIN)


class UsbUartRx:
    def available(self):
        # 非阻塞查詢 USB 序列埠目前有沒有資料可讀，介面跟 BtUartRx 一致方便 main.py 共用
        return _poll.poll(0)

    def read_byte(self, timeout_ms=1000):
        # 沒資料時會卡住等待，要先用 available() 確認有資料再呼叫；訊息讀到一半若對方斷線、
        # 剩下的位元組遲遲不來，這裡逾時就丟例外，讓 main.py 能恢復 kbd_intr 而不是永遠卡住
        if not _poll.poll(timeout_ms):
            raise OSError("usb rx timeout")
        return sys.stdin.buffer.read(1)[0]

    def read_into(self, buf, timeout_ms=1000):
        # 圖片資料量大(一張 480x300 圖有 28.8 萬 bytes)，改一次讀整段 buf 取代 read_byte
        # 逐位元組呼叫；逐位元組會讓 MicroPython 累積幾十萬次 poll+read 系統呼叫，速度追不上
        # USB 送資料的速度，導致中途逾時、圖片顯示一下子就斷掉不再更新，改整段讀就沒這問題
        n = 0
        while n < len(buf):
            if not _poll.poll(timeout_ms):
                raise OSError("usb rx timeout")
            got = sys.stdin.buffer.readinto(memoryview(buf)[n:])  # type: ignore
            if not got:
                raise OSError("usb rx closed")
            n += got
        return n


if __name__ == "__main__":
    # 單獨測試用：電腦端開終端機軟體對 Pico 的 USB 序列埠打字，這裡會即時印出來
    print("UsbUartRx 啟動，等待 USB 序列埠資料...")
    rx = UsbUartRx()
    while True:
        if rx.available():
            print(chr(rx.read_byte()), end="")
