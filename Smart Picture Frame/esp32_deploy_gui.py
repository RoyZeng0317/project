# 開發用小工具：GUI 版一鍵編譯+燒錄 ESP32-S3-CAM/SmartFrame 韌體，選 COM 埠後按一下按鈕就好，
# 不用再手動打 python esp32_deploy.py COM6；燒錄邏輯完全重用 esp32_deploy.py，不重寫一份，
# 介面架構也直接沿用 pico_deploy_gui.py 同一套 log 佇列寫法。
# 首次執行會自動裝 esp32 開發板套件+LovyanGFX函式庫，比較久，請耐心等記錄視窗跑完。
import os, queue, sys, threading
import tkinter as tk
from tkinter import ttk
from serial.tools import list_ports
from esp32_deploy import SKETCH_BASE, deploy

_log_q = queue.Queue()
_SKETCHES = sorted(d for d in os.listdir(SKETCH_BASE) if os.path.isfile(os.path.join(SKETCH_BASE, d, d + ".ino")))


class _QueueWriter:
    # 讓 esp32_deploy.py 裡原本的 print() 直接被導向這個佇列，主執行緒再從佇列讀出來更新畫面，
    # 避免燒錄執行緒直接操作 tkinter 元件(tkinter 不是執行緒安全的)
    def write(self, s):
        _log_q.put(s)

    def flush(self):
        pass


def refresh_ports():
    ports = [p.device for p in list_ports.comports()]
    port_box["values"] = ports
    if ports and not port_box.get():
        port_box.set(ports[0])


def run_deploy():
    port = port_box.get()
    sketch = sketch_box.get()
    if not port or not sketch:
        return
    burn_btn.config(state="disabled")
    log.delete("1.0", "end")

    def worker():
        sys.stdout = _QueueWriter()
        try:
            deploy(port, sketch)
        except Exception as e:
            _log_q.put(f"\n燒錄失敗: {e}\n")
        finally:
            sys.stdout = sys.__stdout__
        _log_q.put(None)  # 結束標記

    threading.Thread(target=worker, daemon=True).start()
    poll_log()


def copy_log():
    # 一鍵把整份記錄(含錯誤訊息)複製到剪貼簿，方便直接貼給別人看錯誤
    window.clipboard_clear()
    window.clipboard_append(log.get("1.0", "end-1c"))


def poll_log():
    try:
        while True:
            item = _log_q.get_nowait()
            if item is None:
                burn_btn.config(state="normal")
                return
            log.insert("end", item)
            log.see("end")
    except queue.Empty:
        pass
    window.after(100, poll_log)


window = tk.Tk()
window.title("ESP32-S3-CAM 燒錄工具")

top = tk.Frame(window)
top.pack(fill="x", padx=10, pady=10)
tk.Label(top, text="COM 埠：").pack(side="left")
port_box = ttk.Combobox(top, width=10)
port_box.pack(side="left", padx=5)
tk.Button(top, text="重新整理", command=refresh_ports).pack(side="left")
tk.Label(top, text="韌體：").pack(side="left", padx=(10, 0))
sketch_box = ttk.Combobox(top, width=14, values=_SKETCHES, state="readonly")
sketch_box.set("SmartFrame" if "SmartFrame" in _SKETCHES else _SKETCHES[0])
sketch_box.pack(side="left", padx=5)
burn_btn = tk.Button(top, text="燒錄", command=run_deploy)
burn_btn.pack(side="left", padx=5)
tk.Button(top, text="複製記錄", command=copy_log).pack(side="left")

log = tk.Text(window, width=70, height=20)
log.pack(padx=10, pady=(0, 10))

refresh_ports()
window.mainloop()
