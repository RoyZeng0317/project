import machine
import time
import framebuf

ILI9341_NOP = 0x00
ILI9341_SWRESET = 0x01
ILI9341_RDDID = 0x04
ILI9341_RDDST = 0x09
ILI9341_SLPIN = 0x10
ILI9341_SLPOUT = 0x11
ILI9341_PTLON = 0x12
ILI9341_NORON = 0x13
ILI9341_RDMODE = 0x0A
ILI9341_RDMADCTL = 0x0B
ILI9341_RDPIXFMT = 0x0C
ILI9341_RDIMGFMT = 0x0D
ILI9341_RDSELFDIAG = 0x0F
ILI9341_INVOFF = 0x20
ILI9341_INVON = 0x21
ILI9341_GAMMASET = 0x26
ILI9341_DISPOFF = 0x28
ILI9341_DISPON = 0x29
ILI9341_CASET = 0x2A
ILI9341_PASET = 0x2B
ILI9341_RAMWR = 0x2C
ILI9341_RAMRD = 0x2E
ILI9341_PTLAR = 0x30
ILI9341_VSCRDEF = 0x33
ILI9341_DISCOFF = 0x34
ILI9341_DISCON = 0x35
ILI9341_TEOFF = 0x34
ILI9341_TEON = 0x35
ILI9341_MADCTL = 0x36
ILI9341_VSCRSADD = 0x37
ILI9341_IDMOFF = 0x38
ILI9341_IDMON = 0x39
ILI9341_PIXFMT = 0x3A
ILI9341_WRMEMCONT = 0x3C
ILI9341_RDMEMCONT = 0x3E
ILI9341_SETTEARLINE = 0x44
ILI9341_GAMMA1 = 0xE0
ILI9341_GAMMA2 = 0xE1

MADCTL_MY = 0x80
MADCTL_MX = 0x40
MADCTL_MV = 0x20
MADCTL_ML = 0x10
MADCTL_BGR = 0x08
MADCTL_MH = 0x04


class ILI9341:
    def __init__(self, spi, cs, dc, rst, width=320, height=240, rotation=0):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.width = width
        self.height = height
        self.rotation = rotation

        self.cs.init(mode=machine.Pin.OUT, value=1)
        self.dc.init(mode=machine.Pin.OUT, value=0)
        self.rst.init(mode=machine.Pin.OUT, value=1)

        self.buf_size = width * height * 2
        self._buffer = None

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
        self.rst.off()
        time.sleep_ms(50)
        self.rst.on()
        time.sleep_ms(120)

        self._write_cmd(ILI9341_SWRESET)
        time.sleep_ms(120)

        self._write_cmd(0xEF, b"\x03\x80\x02")
        self._write_cmd(0xCF, b"\x00\xC1\x30")
        self._write_cmd(0xED, b"\x64\x03\x12\x81")
        self._write_cmd(0xE8, b"\x85\x00\x78")
        self._write_cmd(0xCB, b"\x39\x2C\x00\x34\x02")
        self._write_cmd(0xF7, b"\x20")
        self._write_cmd(0xEA, b"\x00\x00")

        self._write_cmd(ILI9341_PIXFMT, b"\x55")

        self._write_cmd(ILI9341_MADCTL, bytes([self._madctl_value()]))

        self._write_cmd(ILI9341_INVOFF)

        self._write_cmd(0xB1, b"\x00\x1B")
        self._write_cmd(0xB6, b"\x0A\x82\x27\x00")
        self._write_cmd(0xB7, b"\x06")
        self._write_cmd(0xF2, b"\x00")
        self._write_cmd(0x26, b"\x01")
        self._write_cmd(0xE0, b"\x0F\x31\x2B\x0C\x0E\x08\x4E\xF1\x37\x07\x10\x03\x0E\x09\x00")
        self._write_cmd(0xE1, b"\x00\x0E\x14\x03\x11\x07\x31\xC1\x48\x08\x0F\x0C\x31\x36\x0F")

        self._write_cmd(ILI9341_SLPOUT)
        time.sleep_ms(120)

        self._write_cmd(ILI9341_DISPON)
        time.sleep_ms(100)

    def _madctl_value(self):
        rotation_vals = {
            0: 0x00,
            1: MADCTL_MX | MADCTL_MV | MADCTL_MY,
            2: MADCTL_MX | MADCTL_MY,
            3: MADCTL_MV,
        }
        return rotation_vals.get(self.rotation % 4, 0x00) | MADCTL_BGR

    def _set_window(self, x0, y0, x1, y1):
        self._write_cmd(ILI9341_CASET, struct.pack(">HH", x0, x1))
        self._write_cmd(ILI9341_PASET, struct.pack(">HH", y0, y1))

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
        self._write_cmd(ILI9341_RAMWR, buf)

    def fill(self, color):
        self.fill_rect(0, 0, self.width, self.height, color)

    def pixel(self, x, y, color):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        self._set_window(x, y, x, y)
        self._write_cmd(ILI9341_RAMWR, struct.pack(">H", color))

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
        self._write_cmd(ILI9341_RAMWR, buf)

    def text(self, string, x, y, color=0xFFFF, bg=None, font=None):
        if font is None:
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
        self._write_cmd(ILI9341_DISPOFF)


FONT8_WIDTH = 8
FONT8_MAP = [
    b"\x00\x00\x00\x00\x00\x00\x00\x00",
    b"\x20\x20\x20\x20\x00\x20\x00\x00",
    b"\x50\x50\x50\x00\x00\x00\x00\x00",
    b"\x50\xf8\x50\x50\xf8\x50\x00\x00",
    b"\x20\x78\xa0\x70\x28\xf0\x20\x00",
    b"\xc0\xc8\x10\x20\x40\x98\x18\x00",
    b"\x40\xa0\x40\xa8\x90\x68\x00\x00",
    b"\x10\x20\x20\x00\x00\x00\x00\x00",
    b"\x10\x20\x40\x40\x40\x20\x10\x00",
    b"\x40\x20\x10\x10\x10\x20\x40\x00",
    b"\x00\x20\xa8\x70\xa8\x20\x00\x00",
    b"\x00\x20\x20\xf8\x20\x20\x00\x00",
    b"\x00\x00\x00\x00\x20\x20\x40\x00",
    b"\x00\x00\x00\xf8\x00\x00\x00\x00",
    b"\x00\x00\x00\x00\x60\x60\x00\x00",
    b"\x00\x08\x10\x20\x40\x80\x00\x00",
    b"\x70\x88\x98\xa8\xc8\x88\x70\x00",
    b"\x20\x60\x20\x20\x20\x20\xf8\x00",
    b"\x70\x88\x08\x30\x40\x80\xf8\x00",
    b"\x70\x88\x08\x30\x08\x88\x70\x00",
    b"\x10\x30\x50\x90\xf8\x10\x10\x00",
    b"\xf8\x80\xf0\x08\x08\x88\x70\x00",
    b"\x30\x40\x80\xf0\x88\x88\x70\x00",
    b"\xf8\x08\x10\x20\x40\x40\x40\x00",
    b"\x70\x88\x88\x70\x88\x88\x70\x00",
    b"\x70\x88\x88\x78\x08\x10\x60\x00",
    b"\x00\x20\x20\x00\x20\x20\x00\x00",
    b"\x00\x20\x20\x00\x20\x20\x40\x00",
    b"\x10\x20\x40\x80\x40\x20\x10\x00",
    b"\x00\x00\xf8\x00\xf8\x00\x00\x00",
    b"\x40\x20\x10\x08\x10\x20\x40\x00",
    b"\x70\x88\x08\x10\x20\x00\x20\x00",
    b"\x70\x88\x08\x68\xa8\xa8\x70\x00",
    b"\x20\x50\x88\x88\xf8\x88\x88\x00",
    b"\xf0\x88\x88\xf0\x88\x88\xf0\x00",
    b"\x70\x88\x80\x80\x80\x88\x70\x00",
    b"\xe0\x90\x88\x88\x88\x90\xe0\x00",
    b"\xf8\x80\x80\xf0\x80\x80\xf8\x00",
    b"\xf8\x80\x80\xf0\x80\x80\x80\x00",
    b"\x70\x88\x80\xb8\x88\x88\x78\x00",
    b"\x88\x88\x88\xf8\x88\x88\x88\x00",
    b"\x70\x20\x20\x20\x20\x20\x70\x00",
    b"\x08\x08\x08\x08\x08\x88\x70\x00",
    b"\x88\x90\xa0\xc0\xa0\x90\x88\x00",
    b"\x80\x80\x80\x80\x80\x80\xf8\x00",
    b"\x88\xd8\xa8\xa8\x88\x88\x88\x00",
    b"\x88\xc8\xa8\x98\x88\x88\x88\x00",
    b"\x70\x88\x88\x88\x88\x88\x70\x00",
    b"\xf0\x88\x88\xf0\x80\x80\x80\x00",
    b"\x70\x88\x88\x88\xa8\x90\x68\x00",
    b"\xf0\x88\x88\xf0\xa0\x90\x88\x00",
    b"\x70\x88\x80\x70\x08\x88\x70\x00",
    b"\xf8\x20\x20\x20\x20\x20\x20\x00",
    b"\x88\x88\x88\x88\x88\x88\x70\x00",
    b"\x88\x88\x88\x88\x50\x50\x20\x00",
    b"\x88\x88\x88\xa8\xa8\xd8\x88\x00",
    b"\x88\x88\x50\x20\x50\x88\x88\x00",
    b"\x88\x88\x50\x20\x20\x20\x20\x00",
    b"\xf8\x08\x10\x20\x40\x80\xf8\x00",
    b"\x70\x40\x40\x40\x40\x40\x70\x00",
    b"\x00\x80\x40\x20\x10\x08\x00\x00",
    b"\x70\x10\x10\x10\x10\x10\x70\x00",
    b"\x20\x50\x88\x00\x00\x00\x00\x00",
    b"\x00\x00\x00\x00\x00\x00\xf8\x00",
    b"\x40\x20\x10\x00\x00\x00\x00\x00",
    b"\x00\x00\x70\x08\x78\x88\x78\x00",
    b"\x80\x80\xb0\xc8\x88\xc8\xb0\x00",
    b"\x00\x00\x70\x88\x80\x88\x70\x00",
    b"\x08\x08\x68\x98\x88\x98\x68\x00",
    b"\x00\x00\x70\x88\xf8\x80\x70\x00",
    b"\x10\x28\x20\x70\x20\x20\x20\x00",
    b"\x00\x00\x68\x98\x88\x98\x68\x08",
    b"\x80\x80\xb0\xc8\x88\x88\x88\x00",
    b"\x20\x00\x60\x20\x20\x20\x70\x00",
    b"\x10\x00\x30\x10\x10\x10\x90\x60",
    b"\x80\x80\x90\xa0\xc0\xa0\x90\x00",
    b"\x60\x20\x20\x20\x20\x20\x70\x00",
    b"\x00\x00\xd0\xa8\xa8\xa8\x88\x00",
    b"\x00\x00\xb0\xc8\x88\x88\x88\x00",
    b"\x00\x00\x70\x88\x88\x88\x70\x00",
    b"\x00\x00\xb0\xc8\x88\xc8\xb0\x80",
    b"\x00\x00\x68\x98\x88\x98\x68\x08",
    b"\x00\x00\xb0\xc8\x80\x80\x80\x00",
    b"\x00\x00\x78\x80\x70\x08\xf0\x00",
    b"\x40\x40\xe0\x40\x40\x48\x30\x00",
    b"\x00\x00\x88\x88\x88\x98\x68\x00",
    b"\x00\x00\x88\x88\x88\x50\x20\x00",
    b"\x00\x00\x88\x88\xa8\xa8\x50\x00",
    b"\x00\x00\x88\x50\x20\x50\x88\x00",
    b"\x00\x00\x88\x88\x88\x78\x08\x70",
    b"\x00\x00\xf8\x10\x20\x40\xf8\x00",
    b"\x18\x20\x20\x40\x20\x20\x18\x00",
    b"\x20\x20\x20\x20\x20\x20\x20\x00",
    b"\xc0\x20\x20\x10\x20\x20\xc0\x00",
    b"\x40\xa8\x10\x00\x00\x00\x00\x00",
]

FONT8 = {
    "width": 8,
    "height": 8,
    "map": FONT8_MAP,
}

import struct
