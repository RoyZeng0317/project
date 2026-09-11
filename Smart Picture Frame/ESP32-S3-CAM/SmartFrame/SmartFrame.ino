// 整合韌體(對應 Task 4)：USB(CH340C) 序列與 BLE 同時監聽，哪邊先到就處理哪邊，
// 通訊協定跟 Raspberry pi pico/main.py 一致(見 protocol.h 開頭註解)
// 需先在 Arduino IDE 裝：Boards Manager 的 esp32(Espressif)套件、Library Manager 的 "LovyanGFX"(作者 lovyan03)
// 板子選 "ESP32S3 Dev Module"，並開啟 PSRAM(Tools > PSRAM > OPI PSRAM)
// 註解不可刪除
#include "pins.h"
#include "lgfx_setup.h"
#include "camera_setup.h"
#include "protocol.h"
#include "ble_service.h"

LGFX tft;

static size_t serialRead(uint8_t *buf, size_t len) {
  size_t n = 0;
  unsigned long t0 = millis();
  while (n < len) {
    if (Serial.available()) {
      n += Serial.readBytes(buf + n, len - n);
      t0 = millis();
    } else if (millis() - t0 > 2000) {
      break;  // 逾時就回傳目前讀到的量，protocol.cpp 會判斷這則訊息不完整
    }
  }
  return n;
}

void setup() {
  Serial.begin(115200);

  tft.init();
  tft.setRotation(0);  // 面板方向要跟 Pico 版一致的直向 320x480，實機測試後依畫面調整
  tft.setSwapBytes(true);  // PC端與鏡頭輸出的RGB565都是big-endian，交換位元組順序面板顏色才會正確
  tft.fillScreen(TFT_BLACK);

  // 診斷用暫時測試畫面，確認面板本身有沒有反應，確認完要刪掉
  tft.fillScreen(TFT_WHITE);
  delay(1000);
  tft.fillScreen(TFT_RED);
  delay(1000);
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE);
  tft.setCursor(10, 10);
  tft.print("SmartFrame OK");

  // 診斷用暫時停用(GPIO 9/10/11/12/13 跟 LCD 的 D9/D10/CS/RST/RS 衝突，確認完畫面正常後要復原)
  // if (!camera_begin()) {
  //   Serial.println("SmartFrame: 鏡頭初始化失敗，拍照功能('C'指令)不會有畫面");
  // }
  // 麥克風硬體已拔除，原本的 G4/G5/G6 改給 LCD 用，錄音功能('R'指令)不會有聲音

  ble_service_begin();

  // 開機短嗶3聲(比照 speaker_test.ino 的接線測試)，順便當作「喇叭正常」的開機提示音
  ledcAttach(SPK_PIN, 1000, 8);
  for (int i = 0; i < 3; i++) {
    ledcWrite(SPK_PIN, 128);
    delay(200);
    ledcWrite(SPK_PIN, 0);
    delay(200);
  }

  Serial.println("SmartFrame: 已啟動，等待 USB 序列或 BLE 資料...");
}

void loop() {
  if (Serial.available()) {
    protocol_handle_message(serialRead);
  }
  if (ble_service_available()) {
    protocol_handle_message(ble_service_read);
  }
}
