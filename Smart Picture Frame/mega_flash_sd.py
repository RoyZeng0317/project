# 電腦端：把 photos/ 資料夾裡的靜態圖片轉成 Mega 面板看得懂的 RGB565 原始格式，
# 存到 TF 卡(SD 卡)根目錄，檔名 P000.BIN、P001.BIN...，開機後 MEGA2560_test.ino 會自動在
# 這幾張之間本地輪播(見 scanLocalPhotos/showLocalPhoto)，直接讀卡秒切，不受 USB 序列埠傳輸
# 速度限制；GIF 動畫不燒(張數太多)，動畫仍走即時傳輸(mega_frame_sender.py)
# 用法：把 TF 卡插進讀卡機，到「本機」看該磁碟機代號(例如 E:)，執行:
#   python mega_flash_sd.py E:
import os
import sys
from PIL import Image
from components import photo
from mega_frame_sender import to_rgb565

MAX_PHOTOS = 50  # 跟 MEGA2560_test.ino 的 MAX_SD_PHOTOS 一致；SD 卡容量夠大，這裡只是限制開機掃描檔案的時間


def flash(sd_root):
    if not os.path.isdir(sd_root):
        print(f"找不到路徑 {sd_root}，確認 TF 卡已插入讀卡機且代號正確")
        return

    pool = photo.get_selected() or photo.list_photos()
    candidates = [n for n in pool if not n.lower().endswith(".gif")]
    if not candidates:
        print("photos/ 資料夾裡沒有可燒錄的靜態圖片")
        return

    burned = 0
    for name in candidates[:MAX_PHOTOS]:
        try:
            data = to_rgb565(Image.open(os.path.join(photo.path, name)))
        except Exception as e:
            print(f"跳過無法讀取的圖片 {name}: {e}")
            continue
        out_path = os.path.join(sd_root, f"P{burned:03d}.BIN")
        with open(out_path, "wb") as f:
            f.write(data)
        print(f"寫入 {name} -> {out_path}")
        burned += 1

    # 清掉這次沒用到、但上次燒錄殘留的舊檔，避免面板輪播到過期照片
    idx = burned
    while os.path.exists(os.path.join(sd_root, f"P{idx:03d}.BIN")):
        os.remove(os.path.join(sd_root, f"P{idx:03d}.BIN"))
        idx += 1

    print(f"完成，共寫入 {burned} 張圖到 TF 卡" if burned else "沒有成功寫入任何圖片(全部讀取失敗)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python mega_flash_sd.py <TF卡磁碟機代號>，例如 python mega_flash_sd.py E:")
        sys.exit(1)
    flash(sys.argv[1])
