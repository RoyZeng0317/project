from screens.base_screen import BaseScreen


class DashboardScreen(BaseScreen):
    def draw(self, time_data=None, weather_data=None, todo_items=None,
             photo_file=None, **kwargs):
        self.display.fill(self.bg)

        self._draw_top_section(time_data, weather_data)
        self._draw_middle_section(photo_file)
        self._draw_bottom_section(todo_items)

    def _draw_top_section(self, time_data, weather_data):
        section_h = 70
        self.display.fill_rect(0, 0, self.width, section_h, 0x0008)

        if time_data:
            time_str = f"{time_data['hour']:02d}:{time_data['minute']:02d}"
            self.display.text(time_str, 15, 8, self.fg)
            date_str = f"{time_data['month']}/{time_data['day']} 星期{time_data['weekday_zh']}"
            self.display.text(date_str, 15, 42, self.dim)

        if weather_data:
            temp_str = f"{weather_data.get('temp', '--'):.0f}°C"
            desc = weather_data.get("description", "")
            self.display.text(temp_str, self.width - 70, 8, self.secondary)
            self.display.text(desc, self.width - 80, 42, self.dim)

        self.display.hline(0, section_h - 1, self.width, self.primary)

    def _draw_middle_section(self, photo_file):
        section_y = 70
        section_h = 100
        if photo_file:
            try:
                with open(photo_file, "rb") as f:
                    buf = f.read(self.width * section_h * 2)
                    if buf:
                        self.display.blit_buffer(buf, 0, section_y,
                                                 self.width, section_h)
            except:
                self._draw_placeholder(section_y, section_h, "圖片輪播")

    def _draw_placeholder(self, y, h, text):
        self.display.rect(8, y + 8, self.width - 16, h - 16, self.dim)
        self.display.text(text,
                          (self.width - len(text) * 8) // 2,
                          y + h // 2 - 4,
                          self.dim)

    def _draw_bottom_section(self, todo_items):
        section_y = 170
        remaining = self.height - section_y

        self.display.hline(0, section_y, self.width, self.primary)
        self.display.text("待辦事項", 8, section_y + 2, self.primary)

        items = todo_items or []
        max_display = (remaining - 4) // 14
        for i, item in enumerate(items[:max_display]):
            y = section_y + 16 + i * 14
            icon = "✓" if item.get("done") else "○"
            text = item.get("text", "")[:18]
            color = self.fg if not item.get("done") else self.dim
            self.display.text(f"{icon} {text}", 8, y, color)
