from screens.base_screen import BaseScreen


class PhotoScreen(BaseScreen):
    def draw(self, photo_file=None, **kwargs):
        self.display.fill(self.bg)
        if photo_file is None:
            self.display.text("無圖片可用", 10, 100, self.dim)
            self.display.text("請將 .rgb565 圖片放入 SD 卡", 10, 120, self.dim)
            return
        try:
            with open(photo_file, "rb") as f:
                w = min(self.width, 320)
                h = min(self.height, 240)
                buf = f.read(w * h * 2)
                if buf:
                    x = (self.width - w) // 2
                    y = (self.height - h) // 2
                    self.display.blit_buffer(buf, x, y, w, h)
        except Exception as e:
            self.display.fill(self.bg)
            self.display.text(f"無法載入圖片", 10, 100, self.accent)

    def handle_touch(self, x, y):
        return "next_photo"
