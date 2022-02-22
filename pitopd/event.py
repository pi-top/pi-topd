from enum import Enum, auto

from pyee import EventEmitter

event_emitter = EventEmitter()


class AppEvents(Enum):
    SPI_BUS_CHANGED = auto()  # 0, 1: SPI bus in use
