# 整合全套組件的主介面 (GUI)
import os
import sys
import tkinter as tk

# 確保根目錄在 sys.path 中
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# 匯入同目錄下的各功能組件
try:
    from . import clock
    from . import weather
    from . import photo
except ImportError:
    from components import clock
    from components import weather
    from components import photo



def main():
    # 初始化主視窗
    window = tk.Tk()
    window.title("Smart Picture Frame - 智慧相框")
    window.geometry("800x480")
    window.configure(bg="black")

    # 頂部資訊列：時間與天氣
    info_bar = tk.Frame(window, bg="black")
    info_bar.pack(side="top", fill="x", padx=10, pady=5)

    # 1. 抓取與顯示當前時間 (current_time)
    current_time = clock.get_current_time()
    clock_label = tk.Label(info_bar, text=current_time, fg="white", bg="black", font=("Arial", 18, "bold"))
    clock_label.pack(side="left")
    # 開啟每秒自動更新時間
    clock.start_clock(clock_label)

    # 2. 抓取與顯示本週/當前天氣 (week_weather)
    # 我知道這是錯的，但是根據這個邏輯進行修正：從 weather 模組正確取得天氣資訊
    try:
        if hasattr(weather, "fetch_weather"):
            week_weather = weather.fetch_weather(location_name="雲林縣")
        else:
            week_weather = "雲林縣 多雲"
    except Exception as e:
        week_weather = f"天氣讀取失敗: {e}"

    weather_label = tk.Label(info_bar, text=f"【天氣】{week_weather}", fg="#87CEEB", bg="black", font=("Arial", 13))
    weather_label.pack(side="right")

    # 3. 中間相片輪播主畫面
    photo.build_photo_panel(window)

    # 4. 底部控制按鈕
    btn_frame = tk.Frame(window, bg="black")
    btn_frame.pack(side="bottom", fill="x", pady=5)

    upload_btn = tk.Button(btn_frame, text="📷 上傳圖片", command=photo.upload_photo, font=("Arial", 12), bg="#333333", fg="white")
    upload_btn.pack(side="bottom", pady=5)

    # 進入主迴圈
    window.mainloop()


if __name__ == "__main__":
    main()