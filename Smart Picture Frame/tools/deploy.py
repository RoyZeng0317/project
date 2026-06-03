import os
import sys
import time
import subprocess


def find_pico_port():
    import serial.tools.list_ports as list_ports
    for port in list_ports.comports():
        if "USB" in port.description and "Serial" in port.description:
            return port.device
        if "UART" in port.description:
            return port.device
    return None


def deploy():
    src_dir = os.path.join(os.path.dirname(__file__), "..", "firmware")
    src_dir = os.path.abspath(src_dir)

    port = find_pico_port()
    if not port:
        print("請連接 Pico 2W 並確認序列埠")
        return

    files_to_deploy = [
        "config.py",
        "main.py",
        "network_manager.py",
        "ntp_time.py",
        "weather.py",
        "photo_manager.py",
        "todo_manager.py",
        "drivers/ili9341.py",
        "drivers/st7789.py",
        "drivers/xpt2046.py",
        "drivers/sdcard.py",
        "lib/font_large.py",
        "screens/base_screen.py",
        "screens/clock_screen.py",
        "screens/weather_screen.py",
        "screens/calendar_screen.py",
        "screens/photo_screen.py",
        "screens/dashboard_screen.py",
    ]

    print(f"部署到 {port} ...")
    for filepath in files_to_deploy:
        local_path = os.path.join(src_dir, filepath)
        remote_path = filepath.replace("\\", "/")
        if not os.path.exists(local_path):
            print(f"  跳過 (不存在): {filepath}")
            continue
        try:
            subprocess.run(
                ["ampy", "--port", port, "put", local_path, remote_path],
                check=True,
                capture_output=True,
            )
            print(f"  ✓ {filepath}")
        except subprocess.CalledProcessError:
            try:
                subprocess.run(
                    ["rshell", "-p", port, "cp", local_path, f"/pyboard/{remote_path}"],
                    check=True,
                    capture_output=True,
                )
                print(f"  ✓ {filepath} (via rshell)")
            except:
                print(f"  ✗ {filepath} - 失敗")

    print("\n部署完成！重新啟動 Pico 2W...")


def deploy_single(filepath):
    src_dir = os.path.join(os.path.dirname(__file__), "..", "firmware")
    src_dir = os.path.abspath(src_dir)
    port = find_pico_port()
    if not port:
        print("請連接 Pico 2W")
        return
    local_path = os.path.join(src_dir, filepath)
    remote_path = filepath.replace("\\", "/")
    if os.path.exists(local_path):
        subprocess.run(["ampy", "--port", port, "put", local_path, remote_path])
        print(f"部署 {filepath} ✓")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        deploy_single(sys.argv[1])
    else:
        deploy()
