/*
 * =====================================================
 *  BB Call — ESP32-S3-CAM 主程式
 *  功能：WiFi / MQTT 訊息收發 + DFPlayer MP3 + OLED 顯示
 * =====================================================
 */

// ─── 必要 include（順序很重要）────────────────────
#include <Arduino.h>
#include <WiFi.h>
#include <ArduinoJson.h>
#include "config.h"
#include "message_store.h"
#include "wifi_manager.h"
#include "mqtt_manager.h"
#include "display_manager.h"
#include "audio_manager.h"

// ─── 全域狀態 ──────────────────────────────────────
unsigned long lastButtonCheck  = 0;
unsigned long lastStatusReport = 0;
bool    hasUnread      = false;
uint8_t currentMsgIndex = 0;

// ─── 函式前置宣告 ──────────────────────────────────
void onMessageReceived(String topic, String payload);
void handleButtons();
void sendReply(const char* text);
void reportStatus();

// ─── 初始化 ────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println(F("\n=== BB Call 啟動中 ==="));

  pinMode(LED_STATUS, OUTPUT);
  digitalWrite(LED_STATUS, LOW);

  pinMode(BTN_REPLY, INPUT_PULLUP);
  pinMode(BTN_READ,  INPUT_PULLUP);
  pinMode(BTN_MUSIC, INPUT_PULLUP);

  Display.begin();
  Display.showBootScreen("BB Call", VERSION);

  Audio.begin();
  MsgStore.begin();

  Display.showStatus("連線 WiFi...");
  WiFiMgr.connect(WIFI_SSID, WIFI_PASSWORD);

  Display.showStatus("連線 MQTT...");
  MqttMgr.begin(MQTT_SERVER, MQTT_PORT, MQTT_USER, MQTT_PASS, DEVICE_ID);
  MqttMgr.setMessageCallback(onMessageReceived);

  Display.showIdle("待機中");
  Audio.playTrack(BOOT_SOUND);
  Serial.println(F("=== 初始化完成 ==="));
}

// ─── 主迴圈 ────────────────────────────────────────
void loop() {
  WiFiMgr.loop();
  MqttMgr.loop();
  Audio.loop();

  if (millis() - lastButtonCheck > 50) {
    handleButtons();
    lastButtonCheck = millis();
  }

  if (millis() - lastStatusReport > 30000) {
    reportStatus();
    lastStatusReport = millis();
  }

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

  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, payload);
  if (err) {
    Serial.printf("[MQTT] JSON 解析失敗: %s\n", err.c_str());
    return;
  }

  const char* from   = doc["from"]  | "Unknown";
  const char* msg    = doc["msg"]   | "";
  int musicTrack     = doc["music"] | 0;

  Message newMsg;
  strncpy(newMsg.from, from, sizeof(newMsg.from) - 1);
  strncpy(newMsg.text, msg,  sizeof(newMsg.text) - 1);
  newMsg.musicTrack = musicTrack;
  newMsg.timestamp  = millis();
  newMsg.isRead     = false;
  MsgStore.push(newMsg);

  currentMsgIndex = MsgStore.getLatestIndex();
  Display.showMessage(from, msg);

  if (musicTrack > 0) {
    Audio.playTrack(musicTrack);
  } else {
    Audio.playTrack(NOTIFY_SOUND);
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

  if (prevReply == HIGH && nowReply == LOW) {
    Serial.println(F("[BTN] 回覆"));
    sendReply("已收到，謝謝！");
    Display.showStatus("回覆已送出");
    delay(1500);
    Display.showMessage(
      MsgStore.get(currentMsgIndex).from,
      MsgStore.get(currentMsgIndex).text
    );
  }

  if (prevRead == HIGH && nowRead == LOW) {
    Serial.println(F("[BTN] 已讀"));
    MsgStore.markRead(currentMsgIndex);
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

  if (prevMusic == HIGH && nowMusic == LOW) {
    Serial.println(F("[BTN] 音樂"));
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
  doc["online"] = true;
  doc["unread"] = MsgStore.getUnreadCount();
  doc["heap"]   = ESP.getFreeHeap();
  doc["rssi"]   = WiFi.RSSI();

  char buf[128];
  serializeJson(doc, buf);

  String topic = String("bbcall/") + DEVICE_ID + "/status";
  MqttMgr.publish(topic.c_str(), buf);
}
