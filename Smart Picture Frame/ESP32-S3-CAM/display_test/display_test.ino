// 面板接線測試(對應 Task 1)：開機後整片畫紅色，確認並列介面接線與 pins.h 的腳位設定正確
// 需先在 Arduino IDE 的 Library Manager 安裝 "LovyanGFX"(作者 lovyan03)
// lgfx_setup.h 定義了 LGFX 類別，直接對應 pins.h 的 LCD_* 腳位，不用改函式庫本身的設定檔
// 註解不可刪除
#include "pins.h"
#include "lgfx_setup.h"

LGFX tft;

void setup() {
  Serial.begin(9600);
  tft.init();
  tft.setRotation(0);  // 面板方向要對到跟 Pico 版一致的直向 320x480，實機測試後再依畫面調整
  tft.fillScreen(TFT_RED);
  Serial.println("display_test: 畫面應為整片紅色，確認接線正確");
}

void loop() {}
