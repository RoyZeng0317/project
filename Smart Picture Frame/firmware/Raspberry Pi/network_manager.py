import network
import time


class NetworkManager:
    def __init__(self, config):
        self.config = config["wifi"]
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self._connected = False

    def connect(self):
        if self.wlan.isconnected():
            self._connected = True
            return True
        ssid = self.config["ssid"]
        password = self.config["password"]
        if ssid == "YOUR_WIFI_SSID":
            return False
        self.wlan.connect(ssid, password)
        timeout = self.config.get("connect_timeout", 30)
        for _ in range(timeout):
            if self.wlan.isconnected():
                self._connected = True
                return True
            time.sleep(1)
        self._connected = False
        return False

    def disconnect(self):
        if self.wlan.isconnected():
            self.wlan.disconnect()
        self._connected = False

    def is_connected(self):
        return self.wlan.isconnected()

    def get_ip(self):
        return self.wlan.ifconfig()[0] if self.is_connected() else None

    def get_rssi(self):
        return self.wlan.status("rssi") if self.is_connected() else None
