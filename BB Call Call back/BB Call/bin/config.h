#pragma once

// ─── 版本 ──────────────────────────────────────────
#define VERSION "1.0.0"

// ─── 裝置識別 ──────────────────────────────────────
// 每台 BB Call 給一個唯一 ID（影響 MQTT Topic）
#define DEVICE_ID "bbcall_01"

// ─── WiFi 設定 ────────────────────────────────────
#define WIFI_SSID     "你的WiFi名稱"
#define WIFI_PASSWORD "你的WiFi密碼"

// ─── MQTT 設定 ────────────────────────────────────
// 使用 HiveMQ Cloud 免費版：
//   broker.hivemq.com  (port 1883, 不加密)
//   <your>.hivemq.cloud (port 8883, TLS)
// 使用本地 Mosquitto：
//   192.168.x.x (port 1883)
#define MQTT_SERVER "broker.hivemq.com"
#define MQTT_PORT    1883
#define MQTT_USER    ""   // 無驗證留空
#define MQTT_PASS    ""

// ─── 音效編號 ─────────────────────────────────────
// SD 卡資料夾結構：/01/001.mp3, /01/002.mp3 ...
// DFPlayer Mini 依資料夾+編號播放
#define BOOT_SOUND   1   // 開機音效
#define NOTIFY_SOUND 2   // 收訊通知音效

// ─── 訊息佇列大小 ─────────────────────────────────
#define MSG_QUEUE_SIZE 10

// ─── OLED 設定 ────────────────────────────────────
#define OLED_ADDRESS 0x3C
#define OLED_WIDTH   128
#define OLED_HEIGHT   64

// ─── DFPlayer 串口 ────────────────────────────────
#define DFPLAYER_RX 16   // ESP32 RX2
#define DFPLAYER_TX 17   // ESP32 TX2
#define DFPLAYER_VOLUME 20  // 0~30
