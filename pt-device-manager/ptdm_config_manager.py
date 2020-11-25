from pitopcommon.logger import PTLogger
from pitopcommon.common_ids import DeviceID


class ConfigManager:
    def get_last_identified_device_id(self):
        try:
            with open("/etc/pi-top/pt-device-manager/device_version", "r") as f:
                line = f.readline().strip()
                return DeviceID[line]
        except (IOError, KeyError):
            PTLogger.warning("Failed to read device version file.")

        return DeviceID.unknown

    def write_device_id_to_file(self, device_id):
        try:
            with open("/etc/pi-top/pt-device-manager/device_version", "w") as f:
                f.write(str(device_id.name) + "\n")
        except IOError:
            PTLogger.warning("Failed to write to device version file")
