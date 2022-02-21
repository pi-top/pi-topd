from enum import Enum, auto
from typing import Dict, List


class AppEvents(Enum):
    SPI_BUS_CHANGED = auto()  # bool - set to use SPI 0


subscribers: Dict[AppEvents, List] = dict()


def subscribe(event_type: AppEvents, fn):
    if event_type not in subscribers:
        subscribers[event_type] = []
    subscribers[event_type].append(fn)


def post_event(event_type: AppEvents, data=None):
    if event_type not in subscribers:
        return
    for fn in subscribers[event_type]:
        fn(data)
