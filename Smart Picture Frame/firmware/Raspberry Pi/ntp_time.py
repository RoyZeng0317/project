import ntptime
import time


class TimeManager:
    TIME_UNITS = ("", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    TIME_UNITS_ZH = ("", "一", "二", "三", "四", "五", "六", "日")

    def __init__(self, config):
        self.config = config["ntp"]
        self.tz = self.config.get("timezone", 8)
        self._last_sync = 0
        self._update_interval = self.config.get("update_interval", 3600)
        self._rtc = None

    def _init_rtc(self):
        try:
            from machine import RTC
            self._rtc = RTC()
        except:
            self._rtc = None

    def sync(self):
        try:
            ntptime.host = self.config.get("server", "pool.ntp.org")
            ntptime.timeout = 5
            ntptime.settime()
            self._last_sync = time.time()
            self._init_rtc()
            return True
        except Exception:
            return False

    def need_sync(self):
        return (time.time() - self._last_sync) > self._update_interval

    def sync_if_needed(self):
        if self.need_sync():
            self.sync()

    def get_time(self):
        year, month, day, weekday, hour, minute, second, _ = time.gmtime(
            time.time() + self.tz * 3600
        )
        return {
            "year": year,
            "month": month,
            "day": day,
            "weekday": weekday,
            "weekday_str": self.TIME_UNITS[weekday],
            "weekday_zh": self.TIME_UNITS_ZH[weekday],
            "hour": hour,
            "minute": minute,
            "second": second,
        }

    def get_date_str(self, fmt="zh"):
        t = self.get_time()
        if fmt == "zh":
            return f"{t['year']}年{t['month']}月{t['day']}日"
        return f"{t['year']}-{t['month']:02d}-{t['day']:02d}"

    def get_time_str(self):
        t = self.get_time()
        return f"{t['hour']:02d}:{t['minute']:02d}:{t['second']:02d}"

    def get_short_time_str(self):
        t = self.get_time()
        return f"{t['hour']:02d}:{t['minute']:02d}"
