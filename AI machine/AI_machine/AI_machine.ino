// ============================================================
// ESP32-S3 AI 對話機器人
// 流程：錄音 → Whisper STT → ChatGPT → OpenAI TTS → 播放
// ============================================================

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <driver/i2s.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <DFRobotDFPlayerMini.h>
#include <SD_MMC.h>

// ─── WiFi 設定 ───────────────────────────────────────────────
const char* WIFI_SSID     = "你的WiFi名稱";
const char* WIFI_PASSWORD = "你的WiFi密碼";
const char* OPENAI_KEY    = "sk-你的OpenAI金鑰";

// ─── I2S 麥克風 Pin ──────────────────────────────────────────
#define I2S_SCK   14
#define I2S_WS    15
#define I2S_SD    13
#define I2S_PORT  I2S_NUM_0
#define SAMPLE_RATE     16000
#define RECORD_SECONDS  5
#define BUFFER_SIZE     (SAMPLE_RATE * RECORD_SECONDS * 2)  // 16-bit

// ─── OLED ────────────────────────────────────────────────────
#define SCREEN_WIDTH  128
#define SCREEN_HEIGHT 64
#define OLED_SDA 11
#define OLED_SCL 12
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// ─── DFPlayer Mini ───────────────────────────────────────────
#define DFPLAYER_RX 18
#define DFPLAYER_TX 17
HardwareSerial dfSerial(1);
DFRobotDFPlayerMini dfPlayer;

// ─── 按鈕 ────────────────────────────────────────────────────
#define BTN_PIN 0   // BOOT 按鈕或外接按鈕

// ─── 音訊緩衝 ────────────────────────────────────────────────
int16_t* audioBuffer = nullptr;

// ─── 對話歷史 ────────────────────────────────────────────────
String conversationHistory = "";

// ─── OLED 顯示工具函數 ───────────────────────────────────────
void showOLED(String line1, String line2 = "", String line3 = "") {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(line1);
  if (line2 != "") { display.setCursor(0, 22); display.println(line2); }
  if (line3 != "") { display.setCursor(0, 44); display.println(line3); }
  display.display();
}

void showOLEDWithDots(String msg) {
  static int dots = 0;
  String d = "";
  for (int i = 0; i <= dots; i++) d += ".";
  dots = (dots + 1) % 3;
  showOLED(msg + d);
}

// ─── I2S 麥克風初始化 ────────────────────────────────────────
void initMic() {
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 64,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };
  i2s_pin_config_t pin_config = {
    .bck_io_num   = I2S_SCK,
    .ws_io_num    = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num  = I2S_SD
  };
  i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_PORT, &pin_config);
}

// ─── 錄音函數 ────────────────────────────────────────────────
bool recordAudio() {
  showOLED("Recording...", "Press btn to stop");
  
  if (!audioBuffer) {
    audioBuffer = (int16_t*)ps_malloc(BUFFER_SIZE);
  }
  if (!audioBuffer) { showOLED("Memory Error!"); return false; }

  int32_t temp32;
  size_t bytesRead;
  int totalSamples = 0;
  int maxSamples = SAMPLE_RATE * RECORD_SECONDS;

  while (totalSamples < maxSamples) {
    i2s_read(I2S_PORT, &temp32, sizeof(temp32), &bytesRead, portMAX_DELAY);
    if (bytesRead > 0) {
      audioBuffer[totalSamples++] = (int16_t)(temp32 >> 16);
    }
    // 按鈕提前結束
    if (digitalRead(BTN_PIN) == LOW && totalSamples > SAMPLE_RATE) break;
  }

  // 存成 WAV 到 SD 卡
  return saveWAV("/rec.wav", audioBuffer, totalSamples);
}

// ─── 儲存 WAV 檔 ─────────────────────────────────────────────
bool saveWAV(const char* path, int16_t* data, int samples) {
  File f = SD_MMC.open(path, FILE_WRITE);
  if (!f) return false;

  int dataSize = samples * 2;
  int fileSize = 44 + dataSize;

  // WAV Header
  f.write((uint8_t*)"RIFF", 4);
  uint32_t v = fileSize - 8; f.write((uint8_t*)&v, 4);
  f.write((uint8_t*)"WAVE", 4);
  f.write((uint8_t*)"fmt ", 4);
  v = 16; f.write((uint8_t*)&v, 4);
  uint16_t s = 1;  f.write((uint8_t*)&s, 2); // PCM
  s = 1;           f.write((uint8_t*)&s, 2); // Mono
  v = SAMPLE_RATE; f.write((uint8_t*)&v, 4);
  v = SAMPLE_RATE * 2; f.write((uint8_t*)&v, 4);
  s = 2;           f.write((uint8_t*)&s, 2);
  s = 16;          f.write((uint8_t*)&s, 2);
  f.write((uint8_t*)"data", 4);
  v = dataSize;    f.write((uint8_t*)&v, 4);
  f.write((uint8_t*)data, dataSize);
  f.close();
  return true;
}

// ─── 呼叫 Whisper STT ────────────────────────────────────────
String speechToText() {
  showOLED("Transcribing", "Whisper STT...");

  HTTPClient http;
  http.begin("https://api.openai.com/v1/audio/transcriptions");
  http.addHeader("Authorization", String("Bearer ") + OPENAI_KEY);

  File f = SD_MMC.open("/rec.wav");
  if (!f) return "";
  size_t fileSize = f.size();
  uint8_t* fileData = (uint8_t*)malloc(fileSize);
  f.read(fileData, fileSize);
  f.close();

  String boundary = "ESP32Boundary";
  String contentType = "multipart/form-data; boundary=" + boundary;
  http.addHeader("Content-Type", contentType);

  String bodyStart =
    "--" + boundary + "\r\n"
    "Content-Disposition: form-data; name=\"model\"\r\n\r\n"
    "whisper-1\r\n"
    "--" + boundary + "\r\n"
    "Content-Disposition: form-data; name=\"language\"\r\n\r\n"
    "zh\r\n"
    "--" + boundary + "\r\n"
    "Content-Disposition: form-data; name=\"file\"; filename=\"rec.wav\"\r\n"
    "Content-Type: audio/wav\r\n\r\n";
  String bodyEnd = "\r\n--" + boundary + "--\r\n";

  int totalLen = bodyStart.length() + fileSize + bodyEnd.length();
  uint8_t* body = (uint8_t*)malloc(totalLen);
  memcpy(body, bodyStart.c_str(), bodyStart.length());
  memcpy(body + bodyStart.length(), fileData, fileSize);
  memcpy(body + bodyStart.length() + fileSize, bodyEnd.c_str(), bodyEnd.length());
  free(fileData);

  int code = http.POST(body, totalLen);
  free(body);

  if (code != 200) { http.end(); return ""; }

  String resp = http.getString();
  http.end();

  DynamicJsonDocument doc(1024);
  deserializeJson(doc, resp);
  return doc["text"].as<String>();
}

// ─── 呼叫 ChatGPT ────────────────────────────────────────────
String askChatGPT(String userText) {
  showOLED("Thinking...", userText.substring(0, 20));

  // 加入對話歷史
  if (conversationHistory.length() > 2000) conversationHistory = "";  // 防止過長
  conversationHistory += "{\"role\":\"user\",\"content\":\"" + userText + "\"},";

  HTTPClient http;
  http.begin("https://api.openai.com/v1/chat/completions");
  http.addHeader("Authorization", String("Bearer ") + OPENAI_KEY);
  http.addHeader("Content-Type", "application/json");

  String body = "{\"model\":\"gpt-4o-mini\","
    "\"messages\":["
    "{\"role\":\"system\",\"content\":\"你是一個友善的中文AI助理，回答請簡潔，不超過50個字。\"},"
    + conversationHistory.substring(0, conversationHistory.length()-1) +
    "],\"max_tokens\":150}";

  int code = http.POST(body);
  if (code != 200) { http.end(); return "抱歉，發生錯誤。"; }

  String resp = http.getString();
  http.end();

  DynamicJsonDocument doc(4096);
  deserializeJson(doc, resp);
  String reply = doc["choices"][0]["message"]["content"].as<String>();

  conversationHistory += "{\"role\":\"assistant\",\"content\":\"" + reply + "\"},";
  return reply;
}

// ─── 呼叫 OpenAI TTS → 存 MP3 → 播放 ───────────────────────
void textToSpeech(String text) {
  showOLED("Generating", "voice...");

  HTTPClient http;
  http.begin("https://api.openai.com/v1/audio/speech");
  http.addHeader("Authorization", String("Bearer ") + OPENAI_KEY);
  http.addHeader("Content-Type", "application/json");

  String body = "{\"model\":\"tts-1\","
    "\"input\":\"" + text + "\","
    "\"voice\":\"nova\","
    "\"response_format\":\"mp3\"}";

  int code = http.POST(body);
  if (code != 200) { http.end(); return; }

  // 串流寫入 SD 卡
  WiFiClient* stream = http.getStreamPtr();
  File f = SD_MMC.open("/reply.mp3", FILE_WRITE);
  uint8_t buf[512];
  while (http.connected() && stream->available()) {
    int len = stream->readBytes(buf, sizeof(buf));
    if (len > 0) f.write(buf, len);
  }
  f.close();
  http.end();

  // DFPlayer 播放
  showOLED("Playing...", text.substring(0, 20));
  dfPlayer.play(1);  // 播放 /mp3/0001.mp3（需先放到SD卡）
  
  // 等待播放完成
  delay(500);
  while (dfPlayer.available()) {
    if (dfPlayer.readType() == DFPlayerPlayFinished) break;
    delay(100);
  }
}

// ─── Setup ───────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  pinMode(BTN_PIN, INPUT_PULLUP);

  // OLED 初始化
  Wire.begin(OLED_SDA, OLED_SCL);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED failed"); while(1);
  }
  showOLED("AI Robot", "Initializing...");

  // SD 卡初始化 (ESP32-S3-CAM 使用 SD_MMC)
  if (!SD_MMC.begin()) {
    showOLED("SD Card Error!"); while(1);
  }

  // DFPlayer 初始化
  dfSerial.begin(9600, SERIAL_8N1, DFPLAYER_RX, DFPLAYER_TX);
  if (!dfPlayer.begin(dfSerial)) {
    showOLED("DFPlayer Error!"); while(1);
  }
  dfPlayer.volume(25);  // 音量 0-30

  // I2S 麥克風初始化
  initMic();

  // WiFi 連線
  showOLED("Connecting", "WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int retry = 0;
  while (WiFi.status() != WL_CONNECTED && retry < 20) {
    delay(500); retry++;
  }
  if (WiFi.status() != WL_CONNECTED) {
    showOLED("WiFi Failed!"); while(1);
  }

  showOLED("Ready!", "Press button", "to speak");
}

// ─── Loop ────────────────────────────────────────────────────
void loop() {
  // 等待按鈕按下
  if (digitalRead(BTN_PIN) == LOW) {
    delay(50);  // 防彈跳
    if (digitalRead(BTN_PIN) == LOW) {

      // 1. 錄音
      if (!recordAudio()) return;

      // 2. STT
      String userText = speechToText();
      if (userText.length() == 0) {
        showOLED("No speech", "detected"); delay(2000); return;
      }
      showOLED("You said:", userText.substring(0, 20));
      delay(1000);

      // 3. ChatGPT
      String reply = askChatGPT(userText);
      showOLED("AI:", reply.substring(0, 20), reply.substring(20, 40));

      // 4. TTS + 播放
      textToSpeech(reply);

      showOLED("Ready!", "Press button", "to speak");
    }
  }
  delay(10);
}