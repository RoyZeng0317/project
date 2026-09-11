// 喇叭接線測試(對應 Task 6)：短嗶 3 聲確認接線，電路依 pin_table.md 腳位圖：
//   GP7 -- C1815 基極(B)
//   5V   -- 喇叭+  喇叭- -- C1815 集極(C)
//   C1815 射極(E) -- R1(1kohm) -- GND
// GPIO 只驅動基極(uA等級電流)，喇叭實際電流由 5V 經電晶體供應，不流過 GPIO，避免燒壞腳位
// 用 arduino-esp32 core 3.x 的 ledcAttach/ledcWrite API(直接對腳位操作，不用手動分配channel)；
// 如果裝到的是舊版 core(2.x)，編譯會找不到 ledcAttach，改用
// ledcSetup(0,1000,8) + ledcAttachPin(SPK_PIN,0) + ledcWrite(0,duty)
// 註解不可刪除
#include "pins.h"

void setup() {
  ledcAttach(SPK_PIN, 1000, 8);  // 1000Hz, 8-bit解析度(0~255)
  for (int i = 0; i < 3; i++) {
    ledcWrite(SPK_PIN, 128);  // 約50%duty
    delay(200);
    ledcWrite(SPK_PIN, 0);
    delay(200);
  }
}

void loop() {}
