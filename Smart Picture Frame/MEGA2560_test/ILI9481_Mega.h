#pragma once
#include <Arduino.h>
#include <Adafruit_GFX.h>

// ============================================================================
// Arduino Mega 2560 專用 16-bit ILI9481 TFT LCD 驅動器
// 適用插槽：Mega 2560 後端 36-pin (2x18) 雙排排針 (Pins 22~41 + 5V + GND)
//
// 腳位對應表 (硬體直插)：
// DB8~DB15 : Pins 22~29 (ATmega2560 PORTA)
// DB0~DB7  : Pins 37~30 (ATmega2560 PORTC, 37=D0, 36=D1... 30=D7)
// LCD_RS   : Pin 38     (PD7, 指令/資料選擇：0=指令, 1=資料)
// LCD_WR   : Pin 39     (PG2, 寫入時脈，低電位有效)
// LCD_CS   : Pin 40     (PG1, 片選，低電位有效)
// LCD_RST  : Pin 41     (PG0, 重置，低電位有效)
// ============================================================================

class ILI9481_Mega : public Adafruit_GFX {
public:
  ILI9481_Mega() : Adafruit_GFX(320, 480) {}

  void reset() {
    PORTG &= ~(1 << 0); // RST LOW
    delay(20);
    PORTG |= (1 << 0);  // RST HIGH
    delay(150);
  }

  uint16_t readID() {
    return 0x9481; // 此面板無接 RD 讀取腳位，直接回傳 ILI9481 ID
  }

  static inline uint16_t color565(uint8_t r, uint8_t g, uint8_t b) {
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
  }

  void begin(uint16_t id = 0x9481) {
    (void)id; // 保留相容性參數

    // 設定資料埠為輸出
    DDRA = 0xFF; // DB8~DB15
    DDRC = 0xFF; // DB0~DB7

    // 設定控制線為輸出
    DDRD |= (1 << 7);                        // Pin 38 (PD7) LCD_RS
    DDRG |= (1 << 2) | (1 << 1) | (1 << 0);  // Pin 39 (PG2) WR, Pin 40 (PG1) CS, Pin 41 (PG0) RST

    // 初始狀態
    PORTG |= (1 << 2) | (1 << 0); // WR=1, RST=1
    PORTG &= ~(1 << 1);           // CS=0 (持續致能)
    PORTD |= (1 << 7);            // RS=1

    reset();

    // 1. 喚醒
    writeCommand(0x11); // Sleep Out
    delay(150);

    // 2. 電源設定 (Power Setting)
    writeCommand(0xD0);
    writeData(0x07);
    writeData(0x42);
    writeData(0x18);

    // 3. VCOM 控制
    writeCommand(0xD1);
    writeData(0x00);
    writeData(0x07);
    writeData(0x10);

    // 4. 正常模式電源
    writeCommand(0xD2);
    writeData(0x01);
    writeData(0x02);

    // 5. 面板驅動設定 (Panel Driving Setting)
    writeCommand(0xC0);
    writeData(0x10);
    writeData(0x3B);
    writeData(0x00);
    writeData(0x02);
    writeData(0x11);

    // 6. 畫面更新頻率 (Frame Rate)
    writeCommand(0xC5);
    writeData(0x03);

    // 7. Gamma 校準
    writeCommand(0xC8);
    writeData(0x00); writeData(0x32); writeData(0x36); writeData(0x45);
    writeData(0x06); writeData(0x16); writeData(0x37); writeData(0x75);
    writeData(0x77); writeData(0x54); writeData(0x0C); writeData(0x00);

    // 8. 介面像素格式 (16-bit RGB565)
    writeCommand(0x3A);
    writeData(0x55);

    // 預設橫向顯示 (480x320)
    setRotation(1);

    delay(120);

    // 9. 開啟顯示 (Display ON)
    writeCommand(0x29);
    delay(25);
  }

  void setRotation(uint8_t r) override {
    Adafruit_GFX::setRotation(r);
    writeCommand(0x36); // MADCTL
    switch (rotation) {
      case 0: // 直向 (320x480)
        writeData(0x48);
        break;
      case 1: // 橫向 (480x320)
        writeData(0x28);
        break;
      case 2: // 直向 翻轉 180 度
        writeData(0x88);
        break;
      case 3: // 橫向 翻轉 180 度
        writeData(0xE8);
        break;
    }
  }

  void drawPixel(int16_t x, int16_t y, uint16_t color) override {
    if (x < 0 || x >= _width || y < 0 || y >= _height) return;
    setAddrWindow(x, y, x, y);
    PORTD |= (1 << 7); // RS HIGH
    writeBus16(color);
  }

  void fillRect(int16_t x, int16_t y, int16_t w, int16_t h, uint16_t color) override {
    if (x >= _width || y >= _height || w <= 0 || h <= 0) return;
    if (x < 0) { w += x; x = 0; }
    if (y < 0) { h += y; y = 0; }
    if (x + w > _width) w = _width - x;
    if (y + h > _height) h = _height - y;
    if (w <= 0 || h <= 0) return;

    setAddrWindow(x, y, x + w - 1, y + h - 1);
    PORTD |= (1 << 7); // RS HIGH (Data)
    PORTA = color >> 8;
    PORTC = color & 0xFF;
    uint32_t total = (uint32_t)w * h;
    while (total--) {
      PORTG &= ~(1 << 2); // WR LOW
      PORTG |= (1 << 2);  // WR HIGH
    }
  }

  void fillScreen(uint16_t color) override {
    fillRect(0, 0, _width, _height, color);
  }

  void drawFastHLine(int16_t x, int16_t y, int16_t w, uint16_t color) override {
    fillRect(x, y, w, 1, color);
  }

  void drawFastVLine(int16_t x, int16_t y, int16_t h, uint16_t color) override {
    fillRect(x, y, 1, h, color);
  }

public:
  inline void writeBus16(uint16_t data) __attribute__((always_inline)) {
    PORTA = data >> 8;
    PORTC = data & 0xFF;
    PORTG &= ~(1 << 2); // WR LOW
    PORTG |= (1 << 2);  // WR HIGH
  }

  inline void writeCommand(uint16_t cmd) __attribute__((always_inline)) {
    PORTD &= ~(1 << 7); // RS LOW (指令)
    PORTA = 0x00;
    PORTC = cmd & 0xFF;
    PORTG &= ~(1 << 2); // WR LOW
    PORTG |= (1 << 2);  // WR HIGH
    PORTD |= (1 << 7);  // 回復 RS HIGH (預設資料模式)
  }

  inline void writeData(uint16_t data) __attribute__((always_inline)) {
    PORTD |= (1 << 7);  // RS HIGH (資料)
    PORTA = data >> 8;
    PORTC = data & 0xFF;
    PORTG &= ~(1 << 2); // WR LOW
    PORTG |= (1 << 2);  // WR HIGH
  }

  void setAddrWindow(uint16_t x0, uint16_t y0, uint16_t x1, uint16_t y1) {
    writeCommand(0x2A); // CASET (Column Address Set)
    writeData(x0 >> 8);
    writeData(x0 & 0xFF);
    writeData(x1 >> 8);
    writeData(x1 & 0xFF);

    writeCommand(0x2B); // PASET (Page Address Set)
    writeData(y0 >> 8);
    writeData(y0 & 0xFF);
    writeData(y1 >> 8);
    writeData(y1 & 0xFF);

    writeCommand(0x2C); // RAMWR (Memory Write)
  }

  inline void pushPixel(uint16_t color) __attribute__((always_inline)) {
    PORTA = color >> 8;
    PORTC = color & 0xFF;
    PORTG &= ~(1 << 2); // WR LOW
    PORTG |= (1 << 2);  // WR HIGH
  }

  void pushPixels(const uint16_t *colors, uint16_t len) {
    PORTD |= (1 << 7); // RS HIGH (資料)
    while (len--) {
      pushPixel(*colors++);
    }
  }

  void pushPixelsBytes(const uint8_t *bytes, uint16_t byteCount) {
    PORTD |= (1 << 7); // RS HIGH (資料)
    for (uint16_t i = 0; i < byteCount; i += 2) {
      PORTA = bytes[i];
      PORTC = bytes[i + 1];
      PORTG &= ~(1 << 2); // WR LOW
      PORTG |= (1 << 2);  // WR HIGH
    }
  }

  void pushPixels_P(const uint16_t *colors_PROGMEM, uint32_t len) {
    PORTD |= (1 << 7); // RS HIGH (資料)
    while (len--) {
      uint16_t color = pgm_read_word(colors_PROGMEM++);
      PORTA = color >> 8;
      PORTC = color & 0xFF;
      PORTG &= ~(1 << 2); // WR LOW
      PORTG |= (1 << 2);  // WR HIGH
    }
  }
};
