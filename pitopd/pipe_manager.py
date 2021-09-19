from enum import Enum
from pathlib import Path

from pitop.common.logger import PTLogger


class Pipes(Enum):
    device_type = "/run/pt_device_type"
    hub_serial = "/run/pt_hub_serial"
    battery_serial = "/run/pt_battery_serial"
    display_serial = "/run/pt_display_serial"


def write_to_file(self, pipe_path, text):
    try:
        with open(pipe_path, "w") as f:
            f.write(str(text) + "\n")
    except IOError:
        PTLogger.warning("Failed to write to device type file")


class PipeManager:
    def __init__(self):
        for pipe in Pipes:
            path = Path(pipe.value)

            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                path.touch()

    # TODO: loop over writing to FIFO, ready for clients to read
    def set_device_id(self, device_id):
        try:
            write_to_file(Pipes.device_type.value, device_id.name)
        except IOError:
            PTLogger.warning("Failed to write to device type file")

    def set_hub_serial_number(self, serial):
        try:
            write_to_file(Pipes.hub_serial.value, serial)
        except IOError:
            PTLogger.warning("Failed to write to device type file")

    def set_battery_serial_number(self, serial):
        try:
            write_to_file(Pipes.battery_serial.value, serial)
        except IOError:
            PTLogger.warning("Failed to write to device type file")

    def set_display_serial_number(self, serial):
        try:
            write_to_file(Pipes.display_serial.value, serial)
        except IOError:
            PTLogger.warning("Failed to write to device type file")
