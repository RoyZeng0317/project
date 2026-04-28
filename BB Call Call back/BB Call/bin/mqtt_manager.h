#pragma once
#include <PubSubClient.h>
#include <WiFi.h>
#include "config.h"

// ─── Callback 型別 ────────────────────────────────
typedef void (*MsgCallback)(String topic, String payload);

class MqttManager {
public:
  WiFiClient   wifiClient;
  PubSubClient client;
  MsgCallback  userCallback = nullptr;

  const char* _server;
  int         _port;
  const char* _user;
  const char* _pass;
  const char* _deviceId;

  MqttManager() : client(wifiClient) {}

  void begin(const char* server, int port,
             const char* user, const char* pass,
             const char* deviceId) {
    _server   = server;
    _port     = port;
    _user     = user;
    _pass     = pass;
    _deviceId = deviceId;

    client.setServer(server, port);
    client.setCallback([](char* topic, byte* payload, unsigned int len) {
      // 轉發到實例
      MqttMgr._onMessage(topic, payload, len);
    });
    client.setBufferSize(512);
    _connect();
  }

  void setMessageCallback(MsgCallback cb) {
    userCallback = cb;
  }

  void loop() {
    if (!client.connected()) {
      Serial.println(F("[MQTT] 斷線，重新連線..."));
      _connect();
    }
    client.loop();
  }

  bool publish(const char* topic, const char* payload) {
    if (!client.connected()) return false;
    bool ok = client.publish(topic, payload, true);  // retained=true
    Serial.printf("[MQTT] Publish %s → %s\n", topic, ok ? "OK" : "FAIL");
    return ok;
  }

  // ─── 私有 ──────────────────────────────────────
  void _connect() {
    String clientId = String("esp32-") + _deviceId + "-" + String(millis());
    uint8_t retries = 0;

    while (!client.connected() && retries < 5) {
      Serial.printf("[MQTT] 連線至 %s:%d ...\n", _server, _port);

      bool ok;
      if (strlen(_user) > 0) {
        ok = client.connect(clientId.c_str(), _user, _pass,
                            _willTopic().c_str(), 1, true, "{\"online\":false}");
      } else {
        ok = client.connect(clientId.c_str(),
                            nullptr, nullptr,
                            _willTopic().c_str(), 1, true, "{\"online\":false}");
      }

      if (ok) {
        Serial.println(F("[MQTT] 連線成功"));
        _subscribe();
        // 發布上線狀態
        String tp = String("bbcall/") + _deviceId + "/status";
        client.publish(tp.c_str(), "{\"online\":true}", true);
        return;
      } else {
        Serial.printf("[MQTT] 連線失敗，錯誤碼 %d，等待重試\n", client.state());
        delay(3000 * (++retries));
      }
    }
  }

  void _subscribe() {
    // 訂閱收件匣
    String inbox = String("bbcall/") + _deviceId + "/inbox";
    client.subscribe(inbox.c_str());

    // 訂閱音樂控制
    String music = String("bbcall/") + _deviceId + "/music";
    client.subscribe(music.c_str());

    Serial.printf("[MQTT] 訂閱：%s\n", inbox.c_str());
  }

  String _willTopic() {
    return String("bbcall/") + _deviceId + "/status";
  }

  void _onMessage(char* topic, byte* payload, unsigned int len) {
    String topicStr(topic);
    String payloadStr;
    payloadStr.reserve(len);
    for (unsigned int i = 0; i < len; i++) {
      payloadStr += (char)payload[i];
    }
    if (userCallback) userCallback(topicStr, payloadStr);
  }
};

MqttManager MqttMgr;
