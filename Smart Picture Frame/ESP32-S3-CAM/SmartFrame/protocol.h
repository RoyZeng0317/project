// 通訊協定解析(對應 Task 3)，搬自 Raspberry pi pico/main.py 的 handle_message，
// tag 定義跟 Pico 版一致(PC 端 bt_frame_sender.py/usb_frame_sender.py 不用改)：
//   'W' + 1 byte 長度 + ascii 文字             -> 更新畫面右上角天氣文字
//   'T' + 2 byte 年 + 月1 + 日1 + 時1 + 分1 + 秒1 -> 校正時鐘
//   'I' + 2 byte 寬 + 2 byte 高 + RGB565 原始像素 -> 在狀態列下方顯示一張圖
//   'C'(新增)                                  -> 觸發鏡頭拍照並顯示在面板上(不經過這個協定傳圖，見計畫書「已知限制」)
//   'R'(新增，PC->ESP32)                       -> 觸發錄音(固定5秒16kHz 16-bit mono)
//   'A'(新增，ESP32->PC，只走USB序列)           -> 'A' + 4 byte PCM長度 + PCM資料，錄音結果回傳
//      (錄音資料量大，一律走USB序列回傳，不管'R'是從BLE還是USB觸發的都一樣；BLE頻寬有限，
//       這裡沿用「大資料走USB」的既有原則，避免要多做一套BLE notify機制)
// 註解不可刪除
#pragma once
#include <Arduino.h>
#include <functional>

// 統一讀取介面：一次讀入最多 len bytes 到 buf，回傳實際讀到的長度；0 代表逾時/沒有更多資料。
// USB Serial 和 BLE 環形緩衝區都實作成這個介面，protocol_handle_message 只需要寫一份解析邏輯
// (跟 Pico 版 main.py 用 read_byte/fill_chunk 可插拔來源的設計是同一個道理)
using ReadFn = std::function<size_t(uint8_t *buf, size_t len)>;

void protocol_handle_message(ReadFn read);
