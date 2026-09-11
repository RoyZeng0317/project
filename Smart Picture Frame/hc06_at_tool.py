# pip install pyserial
# 直接接 USB-TTL 燒錄器到 HC-06(不透過藍牙)送 AT 指令，查詢/重設配對密碼用
# 接線：USB-TTL TXD -> HC-06 RXD，USB-TTL RXD -> HC-06 TXD，GND -> GND，VCC 依模組規格接 3.3V/5V
# 注意：HC-06 只有在「未連線」狀態(燈快速閃爍)才會進入 AT 模式，指令不用加換行；
# 測試時先拔掉跟 Pico GP27 的接線，避免同時被兩邊拉電位干擾
import serial, time

PORT = "COM10"  # 依 USB-TTL 轉接器在裝置管理員裡顯示的 COM 埠修改
BAUD = 9600     # HC-06 出廠預設鮑率，AT 模式跟資料模式共用同一個鮑率

def send(ser, cmd):
    # 原廠 HC-06 指令不加換行；但部分韌體版本的「設定類」指令要求位元組數精確比對，
    # 多送 \r\n 會比對失敗而不回應，所以先試不加換行，沒反應再補送一次加換行的版本
    for suffix in (b"", b"\r\n"):
        ser.reset_input_buffer()
        ser.write(cmd.encode() + suffix)
        time.sleep(0.5)  # 部分指令(如改密碼)處理較慢，太快讀取會讀到空的
        resp = ser.read(64)
        if resp:
            return resp.decode(errors="replace")
    return None


ser = serial.Serial(PORT, BAUD, timeout=2)
print("已連上 " + PORT + "，輸入 AT 指令(例如 AT / AT+VERSION / AT+PIN1234)，Ctrl+C 結束")
while True:
    cmd = input("> ").strip()
    print(send(ser, cmd) or "(沒有回應)")
