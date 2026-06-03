import machine
import time


class XPT2046:
    def __init__(self, spi, cs, irq=None, width=320, height=240, rotation=0):
        self.spi = spi
        self.cs = cs
        self.irq = irq
        self.width = width
        self.height = height
        self.rotation = rotation
        self._calibration = None

        self.cs.init(mode=machine.Pin.OUT, value=1)
        if self.irq:
            self.irq.init(mode=machine.Pin.IN, pull=machine.Pin.PULL_UP)

    def _read_channel(self, channel):
        cmd = 0x80 | (channel << 4) | 0x08
        self.cs.off()
        self.spi.write(bytearray([cmd, 0x00]))
        raw = self.spi.read(2)
        self.cs.on()
        value = (raw[0] << 8 | raw[1]) >> 4
        return value

    def read(self):
        if self.irq and self.irq.value() == 1:
            return None
        x_raw = self._read_channel(1)
        y_raw = self._read_channel(5)
        z1 = self._read_channel(3)
        z2 = self._read_channel(4)
        pressure = (z2 - z1) * x_raw // 4095
        if pressure < 0:
            pressure = 0
        if pressure > 4000:
            pressure = 4000
        if pressure < 20:
            return None
        x = x_raw * self.width // 4095
        y = y_raw * self.height // 4095
        x = max(0, min(self.width - 1, x))
        y = max(0, min(self.height - 1, y))
        if self._calibration:
            x = (x - self._calibration["x_off"]) * self._calibration["x_scale"]
            y = (y - self._calibration["y_off"]) * self._calibration["y_scale"]
        if self.rotation == 1:
            x, y = self.height - y, x
        elif self.rotation == 2:
            x, y = self.width - x, self.height - y
        elif self.rotation == 3:
            x, y = y, self.width - x
        return int(x), int(y), pressure

    def calibrate(self, cal_data):
        self._calibration = cal_data

    def is_pressed(self):
        pt = self.read()
        return pt is not None
