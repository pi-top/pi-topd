from ptcommon import common_ids
from ptcommon import common_functions
from ptcommon import sys_config
from importlib import import_module
from string import whitespace
from threading import Thread
from shutil import copy
from subprocess import check_output
from subprocess import Popen
from subprocess import call
from os import path
from os import remove
from os import remove
from os import utime
from time import sleep

# Discovers which peripheral libraries are installed, and uses those to
# detect, initialise, and communicate with the corresponding device


class PeripheralManager():
    _loop_delay_seconds = 1
    _i2s_config_file_path = "/etc/pi-top/.i2s-vol/hifiberry-alsactl.restore"
    _i2s_configured_file_path = "/etc/pi-top/.i2s-vol/configured"

    def __init__(self):
        self._logger = None
        self._callback_client = None
        self.sys_cfg_HDMI = sys_config.HDMI()
        self.sys_cfg_I2C = sys_config.I2C()
        self.sys_cfg_I2S = sys_config.I2S()
        self.sys_cfg_UART = sys_config.UART()

    def initialise(self, logger, callback_client):
        self._logger = logger
        self._callback_client = callback_client

        self._run_main_thread = False
        self._main_thread = Thread(target=self._main_thread_loop)

        self._enabled_devices = []
        self._known_devices = []
        self._custom_imported_modules = {}
        self._device_id = None

        self._logger.debug("Initialising peripheral manager...")
        # Dynamically add the required python modules, if they are installed
        self.add_module_if_available('ptspeaker')
        self.add_module_if_available('ptpulse')

        # Initialise the devices that we support
        self.initialise_known_device({'id': 0, 'compatible_ids': [None], 'name': 'pi-topPULSE', 'type': 'HAT', 'addr': 0x24})
        self.initialise_known_device({'id': 1, 'compatible_ids': [2, 3], 'name': 'pi-topSPEAKER-v1-Left', 'type': 'addon', 'addr': 0x71})
        self.initialise_known_device({'id': 2, 'compatible_ids': [1, 3], 'name': 'pi-topSPEAKER-v1-Mono', 'type': 'addon', 'addr': 0x73})
        self.initialise_known_device({'id': 3, 'compatible_ids': [1, 2], 'name': 'pi-topSPEAKER-v1-Right', 'type': 'addon', 'addr': 0x72})
        self.initialise_known_device({'id': 4, 'compatible_ids': [None], 'name': 'pi-topSPEAKER-v2', 'type': 'addon', 'addr': 0x43})

        self.configure_hifiberry_alsactl()

    def initialise_device_id(self, device_id):
        self._device_id = device_id

    def emit_enable_hdmi_to_i2s_audio(self):
        if (self._callback_client is not None):
            self._callback_client._on_enable_hdmi_to_i2s_audio()

    def emit_disable_hdmi_to_i2s_audio(self):
        if (self._callback_client is not None):
            self._callback_client._on_disable_hdmi_to_i2s_audio()

    def emit_peripheral_connected(self, device_id):
        if (self._callback_client is not None):
            self._callback_client._on_peripheral_connected(device_id)

    def emit_peripheral_disconnected(self, device_id):
        if (self._callback_client is not None):
            self._callback_client._on_peripheral_disconnected(device_id)

    def emit_reboot_message(self):
        if (self._callback_client is not None):
            self._callback_client._on_reboot_required()

    def start(self):
        if self._device_id is None or self._device_id == common_ids.DeviceID.not_yet_known:
            self._logger.error("Unable to start pi-top peripheral management - invalid device ID")
            return False

        if not self.is_initialised():
            self._logger.error("Unable to start pi-top peripheral management - run initialise() first!")
            return False

        self._run_main_thread = True
        self._main_thread.start()
        return True

    def stop(self):
        self._logger.info("Stopping peripheral manager...")
        self._run_main_thread = False
        if self._main_thread.is_alive():
            self._main_thread.join()

    def is_initialised(self):
        return (self._main_thread is not None)

    def _main_thread_loop(self):
        while self._run_main_thread:
            self.auto_initialise_peripherals()
            sleep(self._loop_delay_seconds)

    def add_module_if_available(self, module_name):
        cfg_module_str = str(module_name + ".configuration")
        try:

            i = import_module(cfg_module_str)
            self._custom_imported_modules[module_name] = i

        except ImportError:
            self._logger.info("Could not import " + cfg_module_str)

    def add_known_device(self, device):
        self._known_devices.append(device)

    def add_enabled_device(self, device):
        self._logger.debug("Adding enabled device: " + device['name'])

        self._enabled_devices.append(device)
        self.emit_peripheral_connected(device['id'])

    def remove_enabled_device(self, device):
        self._logger.debug("Removing device from enabled devices: " + device['name'])

        self._enabled_devices.remove(device)
        self.emit_peripheral_disconnected(device['id'])

    def initialise_known_device(self, device):
        self.add_known_device(device)

    def get_device_by_id(self, device_id):
        for device in self._known_devices:
            if device['id'] == device_id:
                return device

        return None

    def get_device_by_address(self, addr):
        for device in self._known_devices:
            if device['addr'] == int(addr, 16):
                return device

        return None

    def get_device_by_name(self, name):
        for device in self._known_devices:
            if device['name'] == name:
                return device
        return None

    def enable_v1_hub_v1_speaker(self, device):
        ptspeaker_cfg = self._custom_imported_modules['ptspeaker']
        ptspeaker_cfg.initialise(self._device_id, device['name'], self._logger)

        enabled, reboot_required, v2_hub_hdmi_to_i2s_required = ptspeaker_cfg.enable_device()

        if enabled or reboot_required:
            # Mark as enabled even if a reboot is required
            # to prevent subsequent attempts to enable
            self.add_enabled_device(device)

        if reboot_required:
            self.emit_reboot_message()

    def enable_v1_hub_v2_speaker(self, device):
        ptspeaker_cfg = self._custom_imported_modules['ptspeaker']
        ptspeaker_cfg.initialise(self._device_id, device['name'], self._logger)

        enabled, reboot_required, v2_hub_hdmi_to_i2s_required = ptspeaker_cfg.enable_device()

        if enabled or reboot_required:
            # Mark as enabled even if a reboot is required
            # to prevent subsequent attempts to enable
            self.add_enabled_device(device)

        if reboot_required:
            self.emit_reboot_message()

    def configure_v1_hub_pulse(self, device, enable):
        ptpulse_cfg = self._custom_imported_modules['ptpulse']
        ptpulse_cfg.initialise(self._device_id, device['name'], self._logger)

        enabled, reboot_required, v2_hub_hdmi_to_i2s_required = ptpulse_cfg.enable_device()

        if enabled or reboot_required:
            # Mark as enabled even if a reboot is required
            # to prevent subsequent attempts to enable
            self.add_enabled_device(device)

        if (reboot_required is True):
            self.emit_reboot_message()

    def enable_v2_hub_v2_speaker(self, device):
        ptspeaker_cfg = self._custom_imported_modules['ptspeaker']
        ptspeaker_cfg.initialise(self._device_id, device['name'], self._logger)

        enabled, reboot_required, v2_hub_hdmi_to_i2s_required = ptspeaker_cfg.enable_device()

        if (enabled is True or reboot_required is True):
            # Mark as enabled even if a reboot is required
            # to prevent subsequent attempts to enable
            self.add_enabled_device(device)

        if (enabled is True):
            if (v2_hub_hdmi_to_i2s_required is True):
                self.emit_enable_hdmi_to_i2s_audio()
            else:
                self.emit_disable_hdmi_to_i2s_audio()

        if (reboot_required is True):
            self.emit_reboot_message()

    def configure_v2_hub_pulse(self, device, enable):
        ptpulse_cfg = self._custom_imported_modules['ptpulse']
        ptpulse_cfg.initialise(self._device_id, device['name'], self._logger)

        enabled, reboot_required, v2_hub_hdmi_to_i2s_required = ptpulse_cfg.enable_device()

        if (enabled is True or reboot_required is True):
            # Mark as enabled even if a reboot is required
            # to prevent subsequent attempts to enable
            self.add_enabled_device(device)

        if (enabled is True):
            if (v2_hub_hdmi_to_i2s_required is True):
                self.emit_enable_hdmi_to_i2s_audio()
            else:
                self.emit_disable_hdmi_to_i2s_audio()

        if (reboot_required is True):
            self.emit_reboot_message()

    def show_speaker_install_package_message(self):
        self._logger.info("pi-topSPEAKER initialisation not available - please install 'python3-pt-speaker' package via apt-get")

    def show_pulse_install_package_message(self):
        self._logger.info("pi-topPULSE initialisation not available - please install 'python3-pt-pulse' package via apt-get")

    def update_device_state(self, device, enable):
        if enable:
            self._logger.info("Enabling device: " + device['name'])

        else:
            self._logger.info("Disabling device: " + device['name'])

        device_enabled = (device in self._enabled_devices)
        valid = (enable != device_enabled)

        if valid:
            if 'pi-topPULSE' in device['name']:
                if 'ptpulse' in self._custom_imported_modules:
                    is_v1_hub = (self._device_id == common_ids.DeviceID.pi_top) or (self._device_id == common_ids.DeviceID.pi_top_ceed)

                    if self._device_id == common_ids.DeviceID.pi_top_v2:
                        self.configure_v2_hub_pulse(device, enable)
                    elif is_v1_hub or self._device_id == common_ids.DeviceID.unknown:
                        self.configure_v1_hub_pulse(device, enable)
                    else:
                        print("NOT A VALID CONFIGURATION")
                else:
                    self.show_pulse_install_package_message()
            elif 'pi-topSPEAKER' in device['name']:
                if 'ptspeaker' in self._custom_imported_modules:
                    is_v1_hub = (self._device_id == common_ids.DeviceID.pi_top) or (self._device_id == common_ids.DeviceID.pi_top_ceed)

                    if self._device_id == common_ids.DeviceID.pi_top_v2:
                        # CHECK THAT SPEAKER IS V2
                        if device['name'] == 'pi-topSPEAKER-v2':
                            self.enable_v2_hub_v2_speaker(device)
                        else:
                            print("Unable to initialise V1 speaker with V2 hardware")
                    elif is_v1_hub or self._device_id == common_ids.DeviceID.unknown:
                        if enable is True:
                            if device['name'] == 'pi-topSPEAKER-v2':
                                self.enable_v1_hub_v2_speaker(device)
                            else:
                                self.enable_v1_hub_v1_speaker(device)
                        else:
                            self.remove_enabled_device(device)
                    else:
                        print("NOT A VALID CONFIGURATION")
                else:
                    self.show_speaker_install_package_message()
            else:
                self._logger.error("Device name not recognised")
        else:
            self._logger.debug("Device state was already set")

    def get_connected_devices(self):
        addresses = self.sys_cfg_I2C.get_connected_device_addresses()

        detected_devices = []

        for address in addresses:
            current_device = self.get_device_by_address(address)
            if current_device is not None:
                detected_devices.append(current_device)

        return detected_devices

    def get_connected_device_names(self):
        detected_devices = self.get_connected_devices()

        detected_device_names = []

        for detected_device in detected_devices:
            detected_device_names.append(detected_device['name'])

        return detected_device_names

    ################################
    # EXPORTED FUNCTIONS           #
    ################################

    def attempt_disable_device_by_name(self, current_device_name):
        current_device = self.get_device_by_name(current_device_name)

        if current_device is None:
            self._logger.warning("Device " + current_device_name + " not recognised")

        elif current_device in self._enabled_devices:
            self._logger.debug("updating device state")
            self.update_device_state(current_device, False)

        else:
            self._logger.warning("Device " + current_device_name + " already disabled")

    def attempt_enable_device_by_name(self, current_device_name):
        current_device = self.get_device_by_name(current_device_name)

        if current_device is None:
            self._logger.error("Attempted to enable device " + current_device_name + ", but it was not recognised")

        elif current_device not in self._enabled_devices:

            for enabled_device in self._enabled_devices:

                if current_device['id'] not in enabled_device['compatible_ids']:
                    return

            self.update_device_state(current_device, True)

        else:
            self._logger.debug("Device " + current_device_name + " already enabled")

    def auto_initialise_peripherals(self):
        addresses = self.sys_cfg_I2C.get_connected_device_addresses()

        for device in self._enabled_devices:

            if format(device['addr'], 'x') not in addresses:
                self._logger.debug("Device " + device['name'] + " was enabled but not detected.")
                self.remove_enabled_device(device)
                self.attempt_disable_device_by_name(device['name'])

        for address in addresses:
            current_device = self.get_device_by_address(address)

            if current_device is not None:
                self.attempt_enable_device_by_name(current_device['name'])

    def configure_hifiberry_alsactl(self):
        if self.sys_cfg_I2S.get_current_state() is True and path.isfile(self._i2s_configured_file_path) is False:
            call(("/usr/sbin/alsactl", "-f", self._i2s_config_file_path, "restore"))
            common_functions.touch_file(self._i2s_configured_file_path)
            common_functions.reboot_system()

    def get_peripheral_enabled(self, peripheral_id):
        device = self.get_device_by_id(peripheral_id)
        if (device is not None):
            if (device in self._enabled_devices):
                return True

        return False
