// ============================================================================
// Arduino Mega 2560 + 3.5吋 TFT ILI9481 智慧相框程式
//
// 功能說明：
// 1. 【圖片寫入與顯示】：
//    - USB 序列埠即時串流（支援 photos/ 下的所有 jpg, png, webp, gif 動畫）
//    - 內建 Flash (PROGMEM) 樣品圖片，開機無連線時立即顯示
//    - 支援面板內建 MicroSD 卡（插槽在 36-pin 模組背面，CS=Pin 53），離線讀取 .bmp/.bin
// 2. 【時間顯示】：
//    - 頂部狀態列即時顯示數位時鐘 (HH:MM:SS) 與日期
//    - 使用 millis() 內部軟體時鐘精準走時（每秒更新無閃爍）
//    - 開機以編譯時間 (__TIME__, __DATE__) 自動初始化
//    - 支援電腦端透過 USB 序列埠 ('T' 指令) 動態精準校時
//    - 支援顯示氣溫與天氣資訊 ('W' 指令)
//
// 螢幕類型說明：
// 1. 若使用的是 36-pin 雙排直插式模組（插在 Mega 後端 22~41 號腳位）：
//    USE_MEGA_16BIT_SHIELD 設為 1 (預設，極速 16-bit 平行傳輸)
// 2. 若使用的是標準 Arduino Uno 規格 8-bit Shield（插在 Uno 腳位 D2~D9、A0~A4）：
//    USE_MEGA_16BIT_SHIELD 設為 0
// ============================================================================

#define USE_MEGA_16BIT_SHIELD 1
#define ENABLE_SD_CARD        1  // 1: 啟用 MicroSD 卡讀取支援 (Pin 53), 0: 關閉
#define SCREEN_ROTATION       1  // 1: 橫向 (480x320), 0: 直向 (320x480)
#define SERIAL_BAUD           500000  // 2026-09-09：切換速度已經改用本地 TF 卡輪播解決(見 scanLocalPhotos/
                                       // showLocalPhoto)，USB 序列埠只剩天氣/時間/偶爾一張新照片這種低頻推播，
                                       // 不再需要衝高鮑率；曾試過 2000000，這片板子的 USB-序列晶片撐不住、
                                       // 會出現 [ERR] Image Stream Timeout 掉位元組，退回實測穩定的 500000；
                                       // 電腦端 mega_frame_sender.py 的 BAUD 要跟這裡同步改

#include <Arduino.h>
#include <Adafruit_GFX.h>
#include <avr/pgmspace.h>

#if USE_MEGA_16BIT_SHIELD
  #include "ILI9481_Mega.h"
  ILI9481_Mega tft;
#else
  #include <MCUFRIEND_kbv.h>
  MCUFRIEND_kbv tft;
#endif

#if ENABLE_SD_CARD
  #include <SPI.h>
  #include <SD.h>
  #define SD_CS_PIN 53
  bool g_sdAvailable = false;
#endif

#include "sample_photo.h"

// 常用顏色定義 (RGB565)
#define BLACK       0x0000
#define BLUE        0x001F
#define RED         0xF800
#define GREEN       0x07E0
#define CYAN        0x07FF
#define MAGENTA     0xF81F
#define YELLOW      0xFFE0
#define WHITE       0xFFFF
#define BAR_BG      0x0000
#define BORDER_COL  0x2104

// 狀態列高度 (上方留給時鐘與天氣，下方為照片顯示區)
const int BAR_H = 24;

// 時間與天氣全域變數
uint16_t g_year  = 2026;
uint8_t  g_month = 9;
uint8_t  g_day   = 9;
uint8_t  g_hour  = 12;
uint8_t  g_min   = 0;
uint8_t  g_sec   = 0;
char g_weather[32] = "Smart Frame";
bool g_timeSynced = false;

// 記錄前一次更新的時間字串，避免不必要的重繪
static char g_lastTimeStr[12] = "";

// 2026-09-09：本地 TF 卡輪播——電腦端 mega_flash_sd.py 會把 photos/ 轉成 P000.BIN、P001.BIN...
// 存在卡的根目錄，開機掃到幾張就在這幾張之間輪播，直接讀卡秒切、不受 USB 序列埠傳輸速度限制；
// 即時推播('I' 指令，例如天氣圖或新拍的照片)還是照舊立刻顯示，顯示後會讓本地輪播的計時重新起算，
// 讓即時推的圖至少能撐滿一輪 PHOTO_DWELL_MS 才會被本地輪播蓋掉
#if ENABLE_SD_CARD
const unsigned long PHOTO_DWELL_MS = 5000;
const int MAX_SD_PHOTOS = 50;  // 只是限制開機掃描檔案的時間，SD 卡容量本身夠大
int g_sdPhotoCount = 0;
int g_sdPhotoIdx = 0;
unsigned long g_lastPhotoTick = 0;
#endif

// 函式宣告
void initTimeFromCompile();
void tickOneSecond();
void updateStatusBar(bool forceRedraw = false);
void drawSamplePhoto();
void handleSerialCommands();
void handleTimePacket();
void handleWeatherPacket();
void handleImagePacket();
void handleListPacket();
void handleReadPacket();
#if ENABLE_SD_CARD
bool drawBmpFromSD(const char *filename);
bool drawBinFromSD(const char *filename, uint16_t w, uint16_t h);
void scanLocalPhotos();
void showLocalPhoto(int idx);
#endif

// ============================================================================
// setup 初始化
// ============================================================================
void setup() {
  Serial.begin(SERIAL_BAUD);
  Serial.println(F("========================================"));
  Serial.println(F(" Arduino Mega 2560 Smart Picture Frame "));
  Serial.println(F("========================================"));

  // 1. 初始化 TFT 螢幕
#if USE_MEGA_16BIT_SHIELD
  Serial.println(F("[TFT] Mode: 16-bit Parallel (Pins 22~41)"));
  tft.begin();
#else
  Serial.println(F("[TFT] Mode: 8-bit Shield (MCUFRIEND_kbv)"));
  uint16_t id = tft.readID();
  if (id == 0xD3D3 || id == 0x0000 || id == 0xFFFF) id = 0x9481;
  tft.begin(id);
#endif

  tft.setRotation(SCREEN_ROTATION);
  tft.fillScreen(BLACK);

  // 2. 從編譯時間初始化時鐘
  initTimeFromCompile();

  // 3. 繪製頂部狀態列
  updateStatusBar(true);

  // 4. 繪製開機預設樣品圖片 (photos/ 內建快取)
  drawSamplePhoto();

  // 5. 初始化 MicroSD 卡 (選用)
#if ENABLE_SD_CARD
  pinMode(SD_CS_PIN, OUTPUT);
  if (SD.begin(SD_CS_PIN)) {
    g_sdAvailable = true;
    Serial.println(F("[SD] SD 卡掛載成功！可離線播放 SD 卡圖片"));
  } else {
    g_sdAvailable = false;
    Serial.println(F("[SD] 未偵測到 SD 卡或初始化失敗，等待 USB 序列埠傳輸"));
  }
  if (g_sdAvailable) {
    scanLocalPhotos();
    if (g_sdPhotoCount > 0) {
      showLocalPhoto(0);
    }
  }
#endif

  Serial.println(F("[READY] 系統就緒，等待指令 ('I': 圖片, 'T': 時間, 'W': 天氣, 'L': 列出SD卡, 'R': 讀SD卡)"));
}

// ============================================================================
// loop 主迴圈
// ============================================================================
unsigned long lastSecondTick = 0;

void loop() {
  // 1. 處理序列埠傳來的即時資料 (照片 / 時間 / 天氣)
  handleSerialCommands();

  // 2. 每秒更新時鐘；2026-09-09：接收一張圖片時 handleImagePacket() 會整個卡住好幾秒，
  // 原本這裡用 if 只補 1 秒、其餘被卡住吃掉的秒數就憑空消失，時鐘越走越慢；
  // 改成 while 把卡住期間漏掉的秒數一次補齊，避免時間持續累積誤差
  unsigned long now = millis();
  bool ticked = false;
  while (now - lastSecondTick >= 1000) {
    lastSecondTick += 1000;
    tickOneSecond();
    ticked = true;
  }
  if (ticked) {
    updateStatusBar(false);
  }

  // 3. 沒有即時推播時，本地從 TF 卡輪播快取圖，秒切不受序列埠傳輸速度限制
#if ENABLE_SD_CARD
  if (g_sdPhotoCount > 0) {
    unsigned long nowPhoto = millis();
    if (nowPhoto - g_lastPhotoTick >= PHOTO_DWELL_MS) {
      g_lastPhotoTick = nowPhoto;
      showLocalPhoto((g_sdPhotoIdx + 1) % g_sdPhotoCount);
    }
  }
#endif
}

// ============================================================================
// 時間引擎
// ============================================================================
void initTimeFromCompile() {
  char s_month[5];
  int year, day;
  static const char month_names[] = "JanFebMarAprMayJunJulAugSepOctNovDec";
  if (sscanf(__DATE__, "%s %d %d", s_month, &day, &year) == 3) {
    char *p = strstr(month_names, s_month);
    if (p) {
      g_month = ((p - month_names) / 3) + 1;
      g_day = day;
      g_year = year;
    }
  }
  int h, m, s;
  if (sscanf(__TIME__, "%d:%d:%d", &h, &m, &s) == 3) {
    g_hour = h;
    g_min  = m;
    g_sec  = s;
  }
}

void tickOneSecond() {
  g_sec++;
  if (g_sec >= 60) {
    g_sec = 0;
    g_min++;
    if (g_min >= 60) {
      g_min = 0;
      g_hour++;
      if (g_hour >= 24) {
        g_hour = 0;
        g_day++;
        static const uint8_t daysInMonth[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
        uint8_t dim = daysInMonth[(g_month - 1) % 12];
        if (g_month == 2 && ((g_year % 4 == 0 && g_year % 100 != 0) || (g_year % 400 == 0))) {
          dim = 29;
        }
        if (g_day > dim) {
          g_day = 1;
          g_month++;
          if (g_month > 12) {
            g_month = 1;
            g_year++;
          }
        }
      }
    }
  }
}

void updateStatusBar(bool forceRedraw) {
  char timeBuf[12];
  snprintf(timeBuf, sizeof(timeBuf), "%02d:%02d:%02d", g_hour, g_min, g_sec);

  if (!forceRedraw && strcmp(timeBuf, g_lastTimeStr) == 0) {
    return;
  }
  strncpy(g_lastTimeStr, timeBuf, sizeof(g_lastTimeStr));

  if (forceRedraw) {
    tft.fillRect(0, 0, tft.width(), BAR_H, BAR_BG);
    tft.drawFastHLine(0, BAR_H - 1, tft.width(), BORDER_COL);
  }

  // 1. 左側：數位時間 (HH:MM:SS)
  tft.setTextSize(2);
  tft.setTextColor(WHITE, BAR_BG);
  tft.setCursor(6, 4);
  tft.print(timeBuf);

  // 2. 橫向螢幕時在中間顯示日期 (YYYY-MM-DD)
  if (tft.width() >= 400) {
    char dateBuf[16];
    snprintf(dateBuf, sizeof(dateBuf), "%04d-%02d-%02d", g_year, g_month, g_day);
    tft.setTextSize(1);
    tft.setTextColor(CYAN, BAR_BG);
    tft.setCursor(110, 8);
    tft.print(dateBuf);
  }

  // 3. 右側：天氣或狀態文字
  tft.setTextSize(2);
  tft.setTextColor(YELLOW, BAR_BG);
  int textLen = strlen(g_weather);
  int textW = textLen * 12;
  int startX = tft.width() - textW - 8;
  if (startX < 220) startX = 220;
  tft.setCursor(startX, 4);
  tft.print(g_weather);
}

// ============================================================================
// 內建照片繪製 (開機預設)
// ============================================================================
void drawSamplePhoto() {
  int16_t w = SAMPLE_IMAGE_WIDTH;
  int16_t h = SAMPLE_IMAGE_HEIGHT;

  int16_t x0 = (tft.width() - w) / 2;
  int16_t y0 = BAR_H + ((tft.height() - BAR_H) - h) / 2;

  // 清除照片顯示區域為黑色
  tft.fillRect(0, BAR_H, tft.width(), tft.height() - BAR_H, BLACK);

#if USE_MEGA_16BIT_SHIELD
  tft.setAddrWindow(x0, y0, x0 + w - 1, y0 + h - 1);
  tft.pushPixels_P(sample_image_data, (uint32_t)w * h);
#else
  for (int16_t y = 0; y < h; y++) {
    for (int16_t x = 0; x < w; x++) {
      uint16_t color = pgm_read_word(&sample_image_data[y * w + x]);
      tft.drawPixel(x0 + x, y0 + y, color);
    }
  }
#endif

  // 外框裝飾
  tft.drawRect(x0 - 1, y0 - 1, w + 2, h + 2, CYAN);
}

// ============================================================================
// 序列埠指令處理 (相容 usb_frame_sender.py / mega_frame_sender.py)
// ============================================================================
void handleSerialCommands() {
  while (Serial.available() > 0) {
    uint8_t tag = Serial.read();
    if (tag == 'T') {
      handleTimePacket();
    } else if (tag == 'W') {
      handleWeatherPacket();
    } else if (tag == 'I') {
      handleImagePacket();
    } else if (tag == 'L') {
      handleListPacket();
    } else if (tag == 'R') {
      handleReadPacket();
    }
  }
}

// 'T' + 7 bytes: [year_hi, year_lo, month, day, hour, min, sec]
void handleTimePacket() {
  uint8_t b[7];
  size_t n = Serial.readBytes((char*)b, 7);
  if (n == 7) {
    g_year   = ((uint16_t)b[0] << 8) | b[1];
    g_month  = b[2];
    g_day    = b[3];
    g_hour   = b[4];
    g_min    = b[5];
    g_sec    = b[6];
    g_timeSynced = true;
    updateStatusBar(true);
    Serial.println(F("[ACK] Time Synced"));
  }
}

// 'W' + 1 byte len + text
void handleWeatherPacket() {
  uint8_t len = 0;
  if (Serial.readBytes((char*)&len, 1) == 1 && len > 0) {
    uint8_t toRead = min(len, (uint8_t)(sizeof(g_weather) - 1));
    size_t n = Serial.readBytes(g_weather, toRead);
    g_weather[n] = '\0';
    for (uint8_t i = toRead; i < len; i++) {
      while (!Serial.available());
      Serial.read();
    }
    updateStatusBar(true);
    Serial.println(F("[ACK] Weather Updated"));
  }
}

// 'I' + 4 bytes: [w_hi, w_lo, h_hi, h_lo] + (w * h * 2 bytes RGB565)
void handleImagePacket() {
  uint8_t header[4];
  unsigned long startWait = millis();
  while (Serial.available() < 4) {
    if (millis() - startWait > 2000) return;
  }
  Serial.readBytes((char*)header, 4);

  uint16_t w = ((uint16_t)header[0] << 8) | header[1];
  uint16_t h = ((uint16_t)header[2] << 8) | header[3];

  if (w == 0 || h == 0 || w > tft.width() || h > (tft.height() - BAR_H)) {
    Serial.println(F("[ERR] Invalid Dimensions"));
    return;
  }

  int16_t x0 = (tft.width() - w) / 2;
  int16_t y0 = BAR_H + ((tft.height() - BAR_H) - h) / 2;

  // 若圖片小於可用區域，先將背景刷黑
  if (w < tft.width() || h < (tft.height() - BAR_H)) {
    tft.fillRect(0, BAR_H, tft.width(), tft.height() - BAR_H, BLACK);
  }

#if USE_MEGA_16BIT_SHIELD
  tft.setAddrWindow(x0, y0, x0 + w - 1, y0 + h - 1);
  PORTD |= (1 << 7); // RS HIGH (資料模式)
#else
  tft.setAddrWindow(x0, y0, x0 + w - 1, y0 + h - 1);
#endif

  uint8_t buf[64];
  uint32_t totalBytes = (uint32_t)w * h * 2;
  uint32_t bytesRead = 0;
  unsigned long lastByteTime = millis();

  while (bytesRead < totalBytes) {
    int avail = Serial.available();
    if (avail >= 2) {
      int want = min(avail, (int)sizeof(buf));
      want &= ~1; // 保持 2 的倍數，確保 16-bit 像素完整
      if ((uint32_t)want > (totalBytes - bytesRead)) {
        want = (int)(totalBytes - bytesRead);
      }
      int n = Serial.readBytes((char*)buf, want);
      if (n > 0) {
#if USE_MEGA_16BIT_SHIELD
        tft.pushPixelsBytes(buf, n);
#else
        for (int i = 0; i < n; i += 2) {
          uint16_t color = ((uint16_t)buf[i] << 8) | buf[i + 1];
          tft.pushColors(&color, 1, false);
        }
#endif
        bytesRead += n;
        lastByteTime = millis();
      }
    } else {
      if (millis() - lastByteTime > 3000) {
        Serial.println(F("[ERR] Image Stream Timeout"));
        break;
      }
    }
  }

  if (bytesRead == totalBytes) {
    Serial.println(F("[ACK] Image OK"));
#if ENABLE_SD_CARD
    g_lastPhotoTick = millis();  // 讓即時推播的圖至少能撐滿一輪 PHOTO_DWELL_MS 才被本地輪播蓋掉
#endif
  }
}

static void sendZeroSize() {
  uint8_t z[4] = {0, 0, 0, 0};
  Serial.write(z, 4);
}

// 'L'：電腦端 mega_deploy_gui.py 用，卡片留在面板上不用拔，直接回傳開機時 scanLocalPhotos()
// 掃到的本地快取圖張數(1 byte)，GUI 收到後自己拼出 P000.BIN、P001.BIN... 的清單
void handleListPacket() {
#if ENABLE_SD_CARD
  Serial.write((uint8_t)g_sdPhotoCount);
#else
  Serial.write((uint8_t)0);
#endif
}

// 'R' + 1 byte 檔名長度 + 檔名：電腦端預覽用，回傳 4 bytes 大端檔案大小(0 代表沒有 SD 卡或
// 找不到檔案)，接著才是原始位元組內容；純粹讀出來回傳，不解碼也不顯示在面板上
void handleReadPacket() {
  uint8_t len = 0;
  if (Serial.readBytes((char*)&len, 1) != 1 || len == 0 || len > 12) {
    sendZeroSize();
    return;
  }
  char fname[13];
  size_t n = Serial.readBytes(fname, len);
  fname[n] = '\0';

#if ENABLE_SD_CARD
  if (g_sdAvailable) {
    File f = SD.open(fname);
    if (f) {
      uint32_t size = f.size();
      uint8_t header[4] = {(uint8_t)(size >> 24), (uint8_t)(size >> 16), (uint8_t)(size >> 8), (uint8_t)size};
      Serial.write(header, 4);
      uint8_t buf[64];
      uint32_t sent = 0;
      while (sent < size) {
        uint32_t remain = size - sent;
        uint8_t want = remain > sizeof(buf) ? sizeof(buf) : (uint8_t)remain;  // 避免 AVR 16-bit int 在大檔案時溢位
        int chunk = f.read(buf, want);
        if (chunk <= 0) break;
        Serial.write(buf, chunk);
        sent += chunk;
      }
      f.close();
      return;
    }
  }
#endif
  sendZeroSize();
}

// ============================================================================
// MicroSD 卡讀取支援 (選用功能)
// ============================================================================
#if ENABLE_SD_CARD
static uint16_t read16(File &f) {
  uint16_t res;
  f.read((uint8_t*)&res, 2);
  return res;
}

static uint32_t read32(File &f) {
  uint32_t res;
  f.read((uint8_t*)&res, 4);
  return res;
}

bool drawBmpFromSD(const char *filename) {
  if (!g_sdAvailable) return false;
  File f = SD.open(filename);
  if (!f) return false;

  if (read16(f) != 0x4D42) { f.close(); return false; } // BM signature
  read32(f); read32(f);
  uint32_t offset = read32(f);
  read32(f);
  int32_t bmpW = read32(f);
  int32_t bmpH = read32(f);
  uint16_t planes = read16(f);
  uint16_t depth = read16(f);
  uint32_t comp = read32(f);

  if (planes != 1 || depth != 24 || comp != 0) { f.close(); return false; }

  bool flip = true;
  if (bmpH < 0) { bmpH = -bmpH; flip = false; }

  int16_t w = min((int16_t)bmpW, (int16_t)tft.width());
  int16_t h = min((int16_t)bmpH, (int16_t)(tft.height() - BAR_H));
  int16_t x0 = (tft.width() - w) / 2;
  int16_t y0 = BAR_H + ((tft.height() - BAR_H) - h) / 2;

  uint32_t rowSize = (bmpW * 3 + 3) & ~3;
  uint8_t rowBuf[96];

  for (int16_t row = 0; row < h; row++) {
    uint32_t pos = offset + (flip ? (uint32_t)(bmpH - 1 - row) : (uint32_t)row) * rowSize;
    f.seek(pos);

#if USE_MEGA_16BIT_SHIELD
    tft.setAddrWindow(x0, y0 + row, x0 + w - 1, y0 + row);
    PORTD |= (1 << 7);
#endif

    int16_t col = 0;
    while (col < w) {
      int16_t wantPx = min((int16_t)(w - col), (int16_t)(sizeof(rowBuf) / 3));
      int16_t bytesRead = f.read(rowBuf, wantPx * 3);
      if (bytesRead <= 0) break;

      for (int16_t i = 0; i < bytesRead; i += 3) {
        uint16_t c = tft.color565(rowBuf[i + 2], rowBuf[i + 1], rowBuf[i]); // BGR -> RGB565
#if USE_MEGA_16BIT_SHIELD
        tft.pushPixel(c);
#else
        tft.drawPixel(x0 + col + (i / 3), y0 + row, c);
#endif
      }
      col += wantPx;
    }
  }

  f.close();
  return true;
}

bool drawBinFromSD(const char *filename, uint16_t w, uint16_t h) {
  if (!g_sdAvailable) return false;
  File f = SD.open(filename);
  if (!f) return false;

  int16_t x0 = (tft.width() - w) / 2;
  int16_t y0 = BAR_H + ((tft.height() - BAR_H) - h) / 2;

#if USE_MEGA_16BIT_SHIELD
  tft.setAddrWindow(x0, y0, x0 + w - 1, y0 + h - 1);
  PORTD |= (1 << 7);
#endif

  uint8_t buf[64];
  while (f.available()) {
    int n = f.read(buf, sizeof(buf));
    if (n <= 0) break;
#if USE_MEGA_16BIT_SHIELD
    tft.pushPixelsBytes(buf, n);
#else
    for (int i = 0; i < n; i += 2) {
      uint16_t c = ((uint16_t)buf[i] << 8) | buf[i + 1];
      tft.pushColors(&c, 1, false);
    }
#endif
  }
  f.close();
  return true;
}

// 開機時掃描電腦端 mega_flash_sd.py 燒進 TF 卡根目錄的 P000.BIN、P001.BIN...，找到幾張算幾張，
// 檔案不連號(例如只有 P000.BIN、P002.BIN)就在第一個缺號處停止，跟 mega_flash_sd.py 每次都
// 從 0 開始連號寫入、並清掉多餘舊檔的行為互相配合
void scanLocalPhotos() {
  char fname[13];
  g_sdPhotoCount = 0;
  while (g_sdPhotoCount < MAX_SD_PHOTOS) {
    snprintf(fname, sizeof(fname), "P%03d.BIN", g_sdPhotoCount);
    if (!SD.exists(fname)) break;
    g_sdPhotoCount++;
  }
  Serial.print(F("[SD] 找到本地快取圖 "));
  Serial.print(g_sdPhotoCount);
  Serial.println(F(" 張"));
}

void showLocalPhoto(int idx) {
  char fname[13];
  snprintf(fname, sizeof(fname), "P%03d.BIN", idx);
  if (drawBinFromSD(fname, tft.width(), tft.height() - BAR_H)) {
    g_sdPhotoIdx = idx;
  }
}
#endif

