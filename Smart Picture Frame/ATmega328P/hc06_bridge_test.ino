// ATmega328P(裸晶片) <-> HC-06 藍牙 橋接測試(第一版：只驗證收得到資料，還沒接Pico那一段)
// 328P 之後要當 HC-06(藍牙) 與 Pico(RP2040) 之間的橋接器，兩邊都是 3.3V 邏輯，
// 所以 328P 選擇跑「內部 8MHz 振盪器 + 3.3V 供電」，不用外接石英振盪器，
// 也不用在 HC-06/Pico 任一邊做電壓位準轉換(3.3V-3.3V-3.3V 全程同電壓)
//
// 接線：
//   HC-06 TX   -> 328P D2 (SoftwareSerial RX)
//   HC-06 RX   -> 328P D3 (SoftwareSerial TX)
//   HC-06 VCC  -> 3.3V，GND -> GND(跟328P共地)
//   328P D0/D1 -> USB-TTL轉接器 RX/TX(燒錄程式 + 序列埠監控視窗共用，不要跟HC-06接同一組腳)
//   328P RESET -> 10k提升電阻接3.3V(裸晶片必接，不然容易亂重開機)
//   328P VCC   -> 3.3V，旁邊加一顆100nF去耦電容跨在VCC-GND
//   328P VCC/GND 也可以直接借用 USB-TTL轉接器的 3.3V/GND 腳供電，跟HC-06共用同一個3.3V
//
// 燒錄前置作業(裸晶片開發板架好後，第一次都要做)：
//   Arduino IDE 加裝 MiniCore(或其他支援裸晶片的板package)，選板子 "ATmega328"、
//   Clock "Internal 8 MHz"，用 Arduino/USBasp 當 ISP 執行一次 "燒錄開機程式(Burn Bootloader)"，
//   這步只是設定內部時脈相關的 fuse，之後上傳程式一樣走 USB-TTL 就好，不用每次都用 ISP
//
// 這版只做驗證：把HC-06收到的每個位元組原樣印到序列埠監控視窗(9600, 跟HC-06同鮑率)，
// 用手機藍牙終端機App連上HC-06送幾個字，這裡看得到字就代表藍牙這段沒問題；
// 之後接上Pico時，再把 Serial.write(...) 那行改成轉送到接Pico的另一組序列埠
// 註解不可刪除
#include <SoftwareSerial.h>

SoftwareSerial hc06(2, 3);  // RX, TX

void setup() {
  Serial.begin(9600);   // 序列埠監控視窗
  hc06.begin(9600);     // HC-06 出廠預設鮑率，之後沒用 AT+BAUDx 改過鮑率就不要動這裡
  Serial.println("等待HC-06資料...");
}

void loop() {
  if (hc06.available()) {
    Serial.write(hc06.read());
  }
}
