import machine
import time
import gc

from config import CONFIG
from network_manager import NetworkManager
from ntp_time import TimeManager
from weather import WeatherManager
from photo_manager import PhotoManager
from todo_manager import TodoManager

gc.collect()


def init_display(cfg):
    disp_cfg = cfg["display"]
    if disp_cfg["type"] == "ILI9341":
        from drivers.ili9341 import ILI9341
        driver_cls = ILI9341
    elif disp_cfg["type"] == "ST7789":
        from drivers.st7789 import ST7789
        driver_cls = ST7789
    else:
        raise ValueError(f"Unknown display: {disp_cfg['type']}")

    spi = machine.SPI(
        disp_cfg.get("spi_id", 0),
        baudrate=disp_cfg.get("spi_baud", 40000000),
        polarity=0,
        phase=0,
        sck=machine.Pin(disp_cfg.get("pin_sck", 2)),
        mosi=machine.Pin(disp_cfg.get("pin_mosi", 3)),
        miso=machine.Pin(disp_cfg.get("pin_miso", 4)),
    )
    cs = machine.Pin(disp_cfg["pin_cs"], machine.Pin.OUT, value=1)
    dc = machine.Pin(disp_cfg["pin_dc"], machine.Pin.OUT, value=0)
    rst = machine.Pin(disp_cfg["pin_rst"], machine.Pin.OUT, value=1)

    display = driver_cls(
        spi=spi,
        cs=cs,
        dc=dc,
        rst=rst,
        width=disp_cfg["width"],
        height=disp_cfg["height"],
        rotation=disp_cfg.get("rotation", 0),
    )

    if disp_cfg.get("pin_bl"):
        bl = machine.Pin(disp_cfg["pin_bl"], machine.Pin.OUT, value=1)

    return display


def init_touch(cfg, display):
    touch_cfg = cfg.get("touch", {})
    if not touch_cfg.get("enabled", False):
        return None
    if touch_cfg.get("type") == "XPT2046":
        from drivers.xpt2046 import XPT2046
        spi = machine.SPI(
            touch_cfg.get("spi_id", 1),
            baudrate=touch_cfg.get("spi_baud", 2000000),
            sck=machine.Pin(touch_cfg.get("pin_sck", 10)),
            mosi=machine.Pin(touch_cfg.get("pin_mosi", 11)),
            miso=machine.Pin(touch_cfg.get("pin_miso", 12)),
        )
        cs = machine.Pin(touch_cfg["pin_cs"], machine.Pin.OUT, value=1)
        irq = machine.Pin(touch_cfg["pin_irq"], machine.Pin.IN,
                          machine.Pin.PULL_UP) if "pin_irq" in touch_cfg else None
        touch = XPT2046(
            spi=spi,
            cs=cs,
            irq=irq,
            width=cfg["display"]["width"],
            height=cfg["display"]["height"],
        )
        return touch
    return None


def init_sd(cfg):
    sd_cfg = cfg.get("sd_card", {})
    if not sd_cfg.get("enabled", False):
        return False
    try:
        from drivers.sdcard import SDCard
        spi = machine.SPI(
            sd_cfg.get("spi_id", 1),
            baudrate=sd_cfg.get("spi_baud", 2000000),
            sck=machine.Pin(sd_cfg.get("pin_sck", 10)),
            mosi=machine.Pin(sd_cfg.get("pin_mosi", 11)),
            miso=machine.Pin(sd_cfg.get("pin_miso", 12)),
        )
        cs = machine.Pin(sd_cfg["pin_cs"], machine.Pin.OUT, value=1)
        sd = SDCard(spi=spi, cs=cs)
        import os
        try:
            os.mount(sd, "/sd")
            return True
        except:
            import uos
            uos.mount(sd, "/sd")
            return True
    except Exception:
        return False


def main():
    display = init_display(CONFIG)
    display.fill(0x0000)
    display.text("Smart Picture Frame", 20, 60, 0xFFFF)
    display.text("Loading...", 60, 100, 0x8410)

    wifi_ok = False
    net = NetworkManager(CONFIG)
    display.text("Connecting WiFi...", 30, 130, 0x8410)
    if net.connect():
        wifi_ok = True
        display.text("WiFi OK", 60, 150, 0x07E0)
    else:
        display.text("WiFi Offline", 60, 150, 0xF800)

    time_mgr = TimeManager(CONFIG)
    if wifi_ok:
        display.text("Syncing time...", 30, 170, 0x8410)
        time_mgr.sync()

    weather_mgr = WeatherManager(CONFIG, net)
    if wifi_ok:
        weather_mgr.fetch()

    sd_ok = init_sd(CONFIG)
    photo_mgr = PhotoManager(CONFIG)
    if sd_ok:
        photo_mgr.scan_sd_card()

    todo_mgr = TodoManager(CONFIG)

    from screens.clock_screen import ClockScreen
    from screens.weather_screen import WeatherScreen
    from screens.calendar_screen import CalendarScreen
    from screens.photo_screen import PhotoScreen
    from screens.dashboard_screen import DashboardScreen

    clock_screen = ClockScreen(display, CONFIG)
    weather_screen = WeatherScreen(display, CONFIG)
    calendar_screen = CalendarScreen(display, CONFIG)
    photo_screen = PhotoScreen(display, CONFIG)
    dashboard_screen = DashboardScreen(display, CONFIG)

    screens = {
        "clock": clock_screen,
        "weather": weather_screen,
        "calendar": calendar_screen,
        "photos": photo_screen,
        "dashboard": dashboard_screen,
    }

    touch = init_touch(CONFIG, display)

    screen_order = CONFIG["ui"].get("screens_order",
                                    ["dashboard", "clock", "weather",
                                     "calendar", "photos"])
    current_idx = 0
    auto_switch_interval = CONFIG["ui"].get("auto_screen_interval", 15)
    last_switch = time.time()

    while True:
        now = time.time()
        time_data = time_mgr.get_time()
        weather_data = weather_mgr.get_weather()
        todo_items = todo_mgr.get_pending()

        if wifi_ok:
            if time_mgr.need_sync():
                time_mgr.sync()
            if weather_mgr.need_update():
                weather_mgr.fetch()

        current_name = screen_order[current_idx]
        screen = screens[current_name]

        photo_file = None
        if current_name == "dashboard" or current_name == "photos":
            photo_file = photo_mgr.get_current()
            if photo_mgr.should_switch():
                photo_file = photo_mgr.next()

        screen.draw(
            time_data=time_data,
            weather_data=weather_data,
            todo_items=todo_items,
            photo_file=photo_file,
        )

        if touch:
            pt = touch.read()
            if pt:
                tx, ty, _ = pt
                result = screen.handle_touch(tx, ty)
                if result == "next":
                    current_idx = (current_idx + 1) % len(screen_order)
                    last_switch = now
                elif result == "prev":
                    current_idx = (current_idx - 1) % len(screen_order)
                    last_switch = now
                elif result == "next_photo":
                    photo_mgr.next()
                time.sleep_ms(200)

        if now - last_switch >= auto_switch_interval:
            current_idx = (current_idx + 1) % len(screen_order)
            last_switch = now

        gc.collect()
        time.sleep_ms(500)


try:
    main()
except Exception as e:
    import sys
    sys.print_exception(e)
