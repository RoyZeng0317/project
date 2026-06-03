from screens.base_screen import BaseScreen


class WeatherScreen(BaseScreen):
    def draw(self, weather_data=None, **kwargs):
        self.display.fill(self.bg)
        if weather_data is None:
            self.display.text("天氣資料加載中...", 10, 100, self.dim)
            return
        cx = self.width // 2
        icon = weather_data.get("icon_char", "?")
        temp = weather_data.get("temp", "--")
        desc = weather_data.get("description", "")
        city = weather_data.get("city", "")
        feels_like = weather_data.get("feels_like", "--")
        humidity = weather_data.get("humidity", "--")

        self.display.text(city, cx - len(city) * 4, 30, self.primary)
        self.display.fill_rect(cx - 30, 50, 60, 60, self.primary)
        temp_str = f"{temp:.0f}°C"
        self.display.text(temp_str, cx - len(temp_str) * 4, 115, self.fg)
        self.display.text(desc, cx - len(desc) * 4, 135, self.dim)

        info_y = 160
        self.display.text(f"體感: {feels_like:.0f}°C", 20, info_y, self.dim)
        self.display.text(f"濕度: {humidity}%", 20, info_y + 14, self.dim)

        self.display.hline(20, info_y - 4, self.width - 40, self.primary)
