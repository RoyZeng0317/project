#pragma once
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "config.h"

class DisplayManager {
  Adafruit_SSD1306 oled;

public:
  DisplayManager() : oled(OLED_WIDTH, OLED_HEIGHT, &Wire, -1) {}

  void begin() {
    if (!oled.begin(SSD1306_SWITCHCAPVCC, OLED_ADDRESS)) {
      Serial.println(F("[OLED] 初始化失敗！"));
      return;
    }
    oled.clearDisplay();
    oled.setTextColor(SSD1306_WHITE);
    Serial.println(F("[OLED] 初始化成功"));
  }

  // 開機畫面
  void showBootScreen(const char* title, const char* ver) {
    oled.clearDisplay();
    oled.setTextSize(2);
    oled.setCursor(20, 10);
    oled.println(title);
    oled.setTextSize(1);
    oled.setCursor(40, 35);
    oled.print(F("版本 "));
    oled.println(ver);
    oled.setCursor(20, 50);
    oled.println(F("正在啟動..."));
    oled.display();
  }

  // 顯示一則訊息（寄件人 + 內文自動換行）
  void showMessage(const char* from, const char* text) {
    oled.clearDisplay();

    // 頂部：寄件人（反白）
    oled.fillRect(0, 0, OLED_WIDTH, 14, SSD1306_WHITE);
    oled.setTextColor(SSD1306_BLACK);
    oled.setTextSize(1);
    oled.setCursor(3, 3);
    oled.print(F("From: "));
    oled.print(from);

    // 分隔線
    oled.setTextColor(SSD1306_WHITE);
    oled.drawFastHLine(0, 15, OLED_WIDTH, SSD1306_WHITE);

    // 訊息內文（自動換行，最多 3 行）
    oled.setTextSize(1);
    oled.setCursor(0, 18);
    _printWrapped(text, 128, 3);

    // 底部提示
    oled.drawFastHLine(0, 54, OLED_WIDTH, SSD1306_WHITE);
    oled.setCursor(0, 56);
    oled.print(F("[1]回覆 [2]已讀 [3]音樂"));

    oled.display();
  }

  // 顯示狀態文字（置中）
  void showStatus(const char* msg) {
    oled.clearDisplay();
    oled.setTextSize(1);
    oled.setTextColor(SSD1306_WHITE);
    int16_t x1, y1;
    uint16_t w, h;
    oled.getTextBounds(msg, 0, 0, &x1, &y1, &w, &h);
    oled.setCursor((OLED_WIDTH - w) / 2, (OLED_HEIGHT - h) / 2);
    oled.println(msg);
    oled.display();
  }

  // 待機畫面
  void showIdle(const char* statusText) {
    oled.clearDisplay();
    oled.setTextSize(2);
    oled.setTextColor(SSD1306_WHITE);
    oled.setCursor(14, 8);
    oled.println(F("BB CALL"));
    oled.setTextSize(1);
    oled.drawFastHLine(0, 28, OLED_WIDTH, SSD1306_WHITE);
    oled.setCursor(0, 32);
    oled.println(statusText);

    // 時間 (以 millis 示意，實際可接 RTC)
    unsigned long s = millis() / 1000;
    oled.setCursor(0, 46);
    oled.printf("Up: %02lu:%02lu:%02lu", s / 3600, (s % 3600) / 60, s % 60);

    oled.display();
  }

private:
  // 自動換行列印（maxWidth 像素寬，maxLines 行數）
  void _printWrapped(const char* str, int maxWidth, int maxLines) {
    int lineCount = 0;
    int charWidth = 6;  // 1x font = 6px/char
    int maxChars  = maxWidth / charWidth;

    String line = "";
    String word = "";

    for (int i = 0; str[i] != '\0' && lineCount < maxLines; i++) {
      char c = str[i];
      if (c == ' ' || c == '\n') {
        // 嘗試加入這個詞
        if ((int)(line.length() + word.length()) <= maxChars) {
          line += word + ' ';
        } else {
          oled.println(line);
          lineCount++;
          line = word + ' ';
        }
        word = "";
        if (c == '\n') {
          oled.println(line);
          lineCount++;
          line = "";
        }
      } else {
        word += c;
      }
    }
    // 剩餘文字
    if (lineCount < maxLines) {
      line += word;
      if (line.length() > 0) oled.println(line);
    }
  }
};

DisplayManager Display;
