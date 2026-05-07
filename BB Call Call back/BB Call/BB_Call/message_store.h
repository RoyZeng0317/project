#pragma once
#include "config.h"

// ─── 訊息結構 ─────────────────────────────────────
struct Message {
  char     from[32];
  char     text[128];
  uint8_t  musicTrack;
  uint32_t timestamp;
  bool     isRead;
};

// ─── 環形緩衝區，儲存最近 N 則訊息 ──────────────
class MessageStore {
  Message  buf[MSG_QUEUE_SIZE];
  uint8_t  head    = 0;  // 下一個寫入位置
  uint8_t  count   = 0;  // 目前訊息數
  uint8_t  unread  = 0;  // 未讀數

public:
  void begin() {
    memset(buf, 0, sizeof(buf));
    Serial.printf("[MsgStore] 初始化，容量 %d 則\n", MSG_QUEUE_SIZE);
  }

  // 推入新訊息，回傳其索引
  uint8_t push(const Message& msg) {
    uint8_t idx = head;
    buf[idx] = msg;
    head = (head + 1) % MSG_QUEUE_SIZE;
    if (count < MSG_QUEUE_SIZE) count++;
    unread++;
    Serial.printf("[MsgStore] 新訊息[%d]，未讀 %d\n", idx, unread);
    return idx;
  }

  // 取得訊息（索引）
  Message& get(uint8_t idx) {
    return buf[idx % MSG_QUEUE_SIZE];
  }

  // 標記已讀
  void markRead(uint8_t idx) {
    if (!buf[idx].isRead) {
      buf[idx].isRead = true;
      if (unread > 0) unread--;
    }
  }

  // 找下一則未讀（從 current 往後）
  int getNextUnread(uint8_t current) {
    for (uint8_t i = 1; i <= count; i++) {
      uint8_t idx = (current + i) % MSG_QUEUE_SIZE;
      if (!buf[idx].isRead && buf[idx].timestamp > 0) return idx;
    }
    return -1;  // 無未讀
  }

  // 最新一則訊息的索引
  uint8_t getLatestIndex() {
    return (head == 0) ? MSG_QUEUE_SIZE - 1 : head - 1;
  }

  uint8_t getUnreadCount() { return unread; }
  uint8_t getTotalCount()  { return count;  }
};

MessageStore MsgStore;
