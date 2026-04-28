#!/usr/bin/env python3
"""
BB Call 測試腳本
用法：python3 test_bbcall.py

需要安裝：pip install paho-mqtt
"""

import json
import time
import paho.mqtt.client as mqtt

# ─── 設定（與 config.h 一致）────────────────────────
BROKER    = "broker.hivemq.com"
PORT      = 1883
DEVICE_ID = "bbcall_01"

TOPIC_INBOX  = f"bbcall/{DEVICE_ID}/inbox"
TOPIC_REPLY  = f"bbcall/{DEVICE_ID}/reply"
TOPIC_STATUS = f"bbcall/{DEVICE_ID}/status"

# ─── 回呼 ────────────────────────────────────────────
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ 連線成功 → {BROKER}")
        client.subscribe(TOPIC_REPLY)
        client.subscribe(TOPIC_STATUS)
        print(f"📡 訂閱：{TOPIC_REPLY}")
        print(f"📡 訂閱：{TOPIC_STATUS}")
    else:
        print(f"❌ 連線失敗，錯誤碼：{rc}")

def on_message(client, userdata, msg):
    print(f"\n📨 [{msg.topic}]")
    try:
        data = json.loads(msg.payload)
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except:
        print(msg.payload.decode())

# ─── 發送訊息 ─────────────────────────────────────────
def send_message(client, from_name: str, text: str, music: int = 0):
    payload = json.dumps({
        "from":  from_name,
        "msg":   text,
        "music": music
    }, ensure_ascii=False)
    client.publish(TOPIC_INBOX, payload)
    print(f"\n✉️  已發送：{payload}")

# ─── 主程式 ───────────────────────────────────────────
def main():
    client = mqtt.Client(f"test-{int(time.time())}")
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"連線至 {BROKER}:{PORT} ...")
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()
    time.sleep(2)

    print("\n=== BB Call 測試選單 ===")
    while True:
        print("\n1. 發送純文字訊息")
        print("2. 發送訊息 + 播放音樂 (track 3)")
        print("3. 發送長訊息（測試換行）")
        print("4. 等待回覆 10 秒")
        print("0. 離開")

        choice = input("\n選擇：").strip()

        if choice == "1":
            name = input("寄件人：") or "Alice"
            msg  = input("訊息：")  or "哈囉，你好！"
            send_message(client, name, msg)

        elif choice == "2":
            send_message(client, "Bob", "播放音樂給你聽！", music=3)

        elif choice == "3":
            send_message(client, "Carol",
                "這是一則比較長的測試訊息，用來檢查 OLED 螢幕自動換行功能是否正常運作。")

        elif choice == "4":
            print("等待裝置回覆 10 秒...")
            time.sleep(10)

        elif choice == "0":
            break

    client.loop_stop()
    client.disconnect()
    print("已斷線")

if __name__ == "__main__":
    main()
