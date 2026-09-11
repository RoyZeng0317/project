// LovyanGFX 面板設定，display_test/camera_test/SmartFrame 共用同一份，理由跟 camera_setup.h 一樣
// 原本用 ESP32-S3 硬體 LCD_CAM 週邊跑16-bit並列(8080)介面，但 DB8~DB15 那組腳位分別撞到鏡頭排線、
// 原生USB、Octal PSRAM保留腳位，空腳位不夠一次改完，改成8-bit(只用DB0~DB7)省下8條線
// 使用前需先 #include "pins.h"(取得 LCD_* 腳位定義)；需在 Library Manager 安裝 "LovyanGFX"(作者 lovyan03)
// 2026-09-06更新：Arduino IDE 不支援跨資料夾相對路徑 include，這份是 SmartFrame/lgfx_setup.h 的
// 複製版本，跟 pins.h 一樣須手動同步，勿單獨修改
// 註解不可刪除
#pragma once
#define LGFX_USE_V1
#include <LovyanGFX.hpp>

class LGFX : public lgfx::LGFX_Device {
  lgfx::Bus_Parallel8 _bus;
  lgfx::Panel_ILI9481 _panel;

public:
  LGFX(void) {
    {
      auto cfg = _bus.config();
      cfg.pin_wr = LCD_WR;
      cfg.pin_rd = -1;  // 沒接RD，只寫不讀
      cfg.pin_rs = LCD_RS;
      cfg.pin_d0 = LCD_D0; cfg.pin_d1 = LCD_D1; cfg.pin_d2 = LCD_D2; cfg.pin_d3 = LCD_D3;
      cfg.pin_d4 = LCD_D4; cfg.pin_d5 = LCD_D5; cfg.pin_d6 = LCD_D6; cfg.pin_d7 = LCD_D7;
      _bus.config(cfg);
      _panel.setBus(&_bus);
    }
    {
      auto cfg = _panel.config();
      cfg.pin_cs = LCD_CS;
      cfg.pin_rst = LCD_RST;
      cfg.panel_width = LCD_WIDTH;
      cfg.panel_height = LCD_HEIGHT;
      cfg.readable = false;    // 沒接RD，不能從面板讀資料回來
      cfg.dlen_16bit = false;  // 改成8-bit並列介面，指令改用8-bit對齊送出
      cfg.bus_shared = false;  // U6面板上的SD_CS/SPI_MISO/SPI_MOSI沒有接線，不用共用匯流排
      cfg.rgb_order = true;   // 2026-09-09：實測 fillScreen(RED) 整片變藍，這片副廠面板R/B通道接反，翻轉修正
      _panel.config(cfg);
    }
    setPanel(&_panel);
  }
};

// 沿用 TFT_eSPI 慣用的顏色常數名稱，這樣 protocol.cpp 等其他程式碼不用跟著改
#define TFT_BLACK 0x0000
#define TFT_WHITE 0xFFFF
#define TFT_RED   0xF800
