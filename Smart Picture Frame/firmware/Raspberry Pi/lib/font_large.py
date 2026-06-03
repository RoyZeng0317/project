FONT16_WIDTH = 16
FONT16_MAP = []

for _ in range(95):
    row = b""
    for _ in range(16):
        row += b"\x00\x00"
    FONT16_MAP.append(row)

FONT16 = {
    "width": 16,
    "height": 16,
    "map": FONT16_MAP,
}
