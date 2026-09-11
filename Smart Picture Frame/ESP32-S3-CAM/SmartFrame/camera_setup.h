// 鏡頭初始化，camera_test.ino 與 SmartFrame.ino 共用
// Arduino 不同 sketch 資料夾之間沒辦法共用 .cpp(不會被自動編譯進去)，只有標頭檔用
// #include 這種純文字貼入的方式才能跨資料夾共用，所以寫成 header-only 的 static function，
// 避免同一段鏡頭設定在兩個 .ino 各寫一份、之後改一邊忘記改另一邊
// 使用前需先 #include "pins.h"(取得 CAM_PIN_* 腳位定義)
#pragma once
#include "esp_camera.h"

static inline bool camera_begin() {
  camera_config_t c = {};
  c.pin_pwdn = CAM_PIN_PWDN;
  c.pin_reset = CAM_PIN_RESET;
  c.pin_xclk = CAM_PIN_XCLK;
  c.pin_sscb_sda = CAM_PIN_SIOD;  // 若編譯報這個欄位名稱不存在，改試 pin_sccb_sda(新版 esp32-camera 改過欄位名)
  c.pin_sscb_scl = CAM_PIN_SIOC;  // 同上，改試 pin_sccb_scl
  c.pin_d7 = CAM_PIN_D7; c.pin_d6 = CAM_PIN_D6; c.pin_d5 = CAM_PIN_D5; c.pin_d4 = CAM_PIN_D4;
  c.pin_d3 = CAM_PIN_D3; c.pin_d2 = CAM_PIN_D2; c.pin_d1 = CAM_PIN_D1; c.pin_d0 = CAM_PIN_D0;
  c.pin_vsync = CAM_PIN_VSYNC;
  c.pin_href = CAM_PIN_HREF;
  c.pin_pclk = CAM_PIN_PCLK;
  c.xclk_freq_hz = 20000000;
  c.ledc_timer = LEDC_TIMER_0;
  c.ledc_channel = LEDC_CHANNEL_0;
  c.pixel_format = PIXFORMAT_RGB565;
  c.frame_size = FRAMESIZE_HVGA;  // 480x320，跟面板解析度一致
  c.fb_count = 1;
  c.fb_location = CAMERA_FB_IN_PSRAM;
  c.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  return esp_camera_init(&c) == ESP_OK;
}
