#pragma once
#include <DFRobotDFPlayerMini.h>
#include "config.h"

class AudioManager {
  HardwareSerial dfSerial;
  DFRobotDFPlayerMini player;
  bool ready = false;

public:
  AudioManager() : dfSerial(2) {}  // UART2

  void begin() {
    // UART2: RX=16, TX=17
    dfSerial.begin(9600, SERIAL_8N1, DFPLAYER_RX, DFPLAYER_TX);
    delay(1000);

    if (!player.begin(dfSerial, true, true)) {
      Serial.println(F("[Audio] DFPlayer 初始化失敗！"));
      Serial.println(F("[Audio] 確認接線：TX→GPIO16(RX2)，RX→GPIO17(TX2) 加 1kΩ"));
      ready = false;
      return;
    }

    player.volume(DFPLAYER_VOLUME);
    player.EQ(DFPLAYER_EQ_NORMAL);

    uint8_t files = player.readFileCounts();
    Serial.printf("[Audio] DFPlayer OK，SD 卡檔案數：%d\n", files);
    ready = true;
  }

  // 播放指定編號（1~99，對應 /01/001.mp3）
  void playTrack(uint8_t track) {
    if (!ready || track == 0) return;
    player.play(track);
    Serial.printf("[Audio] 播放 track %d\n", track);
  }

  // 停止播放
  void stop() {
    if (!ready) return;
    player.stop();
  }

  // 調整音量 0~30
  void setVolume(uint8_t vol) {
    if (!ready) return;
    player.volume(constrain(vol, 0, 30));
  }

  // 音量加 / 減
  void volumeUp()   { if (ready) player.volumeUp(); }
  void volumeDown() { if (ready) player.volumeDown(); }

  // loop 中呼叫：處理 DFPlayer 狀態回報
  void loop() {
    if (!ready) return;
    if (player.available()) {
      uint8_t type  = player.readType();
      int     value = player.read();
      if (type == DFPlayerPlayFinished) {
        Serial.printf("[Audio] 播放完畢，track %d\n", value);
      } else if (type == DFPlayerError) {
        Serial.printf("[Audio] 錯誤：%d\n", value);
      }
    }
  }

  bool isReady() { return ready; }
};

AudioManager Audio;
