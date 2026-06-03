# Smart Picture Frame - 智慧電子日曆

基於 Raspberry Pi Pico 2W 的智慧電子日曆，支援觸控螢幕操作，
可輪播顯示時間、天氣、待辦事項及圖片。

## 功能特色

| 功能 | 說明 |
|------|------|
| 🕐 **時鐘** | 大字體數位時鐘，NTP 自動校時 |
| 🌤 **天氣** | 從 OpenWeatherMap 取得即時天氣資訊 |
| 📅 **行事曆** | 月曆檢視 + 待辦事項列表 |
| 🖼 **圖片輪播** | 支援 SD 卡圖片、網路圖片、使用者上傳 |
| 🔄 **自動輪播** | 在各大螢幕之間自動切換 |
| 👆 **觸控操作** | 點擊切換畫面，左右滑動瀏覽圖片 |

## 硬體需求

| 元件 | 型號/規格 |
|------|-----------|
| 微控制器 | Raspberry Pi Pico 2W (RP2350, WiFi 內建) |
| 觸控螢幕 | ILI9341 320x240 SPI TFT + XPT2046 觸控 (常見 2.8吋/3.5吋) |
| 或 | ST7789 240x240 SPI TFT (替代選擇) |
| SD 卡模組 | SPI 介面 MicroSD 卡槽 |
| 電源 | 5V USB-C 或 3.7V 鋰電池 |

## 接線說明

### ILI9341 螢幕 (320x240)

| Pico 2W Pin | 功能 | 螢幕 Pin |
|-------------|------|-----------|
| GP2 (SPI0 SCK) | SPI 時脈 | SCK/SCL |
| GP3 (SPI0 TX) | SPI MOSI | MOSI/SDA |
| GP4 (SPI0 RX) | SPI MISO | MISO (可不接) |
| GP9 | 晶片選擇 | CS |
| GP8 | 資料/指令 | DC |
| GP10 | 重置 | RST |
| GP11 | 背光控制 | BL (可接 3.3V) |
| 3.3V | 電源 | VCC |
| GND | 接地 | GND |

### XPT2046 觸控

| Pico 2W Pin | 功能 | 觸控 Pin |
|-------------|------|-----------|
| GP10 (SPI1 SCK) | SPI 時脈 | T_CLK |
| GP11 (SPI1 TX) | SPI MOSI | T_DIN |
| GP12 (SPI1 RX) | SPI MISO | T_DOUT |
| GP13 | 晶片選擇 | T_CS |
| GP14 | 中斷 | T_IRQ |

### MicroSD 卡模組

| Pico 2W Pin | 功能 | SD Pin |
|-------------|------|--------|
| GP10 (SPI1 SCK) | 共用觸控 SCK | SCK |
| GP11 (SPI1 TX) | 共用觸控 MOSI | MOSI |
| GP12 (SPI1 RX) | 共用觸控 MISO | MISO |
| GP15 | 晶片選擇 | CS |

> 若觸控與 SD 卡共用 SPI1，需確保兩者 CS 為不同 Pin。

## 軟體安裝

### 1. 安裝 MicroPython 到 Pico 2W

下載最新 MicroPython for Raspberry Pi Pico 2：
https://micropython.org/download/RPI_PICO2_W/

按住 Pico 2W 的 BOOTSEL 鍵，插上 USB，將 .uf2 檔案拖入 RPI-RP2 磁碟。

### 2. 安裝開發工具

```bash
pip install pyserial adafruit-ampy
```

### 3. 修改設定

編輯 `firmware/config.py`，填入：

```python
# WiFi 設定
"ssid": "你的 WiFi 名稱",
"password": "你的 WiFi 密碼",

# OpenWeatherMap API Key (免費註冊)
"api_key": "你的 API Key",

# 天氣城市
"city": "Yunlin",  # 或 Taipei, Taichung, Kaohsiung
```

### 4. 轉換圖片

將圖片轉換為 RGB565 格式放到 SD 卡：

```bash
python tools/img_convert.py my_photo.jpg
python tools/img_convert.py pictures/ --batch
```

### 5. 部署到 Pico 2W

```bash
python tools/deploy.py
```

部署完成後按 Pico 2W 的 RST 鍵重新啟動。

### 單檔部署

```bash
python tools/deploy.py config.py
```

## 操作說明

| 觸控操作 | 功能 |
|----------|------|
| 點擊畫面 | 切換到下一個畫面 |
| 在圖片畫面點擊 | 切換下一張圖片 |
| 長按 | 返回儀表板 |

## 畫面說明

| 畫面 | 內容 |
|------|------|
| **儀表板** | 時間 + 天氣 + 圖片 + 待辦整合顯示 |
| **時鐘** | 大字體數位時鐘，顯示日期與星期 |
| **天氣** | 城市、溫度、體感溫度、濕度、天氣描述 |
| **行事曆** | 月曆 + 待辦事項列表 |
| **圖片** | 全螢幕圖片輪播 |

## 待辦事項管理

待辦事項儲存在 SD 卡的 `todo.json` 中，可透過修改該檔案
或撰寫網頁後端同步。預設格式：

```json
{
  "items": [
    {"id": 1, "text": "完成專題", "done": false},
    {"id": 2, "text": "買牛奶", "done": true}
  ]
}
```

## 專案結構

```
Smart Picture Frame/
├── firmware/           # MicroPython 韌體
│   ├── main.py         # 主程式入口
│   ├── config.py       # 設定檔
│   ├── network_manager.py  # WiFi 連線
│   ├── ntp_time.py     # NTP 時間同步
│   ├── weather.py      # 天氣 API
│   ├── photo_manager.py    # 圖片管理
│   ├── todo_manager.py     # 待辦事項管理
│   ├── drivers/        # 硬體驅動
│   ├── screens/        # UI 畫面
│   └── lib/            # 工具函式庫
├── tools/              # PC 端工具
│   ├── deploy.py       # 部署到 Pico
│   └── img_convert.py  # 圖片轉換
├── assets/             # 靜態資源
└── README.md
```

## Pin 配置圖 (config.pin_map)

預設 Pin 配置可在 `config.py` 中自由修改，
若使用不同的 TFT 螢幕或腳位，只需更新對應設定即可。
