# 電腦端：一鍵編譯 + 燒錄 Mega2560 韌體(MEGA2560_test/mega2560_tft_test)，取代手動開 Arduino IDE 按上傳。
# Mega2560 走 USB 轉序列晶片，上傳時會自動重置進燒錄模式，不用像 Pico 那樣按實體 BOOTSEL，
# 所以這一步一樣能完全自動化(呼叫 Arduino IDE 內建的 arduino-cli)，邏輯照抄 esp32_deploy.py。
# 第一次執行會自動裝 arduino:avr 開發板套件 + Adafruit GFX Library/MCUFRIEND_kbv(已裝過會跳過)。
# 用法：接上 USB 線，到「裝置管理員 > 連接埠(COM與LPT)」找到板子的 COM 埠後執行:
#   python mega_deploy.py COM6 [MEGA2560_test|mega2560_tft_test，預設 MEGA2560_test]
import glob, os, shutil, subprocess, sys

sys.stdout.reconfigure(errors="replace")  # arduino-cli 輸出偶爾夾雜 Windows 主控台編碼印不出的字元，印壞就整支腳本炸掉太脆弱

SKETCH_BASE = os.path.dirname(__file__)
FQBN = "arduino:avr:mega:cpu=atmega2560"  # 對應 Tools > Board > Arduino Mega or Mega 2560 > Processor > ATmega2560


def _run(cmd, check=True):
    # 用 Popen 逐行讀輸出再 print，而不是直接 subprocess.run()，這樣編譯錯誤訊息才能
    # 即時透過 print() 被 GUI 的記錄視窗(mega_deploy_gui.py 同款做法)捕捉到
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
    # Arduino IDE 2.x 內建就有一份 arduino-cli.exe，裝好 Arduino IDE(ESP32-S3/install.ps1 會自動裝)就有，
    # 不用使用者另外再裝一次 arduino-cli
    pattern = os.path.expandvars(r"%LOCALAPPDATA%\Programs\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe")
    matches = glob.glob(pattern)
    if matches:
        return matches[0]
    raise RuntimeError("找不到 arduino-cli，請先執行 ESP32-S3/install.ps1 安裝 Arduino IDE")


def _ensure_core_and_libs(cli):
    installed_core = subprocess.run([cli, "core", "list"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    if "arduino:avr" not in installed_core:
        print("首次燒錄，安裝 arduino:avr 開發板套件...\n")
        _run([cli, "core", "install", "arduino:avr"])

    installed_lib = subprocess.run([cli, "lib", "list"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    for lib in ("Adafruit GFX Library", "MCUFRIEND_kbv"):
        if lib not in installed_lib:
            print(f"安裝 {lib} 函式庫...\n")
            _run([cli, "lib", "install", lib])


def deploy(port, sketch="MEGA2560_test"):
    cli = _find_cli()
    _ensure_core_and_libs(cli)
    sketch_dir = os.path.join(SKETCH_BASE, sketch)
    print(f"編譯並上傳 {sketch} -> {port}\n")
    _run([cli, "compile", "--upload", "-p", port, "--fqbn", FQBN, sketch_dir])
    print("\n燒錄完成，Mega2560 已自動重啟執行新韌體")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print("用法: python mega_deploy.py <COM埠> [韌體資料夾，預設MEGA2560_test]，例如 python mega_deploy.py COM6 mega2560_tft_test")
        sys.exit(1)
    deploy(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else "MEGA2560_test")
