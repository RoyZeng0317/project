class BaseScreen:
    def __init__(self, display, config):
        self.display = display
        self.cfg = config["ui"]
        self.bg = self.cfg.get("color_bg", 0x0000)
        self.fg = self.cfg.get("color_text", 0xFFFF)
        self.dim = self.cfg.get("color_text_dim", 0x8410)
        self.primary = self.cfg.get("color_primary", 0x001F)
        self.secondary = self.cfg.get("color_secondary", 0x07E0)
        self.accent = self.cfg.get("color_accent", 0xF800)
        self.width = config["display"]["width"]
        self.height = config["display"]["height"]

    def draw(self, **kwargs):
        raise NotImplementedError

    def handle_touch(self, x, y):
        pass

    def enter(self):
        pass

    def leave(self):
        pass

    def _draw_status_bar(self, time_str, wifi_status=False):
        bar_h = 10
        self.display.fill_rect(0, 0, self.width, bar_h, self.primary)
        self.display.text(time_str, 2, 1, 0xFFFF, self.primary)
        if wifi_status:
            self.display.text("W", self.width - 12, 1, self.secondary, self.primary)
