# 開發用小工具：GUI 版的 deploy_pico.py，選 COM 埠後按一下按鈕就能上傳程式+照片快取，
# 不用再手動打 python deploy_pico.py COM6；燒錄邏輯完全重用 deploy_pico.py，不重寫一份。
# 注意：這只是「上傳程式/照片」，不是燒 MicroPython 韌體(.uf2)本身——韌體要進 BOOTSEL
# 得實體按住按鈕+拔掉所有電源重插，這一步是晶片硬體機制，沒辦法用任何軟體按鈕觸發。
import queue
import sys
import threading
import tkinter as tk
from tkinter import ttk
from serial.tools import list_ports
from deploy_pico import deploy
from components import photo

_log_q = queue.Queue()


class _QueueWriter:
    # 讓 deploy_pico.py 裡原本的 print() 直接被導向這個佇列，主執行緒再從佇列讀出來更新畫面，
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
    if not port:
        return
    burn_btn.config(state="disabled")
    log.delete("1.0", "end")

    def worker():
        sys.stdout = _QueueWriter()
        try:
            deploy(port)
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
window.title("Pico 燒錄工具")

top = tk.Frame(window)
top.pack(fill="x", padx=10, pady=10)
tk.Label(top, text="COM 埠：").pack(side="left")
port_box = ttk.Combobox(top, width=10)
port_box.pack(side="left", padx=5)
tk.Button(top, text="重新整理", command=refresh_ports).pack(side="left")
tk.Button(top, text="選擇照片", command=lambda: photo.select_photos_dialog(window)).pack(side="left", padx=5)
burn_btn = tk.Button(top, text="燒錄", command=run_deploy)
burn_btn.pack(side="left", padx=5)
tk.Button(top, text="複製記錄", command=copy_log).pack(side="left")

log = tk.Text(window, width=70, height=20)
log.pack(padx=10, pady=(0, 10))

refresh_ports()
window.mainloop()
