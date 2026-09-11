# 開發用小工具：GUI 版一鍵編譯+燒錄 Mega2560 韌體，選 COM 埠後按一下按鈕就好，
# 完全比照 esp32_deploy_gui.py 的架構，燒錄邏輯重用 mega_deploy.py，不重寫一份。
# 首次執行會自動裝 arduino:avr 開發板套件+函式庫，比較久，請耐心等記錄視窗跑完。
import os, queue, sys, threading
import tkinter as tk
from tkinter import ttk
from serial.tools import list_ports
from PIL import ImageTk
from mega_deploy import SKETCH_BASE, deploy
from lib.tft_read_tf import list_bin_photos, read_bin_photo, bytes_to_image, open_mega

_log_q = queue.Queue()
_tf_ser = None  # 讀 TF 卡用的序列連線(卡片留在面板上，不用拔卡)，讀取/預覽共用，燒錄前需先關閉讓出 COM 埠
_SKETCHES = sorted(d for d in os.listdir(SKETCH_BASE) if os.path.isfile(os.path.join(SKETCH_BASE, d, d + ".ino")))


class _QueueWriter:
    # 讓 mega_deploy.py 裡原本的 print() 直接被導向這個佇列，主執行緒再從佇列讀出來更新畫面，
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
    global _tf_ser
    port = port_box.get()
    sketch = sketch_box.get()
    if not port or not sketch:
        return
    if _tf_ser:
        _tf_ser.close()
        _tf_ser = None
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
    # clipboard_append() 後要馬上 update()，否則 Tk 要等事件迴圈下一輪才真的把內容送進系統剪貼簿，
    # 在 Windows 上常常表現成「按了複製、立刻去別的地方貼上卻是空的」
    window.clipboard_clear()
    window.clipboard_append(log.get("1.0", "end-1c"))
    window.update()


def refresh_tf():
    # TF 卡留在面板上，直接用上方選好的 COM 埠向 Mega 要 SD 卡清單('L' 指令)，不用拔卡
    global _tf_ser
    port = port_box.get()
    tf_list.delete(0, "end")
    if not port:
        tf_list.insert("end", "請先在上方選 COM 埠")
        return
    if _tf_ser:
        _tf_ser.close()
    try:
        _tf_ser = open_mega(port)
    except Exception as e:
        tf_list.insert("end", f"開啟 {port} 失敗: {e}")
        return
    names = list_bin_photos(_tf_ser)
    if not names:
        tf_list.insert("end", "(TF 卡裡沒有 P000.BIN 開頭的快取圖，可能還沒燒錄或 SD 卡沒插好)")
        return
    for n in names:
        tf_list.insert("end", n)


def preview_tf(event=None):
    # 雙擊清單項目：向 Mega 要這張 bin 的原始內容('R' 指令)，轉回圖片開新視窗預覽，確認顏色/內容有沒有燒對
    sel = tf_list.curselection()
    if not sel or not _tf_ser:
        return
    name = tf_list.get(sel[0])
    if not (name.startswith("P") and name.endswith(".BIN")):
        return
    data = read_bin_photo(_tf_ser, name)
    if not data:
        tf_list.insert("end", f"讀取 {name} 失敗，確認 SD 卡還在面板上")
        return
    img = bytes_to_image(data)
    win = tk.Toplevel(window)
    win.title(name)
    photo_img = ImageTk.PhotoImage(img)
    label = tk.Label(win, image=photo_img)
    label.image = photo_img  # type: ignore[attr-defined]  # 保留參照，避免被垃圾回收造成畫面空白
    label.pack()


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
window.title("Mega2560 燒錄工具")

top = tk.Frame(window)
top.pack(fill="x", padx=10, pady=10)
tk.Label(top, text="COM 埠：").pack(side="left")
port_box = ttk.Combobox(top, width=10)
port_box.pack(side="left", padx=5)
tk.Button(top, text="重新整理", command=refresh_ports).pack(side="left")
tk.Label(top, text="韌體：").pack(side="left", padx=(10, 0))
sketch_box = ttk.Combobox(top, width=18, values=_SKETCHES, state="readonly")
sketch_box.set("MEGA2560_test" if "MEGA2560_test" in _SKETCHES else _SKETCHES[0])
sketch_box.pack(side="left", padx=5)
burn_btn = tk.Button(top, text="燒錄", command=run_deploy)
burn_btn.pack(side="left", padx=5)
tk.Button(top, text="複製記錄", command=copy_log).pack(side="left")

tf_top = tk.Frame(window)
tf_top.pack(fill="x", padx=10, pady=(0, 10))
tk.Button(tf_top, text="讀取 TF 卡", command=refresh_tf).pack(side="left")
tk.Label(tf_top, text="(卡片留在面板上，用上方 COM 埠讀取；雙擊清單項目可預覽圖片)").pack(side="left", padx=(10, 0))

tf_list = tk.Listbox(window, width=70, height=6)
tf_list.pack(padx=10, pady=(0, 10))
tf_list.bind("<Double-Button-1>", preview_tf)

log = tk.Text(window, width=70, height=20)
log.pack(padx=10, pady=(0, 10))


def on_close():
    if _tf_ser:
        _tf_ser.close()
    window.destroy()


refresh_ports()
window.protocol("WM_DELETE_WINDOW", on_close)
window.mainloop()
