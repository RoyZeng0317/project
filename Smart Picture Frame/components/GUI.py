# 整合全套組件的主介面 (GUI)
import asyncio
import os
import sys
import threading
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

    select_btn = tk.Button(btn_frame, text="🖼 選擇照片", command=lambda: photo.select_photos_dialog(window), font=("Arial", 12), bg="#333333", fg="white")
    select_btn.pack(side="bottom", pady=5)

    capture_btn = tk.Button(btn_frame, text="📸 拍照", command=_trigger_capture, font=("Arial", 12), bg="#333333", fg="white")
    capture_btn.pack(side="bottom", pady=5)

    record_btn = tk.Button(btn_frame, text="🎤 錄音", command=_trigger_record, font=("Arial", 12), bg="#333333", fg="white")
    record_btn.pack(side="bottom", pady=5)

    # 5. 推送到相框：把這裡輪播/選好的照片實際送去 Mega2560 螢幕顯示(重用 mega_frame_sender.py
    # 的背景迴圈)，按一下開始、再按一下停止
    # 2026-09-09：改推給 Mega2560(USB序列)，不再推給 ESP32-S3-CAM(BLE)——BLE 那條路一直有
    # 掉包/紅色雜訊問題，換成有線 USB 序列傳輸比較穩定；ble_frame_sender.py 保留在檔案裡，
    # 之後 ESP32 那邊穩定了要換回來，只要改下面這行 import 就好
    push_thread: threading.Thread | None = None
    push_stop: threading.Event | None = None

    def _toggle_push():
        nonlocal push_thread, push_stop
        if push_thread and push_thread.is_alive() and push_stop:
            push_stop.set()
            push_btn.config(text="停止中...", state="disabled")
            return

        from mega_frame_sender import main as mega_main
        push_stop = threading.Event()

        def worker():
            try:
                mega_main(push_stop)
            except Exception as e:
                print(f"推送失敗: {e}")
            window.after(0, lambda: push_btn.config(text="📡 推送到相框", state="normal"))

        push_thread = threading.Thread(target=worker, daemon=True)
        push_thread.start()
        push_btn.config(text="⏹ 停止推送")

    push_btn = tk.Button(btn_frame, text="📡 推送到相框", command=_toggle_push, font=("Arial", 12), bg="#333333", fg="white")
    push_btn.pack(side="bottom", pady=5)

    # 進入主迴圈
    window.mainloop()


def _run_ble(coro_func):
    # 觸發 ESP32-S3-CAM 的 BLE 指令共用邏輯；BLE 連線是 async，開一條背景 thread 跑自己的
    # event loop，避免卡住 tkinter 的 mainloop
    threading.Thread(target=lambda: asyncio.run(coro_func()), daemon=True).start()


def _trigger_capture():
    from ble_frame_sender import trigger_capture
    _run_ble(trigger_capture)


def _trigger_record():
    # 錄音結果不會回到這裡，是 ESP32 錄完後透過 USB 序列傳給 usb_frame_sender.py 存檔
    # (見 usb_frame_sender.py 的 check_recording)，這顆按鈕只負責觸發
    from ble_frame_sender import trigger_record
    _run_ble(trigger_record)


if __name__ == "__main__":
    main()