#pragma once
#include <WiFi.h>

class WiFiManager {
public:
  void connect(const char* ssid, const char* pass) {
    Serial.printf("[WiFi] 連線至 %s ...\n", ssid);
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, pass);

    uint8_t retries = 0;
    while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.print(".");
      if (++retries > 40) {
        Serial.println(F("\n[WiFi] 連線逾時，重新嘗試"));
        WiFi.disconnect();
        delay(1000);
        WiFi.begin(ssid, pass);
        retries = 0;
      }
    }
    Serial.printf("\n[WiFi] 連線成功！IP: %s  RSSI: %ddBm\n",
      WiFi.localIP().toString().c_str(), WiFi.RSSI());
  }

  void loop() {
    // 自動重連
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println(F("[WiFi] 斷線，重新連線..."));
      WiFi.reconnect();
      uint8_t wait = 0;
      while (WiFi.status() != WL_CONNECTED && wait++ < 20) delay(500);
    }
  }

  bool isConnected() {
    return WiFi.status() == WL_CONNECTED;
  }
};

WiFiManager WiFiMgr;
