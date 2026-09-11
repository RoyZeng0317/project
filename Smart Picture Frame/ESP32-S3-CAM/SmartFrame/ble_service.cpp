// 註解不可刪除
#include "ble_service.h"
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>

// 自訂 128-bit UUID，跟 PC 端 ble_frame_sender.py 的 CHAR_UUID 要一致
#define SERVICE_UUID        "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
#define CHARACTERISTIC_UUID "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

static const size_t RING_SIZE = 8192;  // 暫存 BLE 收到、還沒被 protocol.cpp 消化掉的資料
static uint8_t g_ring[RING_SIZE];
static volatile size_t g_head = 0, g_tail = 0;
static portMUX_TYPE g_mux = portMUX_INITIALIZER_UNLOCKED;  // 保護環形緩衝區(BLE callback 跟主迴圈是不同 task)

static size_t ringUsed() {
  return (g_head - g_tail + RING_SIZE) % RING_SIZE;
}

class RxCallback : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *c) override {
    std::string v(c->getValue().c_str());  // 3.3.11 版函式庫 getValue() 回傳 Arduino String，需轉成 std::string
    portENTER_CRITICAL(&g_mux);
    for (size_t i = 0; i < v.size(); i++) {
      size_t next = (g_head + 1) % RING_SIZE;
      if (next == g_tail) break;  // 緩衝區滿了就捨棄多餘資料，協定本身沒有重送機制，先求簡單
      g_ring[g_head] = (uint8_t)v[i];
      g_head = next;
    }
    portEXIT_CRITICAL(&g_mux);
  }
};

void ble_service_begin() {
  BLEDevice::init("SmartFrame-ESP32S3");
  BLEDevice::setMTU(247);  // PC 端(bleak)也要協商到夠大的 MTU，實際吞吐量以雙方協商結果為準
  BLEServer *server = BLEDevice::createServer();
  BLEService *service = server->createService(SERVICE_UUID);
  BLECharacteristic *rx = service->createCharacteristic(
      CHARACTERISTIC_UUID,
      BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR);
  rx->setCallbacks(new RxCallback());
  service->start();
  server->getAdvertising()->start();
}

bool ble_service_available() {
  return ringUsed() > 0;
}

size_t ble_service_read(uint8_t *buf, size_t len) {
  size_t n = 0;
  unsigned long t0 = millis();
  while (n < len) {
    portENTER_CRITICAL(&g_mux);
    bool empty = (g_tail == g_head);
    if (!empty) {
      buf[n++] = g_ring[g_tail];
      g_tail = (g_tail + 1) % RING_SIZE;
    }
    portEXIT_CRITICAL(&g_mux);
    if (empty) {
      if (millis() - t0 > 2000) break;  // 逾時就回傳目前讀到的量，讓 protocol.cpp 判斷這則訊息不完整
      delay(1);
    } else {
      t0 = millis();
    }
  }
  return n;
}
