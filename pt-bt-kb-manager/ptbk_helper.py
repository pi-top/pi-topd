from dbus import Interface, SystemBus, Dictionary
from dbus.mainloop.glib import DBusGMainLoop
from subprocess import getoutput

SERVICE_NAME = "org.bluez"
ADAPTER_INTERFACE = SERVICE_NAME + ".Adapter1"
DEVICE_INTERFACE = SERVICE_NAME + ".Device1"

DBusGMainLoop(set_as_default=True)
bus = SystemBus()


def mac_addr_int_to_str(mac_addr_int: int):
    bt_addr_hex = "{:012x}".format(mac_addr_int)
    return ":".join(
        bt_addr_hex[i: i + 2] for i in range(0, len(bt_addr_hex), 2)
    ).lower()


def get_current_bt_interface_address():
    cmd = "hciconfig"
    device_id = "hci0"
    bt_mac = (
        getoutput(cmd)
        .split("{}:".format(device_id))[1]
        .split("BD Address: ")[1]
        .split(" ")[0]
        .strip()
    )
    return bt_mac.lower()


class BluezException(Exception):
    pass


class BluezNoAdapterException(BluezException):
    pass


class BluezNoDeviceException(BluezException):
    pass


class AdapterHelper:
    @staticmethod
    def get_list():
        adapter_path = BluezUtils.find_adapter().object_path

        om = Interface(
            bus.get_object(
                SERVICE_NAME, "/"), "org.freedesktop.DBus.ObjectManager"
        )
        objects = om.GetManagedObjects()

        parsed_objects = list()

        for obj_path, interfaces in objects.items():
            if DEVICE_INTERFACE not in interfaces:
                continue
            properties = interfaces[DEVICE_INTERFACE]
            if properties["Adapter"] != adapter_path:
                continue
            parsed_objects.append(properties)

        return parsed_objects


class BluezUtils:
    @staticmethod
    def get_managed_objects():
        manager = Interface(
            bus.get_object(
                SERVICE_NAME, "/"), "org.freedesktop.DBus.ObjectManager"
        )
        return manager.GetManagedObjects()

    @staticmethod
    def find_adapter(pattern=None):
        return BluezUtils.find_adapter_in_objects(
            BluezUtils.get_managed_objects(), pattern
        )

    @staticmethod
    def find_adapter_in_objects(objects, pattern=None):
        for path, ifaces in objects.items():
            adapter = ifaces.get(ADAPTER_INTERFACE)
            if adapter is None:
                continue
            if not pattern or pattern == adapter["Address"] or path.endswith(pattern):
                obj = bus.get_object(SERVICE_NAME, path)
                return Interface(obj, ADAPTER_INTERFACE)
        raise BluezNoAdapterException("Bluez: No adapter found")

    @staticmethod
    def find_device(device_address, adapter_pattern=None):
        return BluezUtils.find_device_in_objects(
            BluezUtils.get_managed_objects(), device_address, adapter_pattern
        )

    @staticmethod
    def find_device_in_objects(objects, device_address, adapter_pattern=None):
        path_prefix = ""
        if adapter_pattern:
            adapter = BluezUtils.find_adapter_in_objects(
                objects, adapter_pattern)
            path_prefix = adapter.object_path
        for path, ifaces in objects.items():
            device = ifaces.get(DEVICE_INTERFACE)
            if device is None:
                continue
            if device["Address"] is None:
                continue
            if device["Address"].lower() == device_address.lower() and path.startswith(path_prefix):
                obj = bus.get_object(SERVICE_NAME, path)
                return Interface(obj, DEVICE_INTERFACE)

        raise BluezNoDeviceException(
            "Bluez: No device found matching %s", device_address
        )


class DeviceHelper:
    @staticmethod
    def _get_path_from_device(device):
        return device.object_path

    @staticmethod
    def _get_props_from_path(device_path):
        return Interface(
            bus.get_object(
                SERVICE_NAME, device_path), "org.freedesktop.DBus.Properties"
        )

    @staticmethod
    def get_device(mac_address):
        return BluezUtils.find_device(mac_address)

    @staticmethod
    def get_device_path(mac_address):
        return DeviceHelper._get_path_from_device(DeviceHelper.get_device(mac_address))

    @staticmethod
    def get_device_props(mac_address):
        return DeviceHelper._get_props_from_path(
            DeviceHelper.get_device_path(mac_address)
        )
