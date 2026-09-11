# 喇叭出聲測試(第一步，先驗證接線)：手邊電阻是棕黑黃金=100k歐姆(比理想值大，聲音會較小聲，
# 但先求驗證接線)。電晶體建議用 C1815(比 9013 增益高，100k 電阻下聲音較明顯)：
#   GP28 --[100k電阻]-- C1815 基極(B)
#   3V3  -- 喇叭+  喇叭- -- C1815 集極(C)
#   C1815 射極(E) -- GND
# GPIO 只驅動基極(電流僅 uA 等級)，喇叭實際電流由 3V3 經電晶體供應，不流過 GPIO，避免燒壞腳位。
# 注意 C1815(Toshiba TO-92) 平面朝自己時接腳順序是 E-C-B(跟 9013 的 E-B-C 不同)，
# 接之前務必核對電晶體上印的型號跟實際兩側平面/圓弧方向，或用三用電表核對，避免 B/C 接反。
# 用 mpremote/Thonny 單獨執行這支檔案，聽到 3 聲短嗶(即使很小聲)就代表接線正確。
from machine import Pin, PWM
import time

spk = PWM(Pin(28))
spk.freq(1000)
for _ in range(3):
    spk.duty_u16(32768)
    time.sleep(0.2)
    spk.duty_u16(0)
    time.sleep(0.2)
spk.deinit()
