// BLE GATT server(對應 Task 5)，取代原本 Pico 版外接的 HC-06；用 arduino-esp32 內建的
// BLEDevice(Bluedroid)，不用額外裝函式庫。PC 端對應 ble_frame_sender.py
// 註解不可刪除
#pragma once
#include "protocol.h"

void ble_service_begin();
bool ble_service_available();
size_t ble_service_read(uint8_t *buf, size_t len);  // 符合 ReadFn 介面，可直接傳給 protocol_handle_message
