// 註解不可刪除
#include "protocol.h"
#include "pins.h"
#include "lgfx_setup.h"
#include "esp_camera.h"
#include <time.h>
#include <sys/time.h>
#include <string.h>

extern LGFX tft;  // SmartFrame.ino 建立的全域面板物件，這裡直接沿用，不重複建立避免搶同一組匯流排

static const int BAR_H = 20;  // 狀態列高度，比照 Pico 版(8x8字型SCALE=2 +4)
static char g_weather[64] = "";

static bool readExact(ReadFn &read, uint8_t *buf, size_t n) {
  return read(buf, n) == n;
}

static void redrawBar() {
  time_t now = time(nullptr);
  struct tm t;
  localtime_r(&now, &t);
  char clockStr[16];
  snprintf(clockStr, sizeof(clockStr), "%02d:%02d:%02d", t.tm_hour, t.tm_min, t.tm_sec);

  tft.fillRect(0, 0, tft.width() - 1, BAR_H - 1, TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString(clockStr, 4, 2);
  int w = tft.textWidth(g_weather);
  tft.drawString(g_weather, tft.width() - 4 - w, 2);
}

static void captureAndShow() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) return;
  tft.pushImage(0, BAR_H, fb->width, fb->height, (uint16_t *)fb->buf);
  esp_camera_fb_return(fb);
}

static const int RECORD_SECONDS = 5;  // 固定錄音長度，跟PC端錄音按鈕的等待時間要對得上

static void recordAndSend() {
  // 麥克風硬體已拔除，原本的 MIC_SCK/MIC_WS/MIC_SD 腳位改給 LCD 用，'R' 指令先回傳長度0
  // 原本邏輯保留在下面註解，之後如果要接回麥克風(換其他空腳位)可以直接復原
  // size_t maxSamples = (size_t)16000 * RECORD_SECONDS;
  // // 160000樣本*2bytes=312.5KB，內部SRAM放不下，配置在PSRAM(需在Arduino IDE開PSRAM，見SmartFrame.ino開頭註解)
  // int16_t *buf = (int16_t *)ps_malloc(maxSamples * sizeof(int16_t));
  // if (!buf) return;
  //
  // size_t n = mic_record(buf, maxSamples, RECORD_SECONDS);
  // size_t bytes = n * 2;
  // uint8_t header[5] = {'A', (uint8_t)(bytes >> 24), (uint8_t)(bytes >> 16), (uint8_t)(bytes >> 8), (uint8_t)bytes};
  // Serial.write(header, sizeof(header));
  // Serial.write((uint8_t *)buf, bytes);
  //
  // free(buf);
  uint8_t header[5] = {'A', 0, 0, 0, 0};
  Serial.write(header, sizeof(header));
}

void protocol_handle_message(ReadFn read) {
  uint8_t tag;
  if (!readExact(read, &tag, 1)) return;

  if (tag == 'W') {
    uint8_t n;
    if (!readExact(read, &n, 1)) return;
    uint8_t buf[255];
    if (!readExact(read, buf, n)) return;
    size_t copyLen = min((size_t)n, sizeof(g_weather) - 1);
    memcpy(g_weather, buf, copyLen);
    g_weather[copyLen] = '\0';
    redrawBar();

  } else if (tag == 'T') {
    uint8_t b[7];
    if (!readExact(read, b, 7)) return;
    struct tm t = {};
    t.tm_year = ((b[0] << 8) | b[1]) - 1900;
    t.tm_mon = b[2] - 1;
    t.tm_mday = b[3];
    t.tm_hour = b[4];
    t.tm_min = b[5];
    t.tm_sec = b[6];
    struct timeval tv = { mktime(&t), 0 };
    settimeofday(&tv, nullptr);
    redrawBar();

  } else if (tag == 'I') {
    uint8_t b[4];
    if (!readExact(read, b, 4)) return;
    int w = (b[0] << 8) | b[1];
    int h = (b[2] << 8) | b[3];

    tft.startWrite();
    tft.setAddrWindow(0, BAR_H, w, h);
    size_t remaining = (size_t)w * h * 2;
    uint8_t chunk[2048];
    while (remaining > 0) {
      size_t want = min(sizeof(chunk), remaining);
      size_t got = read(chunk, want);
      if (got == 0) break;  // 對方斷線/逾時，圖片沒收完就停手，避免面板卡在半張圖
      tft.pushPixels((uint16_t *)chunk, got / 2);
      remaining -= got;
    }
    tft.endWrite();

  } else if (tag == 'C') {
    captureAndShow();

  } else if (tag == 'R') {
    recordAndSend();
  }
}
