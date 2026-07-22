# 圖片導入
import os
import shutil
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "photos")
os.makedirs(path, exist_ok=True)

# 格式限定於所有圖片與影片檔
format = ".jpeg, .png, .web, .mp4, .wav, .gif"
# 目前輪播/顯示只支援圖片；.mp4/.wav 只會被上面的 format 記錄，播放功能留給日後擴充
IMAGE_EXTS = (".jpeg", ".jpg", ".png", ".webp", ".gif", ".bmp")

_index = 0


def upload_photo():
    # 開啟檔案選擇視窗，把選好的圖片複製進 photos 資料夾
    src = filedialog.askopenfilename(
        title="選擇圖片",
        filetypes=[("Image", "*.jpg *.jpeg *.png *.gif *.webp *.bmp")],
    )
    if src:
        shutil.copy(src, path)


def list_photos():
    # 列出 photos 資料夾中所有符合圖片格式的檔案
    return [f for f in os.listdir(path) if f.lower().endswith(IMAGE_EXTS)]


def build_photo_panel(parent):
    # 建立輪播用的 Label，回傳給 interface.py 放進主視窗；不自建 Tk()/mainloop，
    # 這樣才能跟 weather/time 共用 interface.py 唯一的主視窗
    label = tk.Label(parent, bg="black")
    label.pack(fill="both", expand=True)
    _show_next(label)
    return label


def _show_next(label):
    # 每 5 秒自動切換下一張圖片
    global _index
    photos = list_photos()
    if photos:
        img_path = os.path.join(path, photos[_index % len(photos)])
        img = Image.open(img_path)
        img.thumbnail((label.winfo_screenwidth(), label.winfo_screenheight()))
        photo_img = ImageTk.PhotoImage(img)
        label.image = photo_img  # 保留參照，避免被垃圾回收造成畫面空白
        label.config(image=photo_img)
        _index += 1
    label.after(5000, _show_next, label)
