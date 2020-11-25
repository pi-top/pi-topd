from pitopcommon.file_ops import touch_file
from pitopcommon.current_session_info import get_user_using_first_display
from pitopcommon.sys_config import System
from pitopcommon.common_ids import DeviceID, Peripheral, PeripheralID
from pitopcommon.sys_config import I2C, I2S, Hifiberry
from pitopcommon.logger import PTLogger
from importlib import import_module
from os import path
from subprocess import call
from threading import Thread
from time import sleep

# Discovers which peripheral libraries are installed, and uses those to
# detect, initialise, and communicate with the corresponding peripheral


class PeripheralManager:
    _loop_delay_seconds = 3
    _i2s_config_file_path = "/etc/pi-top/.i2s-vol/hifiberry-alsactl.restore"
    _i2s_configured_file_path = "/etc/pi-top/.i2s-vol/configured"

    def __init__(self):
        self._callback_client = None

        self._run_main_thread = False
        self._main_thread = Thread(target=self._main_thread_loop)

        self._enabled_peripherals = list()
        self._custom_imported_modules = {}
        self._host_device_id = DeviceID.unknown

    def initialise(self, callback_client):
        self._callback_client = callback_client

        PTLogger.debug("Initialising peripheral manager...")
        # Dynamically add the required python modules, if they are installed
        self.add_module_if_available("ptspeaker")
        self.add_module_if_available("ptpulse")

        self.configure_hifiberry()

    def initialise_device_id(self, device_id):
        self._host_device_id = device_id

    def emit_enable_hdmi_to_i2s_audio(self):
        if self._callback_client is not None:
            self._callback_client.on_enable_hdmi_to_i2s_audio()

    def emit_disable_hdmi_to_i2s_audio(self):
        if self._callback_client is not None:
            self._callback_client.on_disable_hdmi_to_i2s_audio()

    def emit_peripheral_connected(self, peripheral_id):
        if self._callback_client is not None:
            self._callback_client.on_peripheral_connected(peripheral_id.value)

    def emit_peripheral_disconnected(self, peripheral_id):
        if self._callback_client is not None:
            self._callback_client.on_peripheral_disconnected(
                peripheral_id.value)

    def emit_unsupported_hardware_message(self):
        if self._callback_client is not None:
            self._callback_client.on_unsupported_hardware()

    def emit_reboot_message(self):
        if self._callback_client is not None:
            self._callback_client.on_reboot_required()

    def start(self):
        if not self.is_initialised():
            PTLogger.error(
                "Unable to start pi-top peripheral management - run initialise() first!"
            )
            return False

        self._run_main_thread = True
        self._main_thread.start()
        return True

    def stop(self):
        PTLogger.info("Stopping peripheral manager...")
        self._run_main_thread = False
        if self._main_thread.is_alive():
            self._main_thread.join()

    def is_initialised(self):
        return self._callback_client is not None

    def _main_thread_loop(self):
        while self._run_main_thread:
            self.auto_initialise_peripherals()
            sleep(self._loop_delay_seconds)

    def add_module_if_available(self, module_name):
        cfg_module_str = str(module_name + ".configuration")
        try:
            i = import_module(cfg_module_str)
            self._custom_imported_modules[module_name] = i

        except ImportError as exc:
            PTLogger.warning(
                "Error: failed to import "
                + cfg_module_str
                + " settings module ("
                + str(exc)
                + ")"
            )

    def add_enabled_peripheral(self, peripheral):
        PTLogger.info("Adding enabled peripheral: " + peripheral.name)

        self._enabled_peripherals.append(peripheral)
        self.emit_peripheral_connected(peripheral.id)

    def remove_enabled_peripheral(self, peripheral):
        PTLogger.debug(
            "Removing peripheral from enabled peripherals: " + peripheral.name
        )

        self._enabled_peripherals.remove(peripheral)
        self.emit_peripheral_disconnected(peripheral.id)

    def enable_v1_hub_v1_speaker(self, peripheral):
        ptspeaker_cfg = self._custom_imported_modules["ptspeaker"]
        ptspeaker_cfg.initialise(self._host_device_id, peripheral.name)

        enabled, reboot_required, v2_hub_hdmi_to_i2s_required = (
            ptspeaker_cfg.enable_device()
        )

        if enabled or reboot_required:
            # Mark as enabled even if a reboot is required
            # to prevent subsequent attempts to enable
            self.add_enabled_peripheral(peripheral)

        if reboot_required:
            self.emit_reboot_message()

    def enable_v1_hub_v2_speaker(self, peripheral):
        ptspeaker_cfg = self._custom_imported_modules["ptspeaker"]
        ptspeaker_cfg.initialise(self._host_device_id, peripheral.name)

        enabled, reboot_required, v2_hub_hdmi_to_i2s_required = (
            ptspeaker_cfg.enable_device()
        )

        if enabled or reboot_required:
            # Mark as enabled even if a reboot is required
            # to prevent subsequent attempts to enable
            self.add_enabled_peripheral(peripheral)

        if reboot_required:
            self.emit_reboot_message()

    def configure_not_v2_hub_pulse(self, peripheral, enable):
        ptpulse_cfg = self._custom_imported_modules["ptpulse"]
        ptpulse_cfg.initialise(self._host_device_id, peripheral.name)

        enabled, reboot_required, v2_hub_hdmi_to_i2s_required = (
            ptpulse_cfg.enable_device()
        )

        if enabled or reboot_required:
            # Mark as enabled even if a reboot is required
            # to prevent subsequent attempts to enable
            self.add_enabled_peripheral(peripheral)

        if reboot_required is True:
            self.emit_reboot_message()

    def enable_v2_hub_v2_speaker(self, peripheral):
        ptspeaker_cfg = self._custom_imported_modules["ptspeaker"]
        ptspeaker_cfg.initialise(self._host_device_id, peripheral.name)

        enabled, reboot_required, v2_hub_hdmi_to_i2s_required = (
            ptspeaker_cfg.enable_device()
        )

        if enabled is True or reboot_required is True:
            # Mark as enabled even if a reboot is required
            # to prevent subsequent attempts to enable
            self.add_enabled_peripheral(peripheral)

        if enabled is True:
            if v2_hub_hdmi_to_i2s_required is True:
                self.emit_enable_hdmi_to_i2s_audio()
            else:
                self.emit_disable_hdmi_to_i2s_audio()

        if reboot_required is True:
            self.emit_reboot_message()

    def configure_v2_hub_pulse(self, peripheral, enable):
        ptpulse_cfg = self._custom_imported_modules["ptpulse"]
        ptpulse_cfg.initialise(self._host_device_id, peripheral.name)

        enabled, reboot_required, v2_hub_hdmi_to_i2s_required = (
            ptpulse_cfg.enable_device()
        )

        if enabled is True or reboot_required is True:
            # Mark as enabled even if a reboot is required
            # to prevent subsequent attempts to enable
            self.add_enabled_peripheral(peripheral)

        if enabled is True:
            if v2_hub_hdmi_to_i2s_required is True:
                self.emit_enable_hdmi_to_i2s_audio()
            else:
                self.emit_disable_hdmi_to_i2s_audio()

        if reboot_required is True:
            self.emit_reboot_message()

    def update_peripheral_state(self, peripheral, enable):
        if enable:
            PTLogger.info("Enabling peripheral: " + peripheral.name)

        else:
            PTLogger.info("Disabling peripheral: " + peripheral.name)

        peripheral_enabled = self.get_peripheral_enabled(peripheral)
        valid = enable != peripheral_enabled

        if valid:
            if "pi-topPULSE" in peripheral.name:
                if "ptpulse" in self._custom_imported_modules:
                    if self._host_device_id == DeviceID.pi_top_3:
                        self.configure_v2_hub_pulse(peripheral, enable)
                    else:
                        self.configure_not_v2_hub_pulse(peripheral, enable)
                else:
                    self.show_pulse_install_package_message()
                    PTLogger.info(
                        "pi-topPULSE initialisation not available - "
                        "please install 'python3-pt-pulse' package via apt-get"
                    )
            elif "pi-topSPEAKER" in peripheral.name:
                if "ptspeaker" in self._custom_imported_modules:
                    is_v1_hub = (self._host_device_id == DeviceID.pi_top) or (
                        self._host_device_id == DeviceID.pi_top_ceed
                    )

                    if self._host_device_id == DeviceID.pi_top_4:
                        # TODO: v3 speaker init code - or just use in-built speaker?
                        pass
                    elif self._host_device_id == DeviceID.pi_top_3:
                        # CHECK THAT SPEAKER IS V2
                        if peripheral.name == "pi-topSPEAKER-v2":
                            self.enable_v2_hub_v2_speaker(peripheral)
                        else:
                            PTLogger.warning(
                                "Unable to initialise V1 speaker with V2 hardware"
                            )
                            # Mark as enabled even if a reboot is required
                            # to prevent subsequent attempts to enable
                            self.add_enabled_peripheral(peripheral)
                            self.emit_unsupported_hardware_message()
                    elif is_v1_hub or self._host_device_id == DeviceID.unknown:
                        if enable is True:
                            if peripheral.name == "pi-topSPEAKER-v2":
                                self.enable_v1_hub_v2_speaker(peripheral)
                            else:
                                self.enable_v1_hub_v1_speaker(peripheral)
                        else:
                            self.remove_enabled_peripheral(peripheral)
                    else:
                        PTLogger.error("Not a valid configuration")
                else:
                    PTLogger.info(
                        "pi-topSPEAKER initialisation not available - "
                        "please install 'python3-pt-speaker' package via apt-get"
                    )
            elif "pi-topPROTO+" in peripheral.name:
                # Nothing to do - add to list of peripherals
                self.add_enabled_peripheral(peripheral)

            else:
                PTLogger.error("Peripheral name not recognised")
        else:
            PTLogger.debug("Peripheral state was already set")

    @staticmethod
    def get_connected_peripherals():
        addresses = I2C.get_connected_device_addresses()

        detected_peripherals = list()

        for address in addresses:
            current_peripheral = Peripheral(addr=int(address, 16))
            if current_peripheral.id != PeripheralID.unknown:
                detected_peripherals.append(current_peripheral)

        return detected_peripherals

    @staticmethod
    def get_connected_peripheral_names():
        detected_peripherals = PeripheralManager.get_connected_peripherals()

        detected_peripheral_names = list()

        for detected_peripheral in detected_peripherals:
            detected_peripheral_names.append(detected_peripheral.name)

        return detected_peripheral_names

    ################################
    # EXPORTED FUNCTIONS           #
    ################################

    def attempt_disable_peripheral_by_name(self, current_peripheral_name):
        current_peripheral = Peripheral(name=current_peripheral_name)

        if current_peripheral.id == PeripheralID.unknown:
            PTLogger.warning(
                "Peripheral " + current_peripheral_name + " not recognised"
            )

        elif self.get_peripheral_enabled(current_peripheral):
            PTLogger.debug("updating peripheral state")
            self.update_peripheral_state(current_peripheral, False)

        else:
            PTLogger.warning(
                "Peripheral " + current_peripheral_name + " already disabled"
            )

    def attempt_enable_peripheral_by_name(self, current_peripheral_name):
        current_peripheral = Peripheral(name=current_peripheral_name)

        if current_peripheral.id == PeripheralID.unknown:
            PTLogger.error(
                "Attempted to enable peripheral "
                + current_peripheral_name
                + ", but it was not recognised"
            )

        elif not self.get_peripheral_enabled(current_peripheral):
            PTLogger.debug(
                "Peripheral " + current_peripheral_name + " not already enabled"
            )

            for enabled_peripheral in self._enabled_peripherals:
                if (
                    enabled_peripheral.id != current_peripheral.id
                    and current_peripheral.id not in enabled_peripheral.compatible_ids
                ):
                    PTLogger.debug("Not compatible with " +
                                   enabled_peripheral.name)
                    return

            self.update_peripheral_state(current_peripheral, True)

        else:
            PTLogger.debug("Peripheral " +
                           current_peripheral_name + " already enabled")

    def auto_initialise_peripherals(self):
        addresses = I2C.get_connected_device_addresses()

        for peripheral in self._enabled_peripherals:
            if format(peripheral.addr, "x") not in addresses:
                PTLogger.debug(
                    "Peripheral " + peripheral.name + " was enabled but not detected."
                )
                self.remove_enabled_peripheral(peripheral)
                self.attempt_disable_peripheral_by_name(peripheral.name)

        for address in addresses:
            current_peripheral = Peripheral(addr=int(address, 16))

            if current_peripheral.id != PeripheralID.unknown:
                self.attempt_enable_peripheral_by_name(current_peripheral.name)

    def configure_hifiberry(self):
        if I2S.get_current_state() is True:
            if path.isfile(self._i2s_configured_file_path) is False:
                call(("/usr/sbin/alsactl", "-f",
                      self._i2s_config_file_path, "restore"))
                touch_file(self._i2s_configured_file_path)
                System.reboot_system()
            else:
                Hifiberry.set_as_audio_output(
                    user=get_user_using_first_display())

    def get_peripheral_enabled(self, peripheral):
        return self.get_peripheral_id_enabled(peripheral.id)

    def get_peripheral_id_enabled(self, peripheral_id):
        if peripheral_id == -1:
            return False

        if isinstance(peripheral_id, int):
            for enabled_peripheral in self._enabled_peripherals:
                if peripheral_id == enabled_peripheral.id.value:
                    return True
        else:
            for enabled_peripheral in self._enabled_peripherals:
                if peripheral_id == enabled_peripheral.id:
                    return True

        return False
