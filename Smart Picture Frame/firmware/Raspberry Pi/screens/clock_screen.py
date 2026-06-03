import time
from screens.base_screen import BaseScreen


class ClockScreen(BaseScreen):
    def draw(self, time_data=None, **kwargs):
        self.display.fill(self.bg)
        if time_data is None:
            return
        cx = self.width // 2
        time_str = f"{time_data['hour']:02d}:{time_data['minute']:02d}"
        date_str = f"{time_data['year']}/{time_data['month']:02d}/{time_data['day']:02d}"
        dow_str = f"星期{time_data['weekday_zh']}"

        font_large_h = 48
        char_w = self.width // len(time_str)
        x_offset = (self.width - len(time_str) * char_w) // 2
        self._draw_large_time(x_offset, 60, time_str, char_w, font_large_h)

        self.display.text(date_str, cx - len(date_str) * 4, 130, self.dim)
        self.display.text(dow_str, cx - len(dow_str) * 4, 145, self.dim)

        self.display.hline(40, 165, self.width - 80, self.primary)

    def _draw_large_time(self, x, y, time_str, char_w, char_h):
        for i, ch in enumerate(time_str):
            block_x = x + i * char_w
            block_w = char_w - 4
            if ch == ":":
                self.display.fill_rect(
                    block_x + block_w // 2 - 2,
                    y + char_h // 2 - 4,
                    4,
                    4,
                    self.primary,
                )
                self.display.fill_rect(
                    block_x + block_w // 2 - 2,
                    y + char_h // 2 + 8,
                    4,
                    4,
                    self.primary,
                )
                continue
            seg_w = block_w // 4
            seg_h = char_h // 4
            h_seg = seg_h
            w_seg = seg_w
            ox = block_x + seg_w
            oy = y + seg_h
            self.display.fill_rect(ox, oy, w_seg * 2, h_seg, self.fg)
            self.display.fill_rect(ox, oy + h_seg * 2, w_seg * 2, h_seg, self.fg)
            self.display.fill_rect(ox, oy + h_seg * 4, w_seg * 2, h_seg, self.fg)
            self.display.fill_rect(ox - w_seg, oy + h_seg, w_seg, h_seg, self.fg)
            self.display.fill_rect(ox + w_seg * 2, oy + h_seg, w_seg, h_seg, self.fg)
            self.display.fill_rect(ox - w_seg, oy + h_seg * 3, w_seg, h_seg, self.fg)
            self.display.fill_rect(ox + w_seg * 2, oy + h_seg * 3, w_seg, h_seg, self.fg)
