# 讓 components 成為一個 Python package
from . import clock
from . import time
from . import weather
from . import photo

__all__ = ["clock", "time", "weather", "photo"]
