/*
 * =====================================================
 *  BB Call — ESP32 主程式
 *  功能：WiFi / MQTT 訊息收發 + DFPlayer MP3 + OLED 顯示
 *  硬體：ESP32 + SSD1306 OLED + DFPlayer Mini + SD Card
 * =====================================================
 *
 *  接線說明
 *  ─────────────────────────────────────────
 *  OLED SSD1306 (I2C)
 *    SDA  → GPIO 21
 *    SCL  → GPIO 22
 *    VCC  → 3.3V
 *    GND  → GND
 *
 *  DFPlayer Mini (UART)
 *    TX   → GPIO 16 (ESP32 RX2)
 *    RX   → GPIO 17 (ESP32 TX2)  ← 接 1kΩ 降壓電阻
 *    VCC  → 5V
 *    GND  → GND
 *    SPK1 → 喇叭 +
 *    SPK2 → 喇叭 -
 *
 *  按鍵 (低電位觸發，內部上拉)
 *    BTN_REPLY   → GPIO 34
 *    BTN_READ    → GPIO 35
 *    BTN_MUSIC   → GPIO 32
 *
 *  狀態 LED
 *    LED_STATUS  → GPIO 2 (內建 LED)
 * =====================================================
 *
 *  MQTT Topic 設計
 *    接收訊息：  bbcall/{deviceId}/inbox
 *    發送回覆：  bbcall/{deviceId}/reply
 *    狀態回報：  bbcall/{deviceId}/status
 *    音樂控制：  bbcall/{deviceId}/music
 *
 *  JSON 訊息格式 (收)
 *    { "from": "Alice", "msg": "你好！", "music": 1 }
 *    music = 0 表示不播音樂；1~99 對應 SD 卡音樂編號
 *
 *  JSON 訊息格式 (發)
 *    { "from": "BBCall", "msg": "已讀", "ts": 1234567890 }
 * =====================================================
 */

#include "config.h"
#include "wifi_manager.h"
#include "mqtt_manager.h"
#include "display_manager.h"
#include "audio_manager.h"
#include "message_store.h"

// ─── 按鍵 GPIO ────────────────────────────────────
#define BTN_REPLY  34
#define BTN_READ   35
#define BTN_MUSIC  32
#define LED_STATUS  2

// ─── 全域狀態 ──────────────────────────────────────
unsigned long lastButtonCheck = 0;
unsigned long lastStatusReport = 0;
bool hasUnread = false;
uint8_t currentMsgIndex = 0;

// ─── 初始化 ────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial.println(F("\n=== BB Call 啟動中 ==="));

  // 初始化 LED
  pinMode(LED_STATUS, OUTPUT);
  digitalWrite(LED_STATUS, LOW);

  // 初始化按鍵（內部上拉）
  pinMode(BTN_REPLY, INPUT_PULLUP);
  pinMode(BTN_READ, INPUT_PULLUP);
  pinMode(BTN_MUSIC, INPUT_PULLUP);

  // 初始化各模組
  Display.begin();
  Display.showBootScreen("BB Call", VERSION);

  Audio.begin();
  MsgStore.begin();

  // 連線 WiFi
  Display.showStatus("連線 WiFi...");
  WiFiMgr.connect(WIFI_SSID, WIFI_PASSWORD);

  // 連線 MQTT
  Display.showStatus("連線 MQTT...");
  MqttMgr.begin(MQTT_SERVER, MQTT_PORT, MQTT_USER, MQTT_PASS, DEVICE_ID);
  MqttMgr.setMessageCallback(onMessageReceived);

  Display.showIdle("待機中");
  Audio.playTrack(BOOT_SOUND);  // 播放開機音效
  Serial.println(F("=== 初始化完成 ==="));
}

// ─── 主迴圈 ────────────────────────────────────────
void loop() {
  WiFiMgr.loop();
  MqttMgr.loop();
  Audio.loop();

  // 每 50ms 檢查按鍵
  if (millis() - lastButtonCheck > 50) {
    handleButtons();
    lastButtonCheck = millis();
  }

  // 每 30s 回報狀態
  if (millis() - lastStatusReport > 30000) {
    reportStatus();
    lastStatusReport = millis();
  }

  // LED 閃爍：有未讀訊息時
  if (hasUnread) {
    digitalWrite(LED_STATUS, (millis() / 500) % 2);
  } else {
    digitalWrite(LED_STATUS, LOW);
  }
}

// ─── 收到 MQTT 訊息 ────────────────────────────────
void onMessageReceived(String topic, String payload) {
  Serial.printf("[MQTT] Topic: %s\n", topic.c_str());
  Serial.printf("[MQTT] Payload: %s\n", payload.c_str());

  // 解析 JSON
  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, payload);
  if (err) {
    Serial.printf("[MQTT] JSON 解析失敗: %s\n", err.c_str());
    return;
  }

  // 讀取欄位（有預設值）
  const char* from    = doc["from"]  | "Unknown";
  const char* msg     = doc["msg"]   | "";
  int musicTrack      = doc["music"] | 0;

  // 儲存訊息
  Message newMsg;
  strncpy(newMsg.from, from, sizeof(newMsg.from) - 1);
  strncpy(newMsg.text, msg,  sizeof(newMsg.text) - 1);
  newMsg.musicTrack = musicTrack;
  newMsg.timestamp  = millis();
  newMsg.isRead     = false;
  MsgStore.push(newMsg);

  // 顯示訊息
  currentMsgIndex = MsgStore.getLatestIndex();
  Display.showMessage(from, msg);

  // 播放音樂（若有指定）
  if (musicTrack > 0) {
    Audio.playTrack(musicTrack);
  } else {
    Audio.playTrack(NOTIFY_SOUND);  // 通知音效
  }

  hasUnread = true;
  Serial.printf("[MSG] 來自 %s：%s\n", from, msg);
}

// ─── 按鍵處理 ─────────────────────────────────────
void handleButtons() {
  static bool prevReply = HIGH, prevRead = HIGH, prevMusic = HIGH;

  bool nowReply = digitalRead(BTN_REPLY);
  bool nowRead  = digitalRead(BTN_READ);
  bool nowMusic = digitalRead(BTN_MUSIC);

  // BTN_REPLY：發送「已收到」回覆
  if (prevReply == HIGH && nowReply == LOW) {
    Serial.println(F("[BTN] 回覆按鍵"));
    sendReply("已收到，謝謝！");
    Display.showStatus("回覆已送出");
    delay(1500);
    Display.showMessage(
      MsgStore.get(currentMsgIndex).from,
      MsgStore.get(currentMsgIndex).text
    );
  }

  // BTN_READ：標記已讀 / 切換訊息
  if (prevRead == HIGH && nowRead == LOW) {
    Serial.println(F("[BTN] 已讀按鍵"));
    MsgStore.markRead(currentMsgIndex);

    // 切換到下一則未讀
    int next = MsgStore.getNextUnread(currentMsgIndex);
    if (next >= 0) {
      currentMsgIndex = next;
      Message m = MsgStore.get(currentMsgIndex);
      Display.showMessage(m.from, m.text);
    } else {
      hasUnread = false;
      Display.showIdle("無未讀訊息");
    }
  }

  // BTN_MUSIC：重播最後一首音樂
  if (prevMusic == HIGH && nowMusic == LOW) {
    Serial.println(F("[BTN] 音樂按鍵"));
    int track = MsgStore.get(currentMsgIndex).musicTrack;
    if (track > 0) {
      Audio.playTrack(track);
      Display.showStatus("播放音樂中...");
    } else {
      Display.showStatus("無音樂");
    }
  }

  prevReply = nowReply;
  prevRead  = nowRead;
  prevMusic = nowMusic;
}

// ─── 發送回覆 ─────────────────────────────────────
void sendReply(const char* text) {
  StaticJsonDocument<128> doc;
  doc["from"] = DEVICE_ID;
  doc["msg"]  = text;
  doc["ts"]   = millis();

  char buf[128];
  serializeJson(doc, buf);

  String topic = String("bbcall/") + DEVICE_ID + "/reply";
  MqttMgr.publish(topic.c_str(), buf);
}

// ─── 回報裝置狀態 ──────────────────────────────────
void reportStatus() {
  StaticJsonDocument<128> doc;
  doc["online"]  = true;
  doc["unread"]  = MsgStore.getUnreadCount();
  doc["heap"]    = ESP.getFreeHeap();
  doc["rssi"]    = WiFi.RSSI();

  char buf[128];
  serializeJson(doc, buf);

  String topic = String("bbcall/") + DEVICE_ID + "/status";
  MqttMgr.publish(topic.c_str(), buf);
}
