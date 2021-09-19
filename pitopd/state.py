from configparser import ConfigParser
from pathlib import Path
from threading import Lock

STATE_FILE_PATH = "/var/lib/pi-topd/state.cfg"
config_parser = ConfigParser()

path = Path(STATE_FILE_PATH)
lock = Lock()

if not path.exists():
    path.mkdir(parents=True, exist_ok=True)
    path.touch()

config_parser.read(STATE_FILE_PATH)


def get(section: str, key: str, fallback=None):
    with lock:
        val = fallback
        try:
            val = config_parser.get(section, key)
        except Exception:
            if fallback is None:
                raise
        finally:
            return val


def set(section: str, key: str, value):
    with lock:
        try:
            if not config_parser.has_section(section):
                config_parser.add_section(section)
            config_parser.set(section, key, value)
        except Exception:
            raise
        __save()


def __save():
    with open(STATE_FILE_PATH, "w") as f:
        config_parser.write(f)
