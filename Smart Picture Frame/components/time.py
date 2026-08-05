from datetime import datetime
from .clock import get_current_time, start_clock

__all__ = ["get_current_time", "start_clock"]


if __name__ == "__main__":
    # 單獨執行本檔案時，用來測試時間格式是否正確
    print(get_current_time())

