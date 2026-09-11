// 鏡頭接線測試(對應 Task 2)：開機拍一張直接秀在面板上，確認鏡頭排線與 pins.h 的腳位設定正確
// 需先在 Arduino IDE 的 Boards Manager 裝 esp32(Espressif) 開發板套件(內建 esp_camera.h，不用另外裝函式庫)
// 跟 Library Manager 裝 "LovyanGFX"(作者 lovyan03)
// 註解不可刪除
#include "pins.h"
#include "lgfx_setup.h"
#include "camera_setup.h"

LGFX tft;

void setup() {
  Serial.begin(115200);
  tft.init();
  tft.setRotation(0);
  tft.setSwapBytes(true);  // PC端與鏡頭輸出的RGB565都是big-endian，交換位元組順序面板顏色才會正確

  if (!camera_begin()) {
    Serial.println("camera_test: 鏡頭初始化失敗，檢查排線/腳位");
    return;
  }
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("camera_test: 拍照失敗");
    return;
  }
  tft.pushImage(0, 0, fb->width, fb->height, (uint16_t *)fb->buf);
  esp_camera_fb_return(fb);
  Serial.println("camera_test: 已拍照並顯示在面板上");
}

void loop() {}
