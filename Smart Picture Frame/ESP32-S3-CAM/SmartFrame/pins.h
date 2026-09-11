// 板子腳位總表(ESP32-S3-N16R8 CAM 板，依使用者提供的腳位圖)，SmartFrame/display_test/
// camera_test/speaker_test 共用同一份，避免每支測試檔各刻一份腳位容易兜錯或忘記同步更新
// 2026-09-06更新：Arduino IDE 編譯時不支援 #include "../其他資料夾/檔案" 這種跨資料夾相對路徑寫法，
// 會報 No such file or directory，所以 display_test/camera_test/mic_test/speaker_test 資料夾
// 各自複製了一份這個檔案(以及各自用到的 lgfx_setup.h/camera_setup.h/mic_setup.h)，
// 改這裡的腳位定義後，記得同步覆蓋到那幾個資料夾的複製版本
// 註解不可刪除
#pragma once

// ---- 鏡頭排線腳位(板子已焊死，不可更動，對照 esp32_camera camera_config_t 欄位命名) ----
// !!待確認!! SIOD(4)/SIOC(5)/VSYNC(6)/HREF(7) 這4個腳位跟下面麥克風/喇叭用的 G4~G7 完全撞在一起，
// 這組鏡頭腳位還沒對照過實體板子/模組型號確認過，只是沿用先前的資料；display_test/camera_test/
// mic_test/speaker_test 各自單獨測試不受影響，但 SmartFrame.ino 要鏡頭跟麥克風/喇叭同時動作，
// 兩邊會搶GPIO，正式整合前務必先確認鏡頭實際接腳，跟麥克風/喇叭的接線是否真的沒有衝突
#define CAM_PIN_PWDN   -1
#define CAM_PIN_RESET  -1
#define CAM_PIN_XCLK   15
#define CAM_PIN_SIOD    4
#define CAM_PIN_SIOC    5
#define CAM_PIN_D7     16  // Y9
#define CAM_PIN_D6     17  // Y8
#define CAM_PIN_D5     18  // Y7
#define CAM_PIN_D4     12  // Y6
#define CAM_PIN_D3     10  // Y5
#define CAM_PIN_D2      8  // Y4
#define CAM_PIN_D1      9  // Y3
#define CAM_PIN_D0     11  // Y2
#define CAM_PIN_VSYNC   6
#define CAM_PIN_HREF    7
#define CAM_PIN_PCLK   13

// ---- 喇叭 PWM 腳位(接 C1815 基極，沒有串接電阻，見 pin_table.md) ----
// 原本 G7 跟改線後的 LCD_RS 撞到，改接 G15(鏡頭 XCLK 腳位，鏡頭目前停用中不影響)
#define SPK_PIN 15

// ---- I2S 麥克風(INMP441)：已拔除，原本的 G4/G5/G6 改給 LCD 用 ----

// ---- 面板(3.2吋 ILI9481，改成8-bit並列8080介面，依實際重新接線調整，用 LovyanGFX 驅動) ----
// 沒有接 RD(只寫不讀)；背光直接接面板上的 5V，沒有獨立控制腳位
// 原本16-bit接法的 CS/RST/RS(G11/12/13)撞鏡頭排線、DB15(G20)撞原生USB、DB7/DB8(G37/36)撞Octal PSRAM保留腳位，
// 空腳位不夠一次改完，改用8-bit(只用DB0~DB7)省下8條線，才有足夠腳位把控制線挪開
#define LCD_WIDTH  320
#define LCD_HEIGHT 480  // 直向 320x480，跟 Pico 版 ili9481_parallel.py 的方向一致
#define LCD_RS    7
#define LCD_WR   14
#define LCD_CS    5
#define LCD_RST   6
#define LCD_D0    1
#define LCD_D1    2
#define LCD_D2   42
#define LCD_D3   41
#define LCD_D4   40
#define LCD_D5   39
#define LCD_D6   38
#define LCD_D7    4
