# 程式進入點：在 Smart Picture Frame 資料夾下執行 `python main.py` 啟動智慧相框介面
# 用 main.py 當入口，是因為 components/time.py 需要用「相對匯入」才不會跟內建 time 模組撞名，
# 而相對匯入必須讓 components 以 package 身分被載入，不能直接 `python components/interface.py`
from components import interface  # 匯入的同時就會建立視窗並進入 mainloop
