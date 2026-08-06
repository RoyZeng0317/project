import os
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from . import clock
    from . import weather
    from . import photo
except ImportError:
    from components import clock
    from components import weather
    from components import photo


# 保留 pi 與 ESP32 的面板驅動
驅動 = ""

# python 視窗
import tkinter as tk

window = tk.Tk()
window.title("Smart Picture Frame")
window.geometry("800x480")

# 頂部資訊列：時鐘 + 天氣
info_bar = tk.Frame(window, bg="black")
info_bar.pack(side="top", fill="x")

clock_label = tk.Label(info_bar, fg="white", bg="black", font=("Arial", 20))
clock_label.pack(side="left", padx=10)
clock.start_clock(clock_label)  # 每秒自動更新時間

weather_label = tk.Label(info_bar, fg="white", bg="black", font=("Arial", 16))
weather_label.pack(side="right", padx=10)


def refresh_weather():
    # 每 30 分鐘重新查一次天氣；GPS 定位 + 呼叫氣象局 API 都偏慢，不需要太頻繁執行
    try:
        lat, lon = weather.get_location()
        city = weather.get_city_name(lat, lon)
        pop_list = weather.get_weekly_pop(city)
        _, pop = pop_list[0]
        weather_label.config(text=f"{city} {weather.rain_analysis(pop)}")
    except Exception as e:
        weather_label.config(text="天氣資料取得失敗")
        print(e)
    window.after(30 * 60 * 1000, refresh_weather)


refresh_weather()

# 中間相片輪播主畫面
photo.build_photo_panel(window)

# 底部上傳按鈕
upload_btn = tk.Button(window, text="上傳圖片", command=photo.upload_photo)
upload_btn.pack(side="bottom", pady=5)

window.mainloop()
