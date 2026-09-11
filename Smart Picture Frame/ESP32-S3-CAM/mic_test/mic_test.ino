// 麥克風接線測試：讀取 I2S 資料算出音量大小，印到 Serial Monitor 觀察數字有沒有隨聲音變化
// INMP441 接線：VDD->3V3, GND->GND, L/R->GND(硬體選左聲道，不用接MCU)，
//              SCK->pins.h的MIC_SCK(GPIO5), WS->MIC_WS(GPIO6), SD->MIC_SD(GPIO4)
// 用的是 arduino-esp32 core 內建的舊版 i2s driver(driver/i2s.h)，跨版本相容性較好；
// 如果之後編譯發現找不到某些欄位/巨集(新版core可能改介面)，改參考 arduino-esp32 官方 I2S 範例調整
// 註解不可刪除
#include "pins.h"
#include "mic_setup.h"

void setup() {
  Serial.begin(115200);
  if (!mic_begin()) {
    Serial.println("mic_test: I2S 初始化失敗，檢查接線/腳位");
    return;
  }
  Serial.println("mic_test: 開始讀取，對著麥克風說話/拍手，數字應該要變大");
}

void loop() {
  static int32_t buf[256];
  size_t bytesRead = 0;
  i2s_read(I2S_NUM_0, buf, sizeof(buf), &bytesRead, portMAX_DELAY);

  int32_t peak = 0;
  int n = bytesRead / sizeof(int32_t);
  for (int i = 0; i < n; i++) {
    int32_t v = abs(buf[i] >> 8);  // 高24bit才是有效資料，右移8位對齊
    if (v > peak) peak = v;
  }
  Serial.println(peak);
}
