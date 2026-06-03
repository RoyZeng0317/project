import json
import time

try:
    import urequests as requests
except:
    import requests


class WeatherManager:
    WEATHER_ICONS = {
        "01d": "\u2600",
        "01n": "\u263D",
        "02d": "\u26C5",
        "02n": "\u26C5",
        "03d": "\u2601",
        "03n": "\u2601",
        "04d": "\u2601",
        "04n": "\u2601",
        "09d": "\u2614",
        "09n": "\u2614",
        "10d": "\u2614",
        "10n": "\u2614",
        "11d": "\u26C8",
        "11n": "\u26C8",
        "13d": "\u2744",
        "13n": "\u2744",
        "50d": "\u2B14",
        "50n": "\u2B14",
    }

    def __init__(self, config, network_manager):
        self.config = config["weather"]
        self.net = network_manager
        self._cache = None
        self._last_update = 0
        self._update_interval = self.config.get("update_interval", 1800)

    def fetch(self):
        if not self.net.is_connected():
            return None
        api_key = self.config.get("api_key", "")
        if api_key == "YOUR_OPENWEATHERMAP_API_KEY":
            return None
        city = self.config.get("city", "Taipei")
        units = self.config.get("units", "metric")
        lang = self.config.get("lang", "zh_tw")
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&units={units}&lang={lang}&appid={api_key}"
        )
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = json.loads(resp.text)
                self._cache = self._parse(data)
                self._last_update = time.time()
                resp.close()
                return self._cache
            resp.close()
        except Exception:
            pass
        return None

    def _parse(self, data):
        return {
            "city": data.get("name", ""),
            "temp": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "temp_min": data["main"]["temp_min"],
            "temp_max": data["main"]["temp_max"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "description": data["weather"][0]["description"],
            "icon": data["weather"][0]["icon"],
            "wind_speed": data["wind"]["speed"],
            "icon_char": self.WEATHER_ICONS.get(
                data["weather"][0]["icon"], "?"
            ),
        }

    def get_weather(self):
        if self._cache is None or time.time() - self._last_update > self._update_interval:
            self.fetch()
        return self._cache

    def need_update(self):
        return (
            self._cache is None
            or time.time() - self._last_update > self._update_interval
        )
