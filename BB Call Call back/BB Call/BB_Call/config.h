#pragma once

// ─── 版本 ──────────────────────────────────────────
#define VERSION "1.0.0"

// ─── 裝置識別 ──────────────────────────────────────
#define DEVICE_ID "bbcall_01"

// ─── WiFi 設定 ────────────────────────────────────
#define WIFI_SSID     "你的WiFi名稱"
#define WIFI_PASSWORD "你的WiFi密碼"

// ─── MQTT 設定 ────────────────────────────────────
#define MQTT_SERVER "broker.hivemq.com"
#define MQTT_PORT    1883
#define MQTT_USER    ""
#define MQTT_PASS    ""

// ─── 音效編號 ─────────────────────────────────────
#define BOOT_SOUND   1
#define NOTIFY_SOUND 2

// ─── 訊息佇列 ─────────────────────────────────────
#define MSG_QUEUE_SIZE 10

// ─── OLED 設定 ────────────────────────────────────
#define OLED_ADDRESS 0x3C
#define OLED_WIDTH   128
#define OLED_HEIGHT   64
#define OLED_SDA     17
#define OLED_SCL     18

// ─── DFPlayer 串口 ────────────────────────────────
#define DFPLAYER_RX     16
#define DFPLAYER_TX     15
#define DFPLAYER_VOLUME 20

// ─── GPIO：ESP32-S3-CAM 安全腳位 ─────────────────
// 避開攝影機佔用的 GPIO 0,1,2,3,4,5,11,12,13,45,46
#define BTN_REPLY   38
#define BTN_READ    39
#define BTN_MUSIC   40
#define LED_STATUS  21