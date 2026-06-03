import machine
import time


class SDCard:
    def __init__(self, spi, cs, baud=2000000):
        self.spi = spi
        self.cs = cs
        self.cs.init(mode=machine.Pin.OUT, value=1)
        self.spi.baudrate = baud
        self._init_card()

    def _wait_ready(self, timeout=300):
        for _ in range(timeout):
            if self._send_cmd(0x41, 0) == 0:
                return True
            time.sleep_ms(1)
        return False

    def _send_cmd(self, cmd, arg, crc=0):
        buf = bytearray([cmd | 0x40, arg >> 24, arg >> 16, arg >> 8, arg, crc | 1])
        self.cs.off()
        self.spi.write(buf)
        for _ in range(100):
            r = self.spi.read(1)[0]
            if r != 0xFF:
                break
        self.cs.on()
        return r

    def _init_card(self):
        self.cs.on()
        for _ in range(10):
            self.spi.write(b"\xFF")
        self.cs.off()
        self.spi.write(b"\xFF")
        self.cs.on()
        for _ in range(5):
            self._send_cmd(0x40, 0)
        for _ in range(100):
            if self._send_cmd(0x41, 0) == 0:
                break
            time.sleep_ms(1)
        self._send_cmd(0x50, 0x200)
        self.cs.off()
        self.spi.write(b"\xFF")
        self.cs.on()

    def read_sectors(self, sector, buf):
        self.cs.off()
        self._send_cmd(0x51, sector)
        for _ in range(100):
            if self.spi.read(1)[0] == 0xFE:
                break
        self.spi.readinto(buf)
        self.spi.read(2)
        self.cs.on()

    def write_sectors(self, sector, buf):
        self.cs.off()
        self._send_cmd(0x58, sector)
        self.spi.write(b"\xFF")
        self.spi.write(b"\xFE")
        self.spi.write(buf)
        self.spi.write(b"\xFF\xFF")
        self.spi.read(1)
        self.cs.on()
