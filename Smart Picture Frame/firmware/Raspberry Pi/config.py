CONFIG = {
    "wifi": {
        "ssid": "YOUR_WIFI_SSID",
        "password": "YOUR_WIFI_PASSWORD",
        "country": "TW",
        "connect_timeout": 30,
    },

    "display": {
        "type": "ILI9341",
        "width": 320,
        "height": 240,
        "rotation": 0,
        "spi_id": 0,
        "spi_baud": 40000000,
        "pin_cs": 9,
        "pin_dc": 8,
        "pin_rst": 10,
        "pin_bl": 11,
    },

    "touch": {
        "enabled": True,
        "type": "XPT2046",
        "spi_id": 0,
        "spi_baud": 2000000,
        "pin_cs": 13,
        "pin_irq": 14,
    },

    "sd_card": {
        "enabled": True,
        "spi_id": 0,
        "spi_baud": 2000000,
        "pin_cs": 12,
    },

    "ntp": {
        "server": "pool.ntp.org",
        "timezone": 8,
        "update_interval": 3600,
    },

    "weather": {
        "api_key": "YOUR_OPENWEATHERMAP_API_KEY",
        "city": "Taipei",
        "units": "metric",
        "lang": "zh_tw",
        "update_interval": 1800,
    },

    "photos": {
        "slideshow_interval": 10,
        "source": "sd_card",
        "online_urls": [],
        "convert_tool": "tools/img_convert.py",
    },

    "todo": {
        "file_path": "/sd/todo.json",
        "max_items": 20,
    },

    "ui": {
        "auto_screen_interval": 15,
        "screens_order": ["dashboard", "clock", "weather", "calendar", "photos"],
        "color_bg": 0x0000,
        "color_primary": 0x001F,
        "color_secondary": 0x07E0,
        "color_accent": 0xF800,
        "color_text": 0xFFFF,
        "color_text_dim": 0x8410,
    },
}
