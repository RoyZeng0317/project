import os
import sys
from PIL import Image


def convert_image(input_path, output_path=None, width=320, height=240):
    if output_path is None:
        base, _ = os.path.splitext(input_path)
        output_path = f"{base}.rgb565"

    img = Image.open(input_path).convert("RGB")
    img = img.resize((width, height), Image.LANCZOS)

    pixels = list(img.getdata())
    rgb565 = bytearray()
    for r, g, b in pixels:
        r5 = (r >> 3) & 0x1F
        g6 = (g >> 2) & 0x3F
        b5 = (b >> 3) & 0x1F
        val = (r5 << 11) | (g6 << 5) | b5
        rgb565.append(val >> 8)
        rgb565.append(val & 0xFF)

    with open(output_path, "wb") as f:
        f.write(rgb565)

    print(f"轉換完成: {output_path} ({width}x{height})")
    return output_path


def convert_batch(input_dir, output_dir=None, width=320, height=240):
    if output_dir is None:
        output_dir = input_dir
    os.makedirs(output_dir, exist_ok=True)

    for fn in os.listdir(input_dir):
        if fn.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
            input_path = os.path.join(input_dir, fn)
            base, _ = os.path.splitext(fn)
            output_path = os.path.join(output_dir, f"{base}.rgb565")
            convert_image(input_path, output_path, width, height)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python tools/img_convert.py <圖片檔案>                  # 單張轉換")
        print("  python tools/img_convert.py <圖片目錄> --batch         # 批次轉換")
        print("  python tools/img_convert.py <檔案> --width 480 --height 320  # 自訂尺寸")
        sys.exit(1)

    path = sys.argv[1]
    width = int(sys.argv[sys.argv.index("--width") + 1]) if "--width" in sys.argv else 320
    height = int(sys.argv[sys.argv.index("--height") + 1]) if "--height" in sys.argv else 240

    if len(sys.argv) > 2 and "--batch" in sys.argv:
        convert_batch(path, width=width, height=height)
    elif os.path.isdir(path):
        convert_batch(path, width=width, height=height)
    else:
        convert_image(path, width=width, height=height)
