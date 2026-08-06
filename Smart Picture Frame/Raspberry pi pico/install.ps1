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

# 2. Raspberry Pi Pico 跟 ESP32-S3 不一樣：Pico 用的是 RP2040/RP2350 原生 USB (CDC)，
#    不是外接 CP210x/CH340 這種轉換晶片，Windows 10/11 內建 usbser 驅動就會自動裝好，
#    正常不需要額外安裝驅動；只有少數 Windows 7 環境才需要手動裝 Zadig/Microchip CDC 驅動
Write-Host ""
Write-Host "Raspberry Pi Pico 在 Windows 10/11 會自動使用內建的 USB 序列埠驅動，一般不需要另外安裝。"
Write-Host "如果裝置管理員出現不明裝置 (通常只發生在 Windows 7)，才需要手動安裝："
Write-Host "  Zadig 工具：https://zadig.akeo.ie/"

# 3. Arduino IDE 要能燒錄 Raspberry Pi Pico，一樣要在 File > Preferences > Additional Boards
#    Manager URLs 貼上 earlephilhower/arduino-pico 的開發板索引網址，再到 Boards Manager
#    搜尋 "pico" 安裝 —— 這一步是 Arduino IDE 的 GUI 設定，寫在偏好設定檔裡風險較高
#    (可能覆蓋你原本的設定)，所以用印出來的方式提醒你手動貼上
Write-Host ""
Write-Host "Arduino IDE 開好後，請到 File > Preferences > Additional Boards Manager URLs 貼上以下網址，"
Write-Host "再到 Tools > Board > Boards Manager 搜尋 pico 安裝，才找得到 Raspberry Pi Pico / Pico W 這個板子："
Write-Host "  https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json"

# 4. 如果之後想改用 MicroPython (而不是 Arduino C++) 開發 Pico，也可以改用 Thonny IDE，
#    燒錄 UF2 韌體跟編輯程式都內建在同一個軟體裡，對新手更簡單
Write-Host ""
Write-Host "備註：如果想改用 MicroPython 開發 (更適合新手)，可以改裝 Thonny IDE：https://thonny.org/"
