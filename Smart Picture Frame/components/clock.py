from datetime import datetime


def get_current_time():
    # 抓取當前時間
    now = datetime.now()
    # format
    ct = now.strftime("%H:%M:%S %a/%m/%d/%Y")
    return ct


def start_clock(label):
    # 每秒更新一次 tkinter Label 上顯示的時間，interface.py 直接呼叫即可自動跳動
    label.config(text=get_current_time())
    label.after(1000, start_clock, label)


if __name__ == "__main__":
    # 單獨執行本檔案時，用來測試時間格式是否正確
    print(get_current_time())
