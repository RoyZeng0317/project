#pragma once
#include <WiFi.h>
#include <PubSubClient.h>

typedef void (*MsgCallback)(String topic, String payload);

class MqttManager {
public:
  WiFiClient   wifiClient;
  PubSubClient client;
  MsgCallback  userCallback = nullptr;

  const char* _server   = nullptr;
  int         _port     = 1883;
  const char* _user     = nullptr;
  const char* _pass     = nullptr;
  const char* _deviceId = nullptr;

  // ─── static 成員：儲存唯一實例指標 ─────────────
  static MqttManager* instance;

  MqttManager() : client(wifiClient) {
    instance = this;
  }

  // ─── static callback：PubSubClient 要求一般函式指標 ──
  static void staticCallback(char* topic, byte* payload, unsigned int len) {
    if (instance) instance->_onMessage(topic, payload, len);
  }

  void begin(const char* server, int port,
             const char* user, const char* pass,
             const char* deviceId) {
    _server   = server;
    _port     = port;
    _user     = user;
    _pass     = pass;
    _deviceId = deviceId;

    client.setServer(server, port);
    client.setCallback(MqttManager::staticCallback);  // 用 class 名稱限定
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
    bool ok = client.publish(topic, payload, true);
    Serial.printf("[MQTT] Publish %s -> %s\n", topic, ok ? "OK" : "FAIL");
    return ok;
  }

  void _onMessage(char* topic, byte* payload, unsigned int len) {
    String topicStr(topic);
    String payloadStr;
    payloadStr.reserve(len);
    for (unsigned int i = 0; i < len; i++) payloadStr += (char)payload[i];
    if (userCallback) userCallback(topicStr, payloadStr);
  }

  void _connect() {
    String clientId = String("esp32-") + _deviceId + "-" + String(millis());
    uint8_t retries = 0;

    while (!client.connected() && retries < 5) {
      Serial.printf("[MQTT] 連線至 %s:%d ...\n", _server, _port);

      bool ok;
      if (_user && strlen(_user) > 0) {
        ok = client.connect(clientId.c_str(), _user, _pass,
                            _willTopic().c_str(), 1, true, "{\"online\":false}");
      } else {
        ok = client.connect(clientId.c_str(), nullptr, nullptr,
                            _willTopic().c_str(), 1, true, "{\"online\":false}");
      }

      if (ok) {
        Serial.println(F("[MQTT] 連線成功"));
        _subscribe();
        String tp = String("bbcall/") + _deviceId + "/status";
        client.publish(tp.c_str(), "{\"online\":true}", true);
        return;
      } else {
        Serial.printf("[MQTT] 連線失敗，錯誤碼 %d\n", client.state());
        delay(3000 * (++retries));
      }
    }
  }

  void _subscribe() {
    String inbox = String("bbcall/") + _deviceId + "/inbox";
    client.subscribe(inbox.c_str());
    String music = String("bbcall/") + _deviceId + "/music";
    client.subscribe(music.c_str());
    Serial.printf("[MQTT] 訂閱：%s\n", inbox.c_str());
  }

  String _willTopic() {
    return String("bbcall/") + _deviceId + "/status";
  }
};

// ─── static 成員的定義（必須在 class 外面寫一次）──
MqttManager* MqttManager::instance = nullptr;

// ─── 全域實例 ─────────────────────────────────────
MqttManager MqttMgr;
