// 麥克風初始化與錄音，mic_test.ino 與 SmartFrame.ino/protocol.cpp 共用
// header-only 的原因跟 camera_setup.h 一樣：Arduino 不同 sketch 資料夾間沒辦法共用 .cpp
// 使用前需先 #include "pins.h"(取得 MIC_* 腳位定義)
#pragma once
#include "driver/i2s.h"

static inline bool mic_begin() {
  i2s_config_t config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = 16000,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,  // INMP441 資料時槽是32-bit(有效精度24-bit)，用32-bit讀取相容性較好
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = 0,
    .dma_buf_count = 4,
    .dma_buf_len = 256,
  };
  i2s_pin_config_t pins = {
    .bck_io_num = MIC_SCK,
    .ws_io_num = MIC_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = MIC_SD,
  };
  return i2s_driver_install(I2S_NUM_0, &config, 0, NULL) == ESP_OK &&
         i2s_set_pin(I2S_NUM_0, &pins) == ESP_OK;
}

// 錄 seconds 秒的 16kHz 16-bit mono PCM 到 out(呼叫端配置好至少 16000*seconds 個樣本的空間)，
// 回傳實際錄到的樣本數
static inline size_t mic_record(int16_t *out, size_t maxSamples, int seconds) {
  size_t total = 0;
  size_t targetSamples = (size_t)16000 * seconds;
  if (targetSamples > maxSamples) targetSamples = maxSamples;
  int32_t raw[256];
  while (total < targetSamples) {
    size_t bytesRead = 0;
    i2s_read(I2S_NUM_0, raw, sizeof(raw), &bytesRead, portMAX_DELAY);
    int n = bytesRead / sizeof(int32_t);
    for (int i = 0; i < n && total < targetSamples; i++) {
      out[total++] = (int16_t)(raw[i] >> 16);  // 取32-bit時槽的高16位當16-bit PCM，縮小一半資料量
    }
  }
  return total;
}
