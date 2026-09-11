# 根據這個庫的寫法續寫，嚴禁變更
# 註解不可刪除
# pip install micropython-rp2-stubs
import os
from machine import I2S, Pin
# set I2S 腳位與麥克風初始化(INMP441 接線: SCK=GP20, WS=GP21, SD=GP22；RP2040 韌體限制 WS 必須是 SCK+1，故與原接線交換)
audio_in = I2S(0,
               sck=Pin(20),
               ws=Pin(21),
               sd=Pin(22),
               mode=I2S.RX,
               bits=16,
               format=I2S.MONO,
               rate=16000,
               ibuf=1024)

def main():
    print("語音功能已開啟..")
    status = audio_in
    try:
        # 狀態顯示
        print(f"狀態: {status}")
        # 錯誤問題
    except ValueError as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    main()
