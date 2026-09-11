# 圖片導入
import io
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageCms, ImageTk

# HEIC/AVIF 是選用格式，要另外 pip install pillow-heif / pillow-avif-plugin(已加進 requirements.txt)，
# 沒裝的話就當作 Pillow 讀不懂的檔案照舊跳過，不影響其他格式
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass
try:
    import pillow_avif  # noqa: F401  # import 就會自動註冊 AVIF 解碼器
except ImportError:
    pass

path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "photos")
os.makedirs(path, exist_ok=True)

# 格式限定於所有圖片與影片檔
format = ".jpeg, .png, .webp, .mp4, .wav, .gif, .bmp, .tiff, .heic, .avif"
# 目前輪播/顯示只支援圖片；.mp4/.wav 只會被上面的 format 記錄，播放功能留給日後擴充
IMAGE_EXTS = (".jpeg", ".jpg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".tif", ".heic", ".heif", ".avif")
_SRGB_PROFILE = ImageCms.createProfile("sRGB")

_index = 0
MAX_SELECT = 3  # 電腦端輪播與燒錄到 Pico 共用同一份手動選片清單，跟 Pico flash 容量上限一致
SELECTED_FILE = os.path.join(path, "selected.txt")


def upload_photo():
    # 開啟檔案選擇視窗，把選好的圖片複製進 photos 資料夾
    src = filedialog.askopenfilename(
        title="選擇圖片",
        filetypes=[("Image", "*.jpg *.jpeg *.png *.gif *.webp *.bmp *.tiff *.tif *.heic *.heif *.avif")],
    )
    if src:
        shutil.copy(src, path)


def normalize_rgb(img):
    # 部分手機/截圖工具(例如三星截圖)存的圖內嵌 Display P3 等非 sRGB 色彩描述檔，
    # 直接 convert("RGB") 會把原始數值當 sRGB 硬解讀，面板上顏色會偏掉；
    # 有描述檔就先換算回 sRGB 再轉，沒有描述檔的圖片維持原本直接轉換
    icc = img.info.get("icc_profile")
    if icc:
        try:
            src_profile = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            return ImageCms.profileToProfile(img.convert("RGB"), src_profile, _SRGB_PROFILE, outputMode="RGB")
        except Exception:
            pass
    return img.convert("RGB")


def list_photos():
    # 列出 photos 資料夾中所有符合圖片格式的檔案
    return [f for f in os.listdir(path) if f.lower().endswith(IMAGE_EXTS)]


def get_selected():
    # 讀取使用者手動指定的最多 MAX_SELECT 張照片(電腦端輪播、燒錄到 Pico 共用)，
    # 檔案不存在或裡面的檔名已被刪除就自動忽略，回傳空清單代表沒手動選過、外部要 fallback 成全部照片
    if not os.path.exists(SELECTED_FILE):
        return []
    with open(SELECTED_FILE, encoding="utf-8") as f:
        names = [line.strip() for line in f if line.strip()]
    existing = set(list_photos())
    return [n for n in names if n in existing][:MAX_SELECT]


def set_selected(names):
    with open(SELECTED_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(names[:MAX_SELECT]))


def select_photos_dialog(parent):
    # 共用的選片視窗，GUI.py(電腦端輪播)跟 pico_deploy_gui.py(燒錄工具)都呼叫這個，
    # 避免同一套選片邏輯寫兩次
    win = tk.Toplevel(parent)
    win.title(f"選擇照片(最多 {MAX_SELECT} 張)")

    listbox = tk.Listbox(win, selectmode="multiple", width=50, height=15)
    listbox.pack(padx=10, pady=10, fill="both", expand=True)

    names = list_photos()
    selected_now = set(get_selected())
    for i, name in enumerate(names):
        listbox.insert("end", name)
        if name in selected_now:
            listbox.selection_set(i)

    def confirm():
        picked = [names[i] for i in listbox.curselection()]
        if len(picked) > MAX_SELECT:
            messagebox.showerror("選太多了", f"最多只能選 {MAX_SELECT} 張")
            return
        set_selected(picked)
        win.destroy()

    tk.Button(win, text="確定", command=confirm).pack(pady=(0, 10))


def build_photo_panel(parent):
    # 建立輪播用的 Label，回傳給 interface.py 放進主視窗；不自建 Tk()/mainloop，
    # 這樣才能跟 weather/time 共用 interface.py 唯一的主視窗
    label = tk.Label(parent, bg="black")
    label.pack(fill="both", expand=True)
    _show_next(label)
    return label


def _show_next(label):
    # 每 5 秒自動切換下一張圖片；有手動選片就只在選到的照片裡輪播，沒選過才 fallback 成全部照片
    global _index
    photos = get_selected() or list_photos()
    if photos:
        img_path = os.path.join(path, photos[_index % len(photos)])
        img = Image.open(img_path)
        img.thumbnail((label.winfo_screenwidth(), label.winfo_screenheight()))
        photo_img = ImageTk.PhotoImage(img)
        label.image = photo_img  # 保留參照，避免被垃圾回收造成畫面空白
        label.config(image=photo_img)
        _index += 1
    label.after(5000, _show_next, label)
