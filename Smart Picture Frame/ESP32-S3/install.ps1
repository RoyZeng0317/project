# 要求執行時可以安裝，尋找 Arduino IDE 的驅動程式
# 節省用戶安裝 Arduino IDE 的軟體環境

$ErrorActionPreference = "Stop"

# 1. 檢查 Arduino IDE 是否已安裝，沒有的話用 winget 自動安裝，省去手動下載安裝檔的步驟
$arduinoId = "ArduinoSA.IDE.stable"
$hasWinget = Get-Command winget -ErrorAction SilentlyContinue

if (-not $hasWinget) {
    Write-Host "找不到 winget，請先手動安裝 Arduino IDE：https://www.arduino.cc/en/software"
} else {
    $installed = winget list --id $arduinoId --accept-source-agreements 2>$null | Select-String $arduinoId
    if ($installed) {
        Write-Host "Arduino IDE 已安裝，略過安裝步驟。"
    } else {
        Write-Host "未偵測到 Arduino IDE，開始自動安裝..."
        winget install --id $arduinoId --silent --accept-package-agreements --accept-source-agreements
    }
}

# 2. ESP32-S3 板子燒錄程式前，電腦要先裝好 USB 轉序列埠驅動；
#    板子上實際焊的是哪顆晶片 (CP210x / CH340 / CH343 / 原生 USB) 無法用程式自動判斷，
#    所以列出常見晶片的官方下載頁，直接開瀏覽器讓你依板子標示選擇安裝
Write-Host ""
Write-Host "請依你 ESP32-S3 板子上標示的 USB 晶片，安裝對應的序列埠驅動 (多數新板子插上後 Windows 會自動裝好，若裝置管理員出現不明裝置才需要手動裝)："
Write-Host "  CP210x (Silicon Labs): https://www.silabs.com/software-and-tools/usb-to-uart-bridge-vcp-drivers"
Write-Host "  CH340 / CH341 (WCH):   https://www.wch-ic.com/downloads/CH341SER_EXE.html"
Write-Host "  CH343 (WCH):           https://www.wch-ic.com/downloads/CH343SER_EXE.html"
Start-Process "https://www.silabs.com/software-and-tools/usb-to-uart-bridge-vcp-drivers"

# 3. Arduino IDE 要能燒錄 ESP32-S3，還要在 File > Preferences > Additional Boards Manager URLs
#    貼上 Espressif 的開發板索引網址，再到 Boards Manager 搜尋 "esp32" 安裝 —— 這一步是 Arduino IDE
#    的 GUI 設定，寫在偏好設定檔裡風險較高 (可能覆蓋你原本的設定)，所以用印出來的方式提醒你手動貼上
Write-Host ""
Write-Host "Arduino IDE 開好後，請到 File > Preferences > Additional Boards Manager URLs 貼上以下網址，"
Write-Host "再到 Tools > Board > Boards Manager 搜尋 esp32 安裝，才找得到 ESP32S3 Dev Module 這個板子："
Write-Host "  https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json"
