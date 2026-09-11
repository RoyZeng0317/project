# 電腦端：一鍵編譯 + 燒錄 ESP32-S3-CAM/SmartFrame 韌體，取代手動開 Arduino IDE 按上傳。
# ESP32-S3 是透過 USB 轉序列晶片(CP210x/CH340等)燒錄，上傳時晶片會自動重置進燒錄模式，
# 不像 Pico 需要實體按 BOOTSEL，所以這一步可以完全自動化(呼叫 Arduino IDE 內建的 arduino-cli)。
# 第一次執行會自動裝 esp32 開發板套件 + LovyanGFX 函式庫(比照 ESP32-S3/install.ps1 的手動步驟)，
# 已經裝過的話會直接跳過，不會每次重裝，所以第一次會比較久、之後就很快。
# 用法：接上 USB 線，到「裝置管理員 > 連接埠(COM與LPT)」找到板子的 COM 埠後執行:
#   python esp32_deploy.py COM6
import glob, os, shutil, subprocess, sys

sys.stdout.reconfigure(errors="replace")  # arduino-cli 輸出偶爾夾雜 Windows 主控台編碼印不出的字元，印壞就整支腳本炸掉太脆弱

SKETCH_BASE = os.path.join(os.path.dirname(__file__), "ESP32-S3-CAM")
FQBN = "esp32:esp32:esp32s3:PSRAM=opi"  # 對應 Tools > Board > ESP32S3 Dev Module + PSRAM > OPI PSRAM
BOARD_URL = "https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json"


def _run(cmd, check=True):
    # 用 Popen 逐行讀輸出再 print，而不是直接 subprocess.run()，這樣編譯錯誤訊息才能
    # 即時透過 print() 被 GUI 的記錄視窗(pico_deploy_gui.py 同款做法)捕捉到
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    for line in proc.stdout:
        print(line, end="")
    proc.wait()
    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)


def _find_cli():
    found = shutil.which("arduino-cli")
    if found:
        return found
    # Arduino IDE 2.x 內建就有一份 arduino-cli.exe，裝好 Arduino IDE(install.ps1 會自動裝)就有，
    # 不用使用者另外再裝一次 arduino-cli
    pattern = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe")
    matches = glob.glob(pattern)
    if matches:
        return matches[0]
    raise RuntimeError("找不到 arduino-cli，請先執行 ESP32-S3/install.ps1 安裝 Arduino IDE")


def _ensure_core_and_lib(cli):
    installed_core = subprocess.run([cli, "core", "list"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    if "esp32:esp32" not in installed_core:
        print("首次燒錄，安裝 esp32 開發板套件(檔案較大，請耐心等候)...\n")
        _run([cli, "core", "update-index", "--additional-urls", BOARD_URL])
        _run([cli, "core", "install", "esp32:esp32", "--additional-urls", BOARD_URL])

    installed_lib = subprocess.run([cli, "lib", "list"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    if "LovyanGFX" not in installed_lib:
        print("安裝 LovyanGFX 函式庫...\n")
        _run([cli, "lib", "install", "LovyanGFX"])


def deploy(port, sketch="SmartFrame"):
    cli = _find_cli()
    _ensure_core_and_lib(cli)
    sketch_dir = os.path.join(SKETCH_BASE, sketch)
    print(f"編譯並上傳 {sketch} -> {port}\n")
    _run([cli, "compile", "--upload", "-p", port, "--fqbn", FQBN, sketch_dir])
    print("\n燒錄完成，ESP32-S3-CAM 已自動重啟執行新韌體")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print("用法: python esp32_deploy.py <COM埠> [韌體資料夾，預設SmartFrame]，例如 python esp32_deploy.py COM6 display_test")
        sys.exit(1)
    deploy(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else "SmartFrame")
