# BB Call — ESP32 完整專案

## 硬體需求

| 元件 | 型號 | 說明 |
|---|---|---|
| 主控板 | ESP32-WROOM-32 DevKit | 任何 ESP32 板皆可 |
| 螢幕 | SSD1306 OLED 128×64 | I2C 介面 |
| 音效模組 | DFPlayer Mini | 搭配 MicroSD |
| 喇叭 | 3W 4Ω | 小型音箱喇叭 |
| MicroSD | 任何品牌 | 格式化成 FAT32 |
| 電阻 | 1kΩ × 1 | DFPlayer RX 降壓用 |
| 按鍵 | 輕觸按鍵 × 3 | 6×6mm 低電位觸發 |

---

## 接線圖

```
ESP32          OLED SSD1306
─────          ────────────
GPIO 21  ─────  SDA
GPIO 22  ─────  SCL
3.3V     ─────  VCC
GND      ─────  GND

ESP32          DFPlayer Mini
─────          ─────────────
GPIO 16  ─────  TX  (ESP RX2)
GPIO 17  ─┤1kΩ├─  RX  (ESP TX2) ← 必須接電阻！
5V       ─────  VCC
GND      ─────  GND
               SPK1 ──┬── 喇叭 +
               SPK2 ──┴── 喇叭 -

ESP32          按鍵
─────          ────
GPIO 34  ─────  BTN_REPLY  (另一端接 GND)
GPIO 35  ─────  BTN_READ   (另一端接 GND)
GPIO 32  ─────  BTN_MUSIC  (另一端接 GND)
GPIO 2   ─────  狀態 LED (內建)
```

---

## SD 卡音樂檔案結構

DFPlayer Mini 使用固定資料夾命名格式：

```
SD 卡根目錄/
└── 01/
    ├── 001.mp3   ← track 1：開機音效
    ├── 002.mp3   ← track 2：收訊通知音效
    ├── 003.mp3   ← track 3：自訂音樂 1
    └── 004.mp3   ← track 4：自訂音樂 2
```

> ⚠️ 資料夾名稱必須是 2 位數，檔案名稱必須是 3 位數。

---

## 安裝 Arduino 程式庫

在 Arduino IDE 的「程式庫管理員」搜尋並安裝：

| 程式庫名稱 | 用途 |
|---|---|
| `PubSubClient` by knolleary | MQTT 客戶端 |
| `Adafruit SSD1306` | OLED 顯示驅動 |
| `Adafruit GFX Library` | 圖形基礎 |
| `DFRobotDFPlayerMini` | MP3 播放驅動 |
| `ArduinoJson` by bblanchon | JSON 解析 |

---

## 設定步驟

1. 用文字編輯器開啟 `config.h`
2. 修改以下設定：
   ```cpp
   #define WIFI_SSID     "你的WiFi名稱"
   #define WIFI_PASSWORD "你的WiFi密碼"
   #define MQTT_SERVER   "broker.hivemq.com"  // 或你的伺服器 IP
   #define DEVICE_ID     "bbcall_01"           // 每台改不同 ID
   ```
3. 在 Arduino IDE 選擇開發板：**ESP32 Dev Module**
4. 上傳程式碼

---

## MQTT Topic 說明

| Topic | 方向 | 說明 |
|---|---|---|
| `bbcall/{id}/inbox` | 手機 → ESP32 | 發送訊息給 BB Call |
| `bbcall/{id}/reply` | ESP32 → 手機 | BB Call 回覆 |
| `bbcall/{id}/status` | ESP32 → 手機 | 裝置狀態（每 30 秒） |
| `bbcall/{id}/music` | 手機 → ESP32 | 直接控制播放 |

### 訊息 JSON 格式

**發送給 BB Call（手機發出）：**
```json
{
  "from": "Alice",
  "msg": "記得帶雨傘！",
  "music": 3
}
```

**BB Call 回覆（按下回覆鍵）：**
```json
{
  "from": "bbcall_01",
  "msg": "已收到，謝謝！",
  "ts": 123456789
}
```

---

## 按鍵功能

| 按鍵 | GPIO | 功能 |
|---|---|---|
| BTN_REPLY | 34 | 發送「已收到」回覆給手機 |
| BTN_READ | 35 | 標記已讀，切換下一則未讀訊息 |
| BTN_MUSIC | 32 | 重播當前訊息附帶的音樂 |

---

## 測試工具

**Python 測試腳本（電腦端）：**
```bash
pip install paho-mqtt
python3 test_bbcall.py
```

**手機 App（免費）：**
- Android：`IoT MQTT Panel` 或 `MQTT Dash`
- iOS：`MQTTool` 或 `EasyMQTT`

在 App 中設定：
- Broker: `broker.hivemq.com`
- Port: `1883`
- Publish topic: `bbcall/bbcall_01/inbox`

---

## 常見問題

**DFPlayer 無聲音？**
- 確認 RX 接線加了 1kΩ 電阻
- SD 卡格式化為 FAT32（非 exFAT）
- 資料夾/檔案命名格式正確

**OLED 不亮？**
- 確認 I2C 位址：用 I2C Scanner 掃描，通常是 `0x3C` 或 `0x3D`
- 修改 `config.h` 中的 `OLED_ADDRESS`

**MQTT 無法連線？**
- 確認 WiFi 已連線
- 嘗試換用 `test.mosquitto.org` broker

**訊息不完整？**
- `MSG_QUEUE_SIZE` 調大
- `text` 欄位長度超過 128 字元時會截斷
