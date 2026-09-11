# ILI9481 面板硬體自檢，對應 Mega2560 端 MEGA2560_test.ino 的測試流程(RGB自檢->
# 幾何圖形->彩虹色帶->計數器刷屏)，只用 ili9481_parallel.py 既有公開函式，不碰驅動內部。
# 不會覆蓋 main.py，用法(不燒進 flash，跑完可直接看畫面確認接線，中斷後 Pico 會回到 main.py)：
#   mpremote connect COM6 run "Raspberry pi pico/tft_test.py"
# 還沒有實機測試過，畫面異常時先確認 lcd.init() 有無報錯
import time
import ili9481_parallel as lcd
import font8x8

BLACK, RED, GREEN, BLUE, CYAN, WHITE = 0x0000, 0xF800, 0x07E0, 0x001F, 0x07FF, 0xFFFF
W, H = 320, 480  # 直向(驅動已向左旋轉90度)


def rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def draw_rect(x0, y0, x1, y1, color, t=3):
    lcd.fill_rect(x0, y0, x1, y0 + t - 1, color)
    lcd.fill_rect(x0, y1 - t + 1, x1, y1, color)
    lcd.fill_rect(x0, y0, x0 + t - 1, y1, color)
    lcd.fill_rect(x1 - t + 1, y0, x1, y1, color)


def fill_circle(cx, cy, r, color):
    for dy in range(-r, r + 1):
        dx = int((r * r - dy * dy) ** 0.5)
        lcd.fill_rect(cx - dx, cy + dy, cx + dx, cy + dy, color)


lcd.init()

# 1. RGB 自檢：滿版紅綠藍，確認有無死像素/斷線
for c in (RED, GREEN, BLUE):
    lcd.fill_screen(c)
    time.sleep_ms(500)

# 2. 測試主畫面
lcd.fill_screen(BLACK)
draw_rect(5, 5, W - 6, H - 6, CYAN)
lcd.fill_rect(30, 40, 130, 140, RED)
fill_circle(W // 2, 190, 60, GREEN)
draw_rect(W - 130, 40, W - 30, 140, BLUE)

# 3. 彩虹色帶：測試色彩連續度
for i in range(W - 40):
    x = 20 + i
    lcd.fill_rect(x, 260, x, 300, rgb565(i % 256, (i * 2) % 256, (i * 3) % 256))

# 4. 計數器刷屏測試
count = 0
while True:
    font8x8.draw_text(lcd, 20, 340, "%03d" % count, GREEN, BLACK, scale=4)
    count = (count + 1) % 1000
    time.sleep_ms(200)
