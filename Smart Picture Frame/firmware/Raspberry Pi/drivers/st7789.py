import machine
import time
import struct

ST7789_NOP = 0x00
ST7789_SWRESET = 0x01
ST7789_SLPIN = 0x10
ST7789_SLPOUT = 0x11
ST7789_NORON = 0x13
ST7789_INVOFF = 0x20
ST7789_INVON = 0x21
ST7789_DISPOFF = 0x28
ST7789_DISPON = 0x29
ST7789_CASET = 0x2A
ST7789_PASET = 0x2B
ST7789_RAMWR = 0x2C
ST7789_RAMRD = 0x2E
ST7789_PTLAR = 0x30
ST7789_VSCRDEF = 0x33
ST7789_TEOFF = 0x34
ST7789_TEON = 0x35
ST7789_MADCTL = 0x36
ST7789_VSCRSADD = 0x37
ST7789_COLMOD = 0x3A
ST7789_GATECTRL = 0xE4
ST7789_PORCTRL = 0xB2
ST7789_GCTRL = 0xB7
ST7789_VCOMS = 0xBB
ST7789_LCMCTRL = 0xC0
ST7789_VDVVRHEN = 0xC2
ST7789_VRHS = 0xC3
ST7789_VDVS = 0xC4
ST7789_FRCTRL2 = 0xC6
ST7789_PWCTRL1 = 0xD0
ST7789_PVGAMCTRL = 0xE0
ST7789_NVGAMCTRL = 0xE1
ST7789_RAMCTRL = 0xB0

MADCTL_MY = 0x80
MADCTL_MX = 0x40
MADCTL_MV = 0x20
MADCTL_ML = 0x10
MADCTL_BGR = 0x08
MADCTL_MH = 0x04


class ST7789:
    def __init__(self, spi, cs, dc, rst=None, bl=None, width=240, height=240, rotation=0):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.bl = bl
        self.width = width
        self.height = height
        self.rotation = rotation

        self.cs.init(mode=machine.Pin.OUT, value=1)
        self.dc.init(mode=machine.Pin.OUT, value=0)
        if self.rst:
            self.rst.init(mode=machine.Pin.OUT, value=1)
        if self.bl:
            self.bl.init(mode=machine.Pin.OUT, value=1)

        self._init_display()

    def _write_cmd(self, cmd, data=None):
        self.cs.off()
        self.dc.off()
        self.spi.write(bytearray([cmd]))
        if data:
            self.dc.on()
            self.spi.write(data)
        self.cs.on()

    def _write_data(self, data):
        self.cs.off()
        self.dc.on()
        self.spi.write(data)
        self.cs.on()

    def _init_display(self):
        if self.rst:
            self.rst.off()
            time.sleep_ms(50)
            self.rst.on()
            time.sleep_ms(150)

        self._write_cmd(ST7789_SWRESET)
        time.sleep_ms(150)

        self._write_cmd(ST7789_SLPOUT)
        time.sleep_ms(10)

        self._write_cmd(ST7789_COLMOD, b"\x55")
        time.sleep_ms(10)

        self._write_cmd(ST7789_MADCTL, bytes([self._madctl_value()]))

        self._write_cmd(ST7789_CASET, struct.pack(">II", 0, self.width - 1))
        self._write_cmd(ST7789_PASET, struct.pack(">II", 0, self.height - 1))

        self._write_cmd(ST7789_INVOFF)

        self._write_cmd(ST7789_NORON)
        time.sleep_ms(10)

        self._write_cmd(ST7789_DISPON)
        time.sleep_ms(100)

        if self.bl:
            self.bl.on()

    def _madctl_value(self):
        rotation_vals = {
            0: 0x00,
            1: MADCTL_MX | MADCTL_MV | MADCTL_MY,
            2: MADCTL_MX | MADCTL_MY,
            3: MADCTL_MV,
        }
        return rotation_vals.get(self.rotation % 4, 0x00) | MADCTL_BGR

    def _set_window(self, x0, y0, x1, y1):
        self._write_cmd(ST7789_CASET, struct.pack(">HH", x0, x1))
        self._write_cmd(ST7789_PASET, struct.pack(">HH", y0, y1))

    def fill_rect(self, x, y, w, h, color):
        if x < 0 or y < 0 or w <= 0 or h <= 0:
            return
        if x + w > self.width:
            w = self.width - x
        if y + h > self.height:
            h = self.height - y
        self._set_window(x, y, x + w - 1, y + h - 1)
        pixels = w * h
        buf = bytearray(pixels * 2)
        hi = (color >> 8) & 0xFF
        lo = color & 0xFF
        for i in range(pixels * 2):
            buf[i] = hi if i % 2 == 0 else lo
        self._write_cmd(ST7789_RAMWR, buf)

    def fill(self, color):
        self.fill_rect(0, 0, self.width, self.height, color)

    def pixel(self, x, y, color):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        self._set_window(x, y, x, y)
        self._write_cmd(ST7789_RAMWR, struct.pack(">H", color))

    def hline(self, x, y, w, color):
        self.fill_rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.fill_rect(x, y, 1, h, color)

    def rect(self, x, y, w, h, color):
        self.hline(x, y, w, color)
        self.hline(x, y + h - 1, w, color)
        self.vline(x, y, h, color)
        self.vline(x + w - 1, y, h, color)

    def line(self, x0, y0, x1, y1, color):
        steep = abs(y1 - y0) > abs(x1 - x0)
        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1
        if x0 > x1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0
        dx = x1 - x0
        dy = abs(y1 - y0)
        err = dx // 2
        ystep = 1 if y0 < y1 else -1
        while x0 <= x1:
            if steep:
                self.pixel(y0, x0, color)
            else:
                self.pixel(x0, y0, color)
            err -= dy
            if err < 0:
                y0 += ystep
                err += dx
            x0 += 1

    def blit_buffer(self, buf, x, y, w, h):
        if x < 0 or y < 0 or w <= 0 or h <= 0:
            return
        if x + w > self.width:
            w = self.width - x
        if y + h > self.height:
            h = self.height - y
        self._set_window(x, y, x + w - 1, y + h - 1)
        self._write_cmd(ST7789_RAMWR, buf)

    def text(self, string, x, y, color=0xFFFF, bg=None, font=None):
        if font is None:
            from drivers.ili9341 import FONT8
            font = FONT8
        x_start = x
        for char in string:
            if ord(char) < 32 or ord(char) > 127:
                char = "?"
            self._draw_char(char, x, y, color, bg, font)
            x += font["width"]
            if x + font["width"] > self.width:
                x = x_start
                y += font["height"]

    def _draw_char(self, char, x, y, color, bg, font):
        char_index = ord(char) - 32
        if char_index < 0 or char_index >= len(font["map"]):
            return
        char_data = font["map"][char_index]
        for row in range(font["height"]):
            row_data = char_data[row]
            bit = 0x80
            for col in range(font["width"]):
                if row_data & bit:
                    self.pixel(x + col, y + row, color)
                elif bg is not None:
                    self.pixel(x + col, y + row, bg)
                bit >>= 1

    def cleanup(self):
        self.fill(0x0000)
        self._write_cmd(ST7789_DISPOFF)
