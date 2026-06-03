import os
import time

try:
    import urequests as requests
except:
    import requests


class PhotoManager:
    def __init__(self, config):
        self.config = config["photos"]
        self._files = []
        self._current_index = 0
        self._last_switch = 0
        self._interval = self.config.get("slideshow_interval", 10)

    def scan_sd_card(self):
        try:
            base = "/sd"
            self._files = [
                f"{base}/{fn}"
                for fn in os.listdir(base)
                if fn.lower().endswith((".rgb565", ".raw"))
            ]
            self._files.sort()
        except:
            self._files = []
        return self._files

    def add_url(self, url):
        urls = self.config.get("online_urls", [])
        if url not in urls:
            urls.append(url)

    def get_current(self):
        if not self._files:
            return None
        if self._current_index >= len(self._files):
            self._current_index = 0
        return self._files[self._current_index]

    def next(self):
        if not self._files:
            return None
        self._current_index = (self._current_index + 1) % len(self._files)
        return self._files[self._current_index]

    def prev(self):
        if not self._files:
            return None
        self._current_index = (self._current_index - 1) % len(self._files)
        return self._files[self._current_index]

    def should_switch(self):
        now = time.time()
        if now - self._last_switch >= self._interval:
            self._last_switch = now
            return True
        return False

    def read_rgb565(self, filepath, width, height):
        try:
            with open(filepath, "rb") as f:
                raw = f.read(width * height * 2)
                return raw
        except:
            return None

    def get_online_image(self):
        urls = self.config.get("online_urls", [])
        if not urls:
            return None
        import random
        url = random.choice(urls)
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.content
            resp.close()
        except:
            pass
        return None
