from ptdm_client import ptdm_common
import traceback
from tempfile import mkstemp
from importlib import import_module
from string import whitespace
from threading import Thread
from subprocess import check_output
from subprocess import Popen
from subprocess import call
from os import path
from os import remove
from os import remove
from os import close
from os import utime
from time import sleep

# Discovers which peripheral libraries are installed, and uses those to
# detect, initialise, and communicate with the corresponding device


class PeripheralManager():
    _loop_delay_seconds = 1
    _boot_config_file_path = "/boot/config.txt"
    _i2s_config_file_path = "/etc/pi-top/.i2s-vol/hifiberry-alsactl.restore"
    _i2s_configured_file_path = "/etc/pi-top/.i2s-vol/configured"

    def __init__(self):
        self._logger = None
        self._callback_client = None

    def initialise(self, logger, callback_client):

        self._logger = logger
        self._callback_client = callback_client

        self._run_main_thread = False
        self._main_thread = Thread(target=self._main_thread_loop)

        self._enabled_devices = []
        self._known_devices = []
        self._custom_imported_modules = {}
        self._i2s_mode_current = False
        self._i2s_mode_next = False
        self._i2c_mode = False

        self._logger.debug("Initialising peripheral manager...")
        # Dynamically add the required python modules, if they are installed
        self.add_module_if_available('ptspeaker')
        self.add_module_if_available('ptpulse')

        # Initialise the devices that we support
        self.initialise_known_device({'id': 0, 'compatible_ids': [None], 'name': 'pi-topPULSE', 'type': 'HAT', 'addr': 0x24})
        self.initialise_known_device({'id': 1, 'compatible_ids': [2, 3], 'name': 'pi-topSPEAKER-Left', 'type': 'addon', 'addr': 0x71})
        self.initialise_known_device({'id': 2, 'compatible_ids': [1, 3], 'name': 'pi-topSPEAKER-Mono', 'type': 'addon', 'addr': 0x73})
        self.initialise_known_device({'id': 3, 'compatible_ids': [1, 2], 'name': 'pi-topSPEAKER-Right', 'type': 'addon', 'addr': 0x72})

        # Get the initial state of the system configuration
        self.determine_i2s_mode_from_system()
        self.determine_i2c_mode_from_system()

        self.configure_hifiberry_alsactl()

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
        if self.is_initialised():
            self._run_main_thread = True
            self._main_thread.start()
        else:
            self._logger.error("Unable to start pi-top peripheral management - run initialise() first!")

    def stop(self):
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

    def update_hat_device_state(self, device, enable):

        global enabled_device

        if 'pi-topPULSE' in device['name']:
            if 'ptpulse' in self._custom_imported_modules:
                ptpulse_cfg = self._custom_imported_modules['ptpulse']

                if self._i2s_mode_current is True:
                    self._logger.info("I2S is already enabled")

                    if enable:
                        self._logger.debug("Enabling " + device['name'])

                    else:
                        self._logger.debug("Disabling " + device['name'])

                    # Switch on I2C if it's not enabled
                    if self._i2c_mode is False:
                        self.enable_i2c(True)

                    if self._i2c_mode is False:
                        self._logger.error("Unable to initialise I2C - updating HAT device state")

                    else:
                        if ptpulse_cfg.reset_device_state(enable):
                            if enable:
                                self.add_enabled_device(device)

                            else:
                                self.remove_enabled_device(device)

                        else:
                            self._logger.error("Unable to verify state of " + str(device['name']))

                else:
                    if self._i2s_mode_next is False:
                        self._logger.debug(
                            "I2S appears to be disabled - enabling...")
                        self.enable_i2s(True)

                    # Add to enabled devices to prevent further scans
                    # attempting to initialise device
                    self.add_enabled_device(device)

                if self._baud_rate_correctly_configured() is True:
                    self._logger.debug(
                        "Baud rate is already configured for ptpulse")

                else:
                    self.set_serial_baud_rate_in_boot_config()

                self.remove_serial_from_cmdline()

                if (self._i2s_mode_current != self._i2s_mode_next):
                    self.emit_reboot_message()

            else:
                if sys.version_info >= (3, 0):
                    package = "python3-pt-pulse"

                else:
                    package = "python-pt-pulse"

                self._logger.info("pi-topPULSE initialisation not available - please install '" + package + "' package via apt-get")
        else:
            self._logger.error("Device name not recognised")

    def update_addon_device_state(self, device, enable):

        self._logger.debug("Updating addon device state...")

        if 'pi-topSPEAKER' in device['name']:
            if 'ptspeaker' in self._custom_imported_modules:
                ptspeaker_cfg = self._custom_imported_modules['ptspeaker']

                if self._i2s_mode_current is True:
                    if self._i2s_mode_next is True:
                        self._logger.debug("I2S appears to be enabled - disabling...")
                        self.enable_i2s(False)

                        # Also ensure that HDMI is correctly configured, so we
                        # don't have to reboot twice
                        self.set_hdmi_drive_in_boot_config()

                    # Add to enabled devices to prevent further scans
                    # attempting to initialise device
                    self.add_enabled_device(device)

                else:
                    self._logger.debug("Initialising pi-topSPEAKER...")

                    if enable:
                        if ptspeaker_cfg.set_audio_output_hdmi():
                            try:
                                mode = format(device['addr'], 'x')

                                # Switch on I2C if it's not enabled
                                if self._i2c_mode is False:
                                    self.enable_i2c(True)

                                if self._i2c_mode is False:
                                    self._logger.error("Unable to initialise I2C - updating addon device state")

                                else:
                                    if ptspeaker_cfg.enable(mode):
                                        self.add_enabled_device(device)

                                        if (self.set_hdmi_drive_in_boot_config() is True):
                                            self.emit_reboot_message()

                                        self._logger.debug("OK.")
                                        return True

                                    else:
                                        self._logger.debug(
                                            "Error initialising speaker")

                            except Exception as e:
                                self._logger.error("Failed to configure pi-topSPEAKER. Error: " + str(e))
                                self._logger.info(traceback.format_exc())

                        else:
                            self._logger.error("Failed to configure HDMI output")
                    # else:
                        # Do nothing - speaker cannot currently be disabled

                if (self._i2s_mode_current != self._i2s_mode_next):
                    self.emit_reboot_message()

            else:
                if sys.version_info >= (3, 0):
                    package = "python3-pt-speaker"

                else:
                    package = "python-pt-speaker"

                self._logger.info("pi-topSPEAKER initialisation not available - please install '" + package + "' package via apt-get")
        else:
            self._logger.error("Device name not recognised")

    def update_device_state(self, device, enable):

        if enable:
            self._logger.info("Enabling device: " + device['name'])

        else:
            self._logger.info("Disabling device: " + device['name'])

        device_enabled = (device in self._enabled_devices)
        valid = (enable != device_enabled)

        if valid:
            if device['type'] == 'HAT':
                self.update_hat_device_state(device, enable)

            elif device['type'] == 'addon':
                self.update_addon_device_state(device, enable)

            else:
                self._logger.error("Unrecognised device type")

        else:
            self._logger.debug("Device state was already set")

    def get_connected_device_addresses(self):

        addresses_arr = []

        # Switch on I2C if it's not enabled
        if self._i2c_mode is False:
            self.enable_i2c(True)

        if self._i2c_mode is False:
            self._logger.error("Unable to initialise I2C - getting connected device addresses")

        else:
            output_lines = check_output(["/usr/sbin/i2cdetect", "-y", "1"]).decode("utf-8").splitlines()[1:]
            for line in output_lines:
                prefix, addresses_line = str(line).split(':')

                new_addresses = addresses_line.replace("--", "").split()
                addresses_arr.extend(new_addresses)

        return addresses_arr

    def get_connected_devices(self):

        addresses = self.get_connected_device_addresses()

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

    def enable_i2c(self, enable):

        if enable:
            self._logger.debug("Enabling I2C...")
            call(["/usr/bin/raspi-config", "nonint", "do_i2c", "0"])

        else:
            self._logger.debug("Disabling I2C...")
            call(["/usr/bin/raspi-config", "nonint", "do_i2c", "1"])

        self.determine_i2c_mode_from_system()

    def enable_i2s(self, enable):

        if enable:
            call(["/usr/bin/pt-i2s", "enable"])
        else:
            call(["/usr/bin/pt-i2s", "disable"])

        self.determine_i2s_mode_from_system()

    def get_value_from_line(self, line_to_check):

        fields = line_to_check.split("=")
        return fields[-1].replace("\n", "")

    def strip_whitespace(self, line):

        return "".join(line.split())

    def is_line_commented(self, line_to_check):

        stripped_line = self.strip_whitespace(line_to_check)
        return stripped_line.startswith('#')

    def comment_line(self, line_to_change):

        stripped_line = self.strip_whitespace(line_to_change)
        commented_line = "#" + stripped_line
        return commented_line

    def uncomment_line(self, line_to_change):

        return line_to_change.replace("#", "")

    def set_hdmi_drive_in_boot_config(self):

        self._logger.debug("Checking hdmi_drive setting in " + self._boot_config_file_path + "...")

        setting_updated = False
        setting_found = False

        temp_file = self.create_temp_file()

        with open(temp_file, 'w') as output_file:
            with open(self._boot_config_file_path, 'r') as input_file:

                # Write all lines from input to output, except the hdmi_drive
                # setting
                for line in input_file:
                    line_to_write = line

                    if "hdmi_drive=" in line_to_write:
                        setting_found = True

                        if (self.is_line_commented(line_to_write)):
                            line_to_write = self.uncomment_line(line_to_write)
                            setting_updated = True

                        if "hdmi_drive=2" not in line_to_write:
                            line_to_write = "hdmi_drive=2\n"
                            setting_updated = True

                    output_file.write(line_to_write)

            if (setting_found is False):
                output_file.write("hdmi_drive=2 # Added for pi-topSPEAKER")
                setting_updated = True

        if (setting_updated is True):

            self._logger.info("Updating " + self._boot_config_file_path + " to set hdmi_drive setting...")
            copy(temp_file, self._boot_config_file_path)

        else:
            self._logger.debug(
                "hdmi_drive setting already set in " + self._boot_config_file_path)

        return setting_updated

    def set_serial_baud_rate_in_boot_config(self):

        config_values = {
            "init_uart_clock": "1627604",
            "init_uart_baud": "460800",
            "enable_uart": "1"
        }

        config_values_enabled = {
            "init_uart_clock": False,
            "init_uart_baud": False,
            "enable_uart": False
        }

        temp_file = self.create_temp_file()

        if not (path.isfile(self._boot_config_file_path)):
            self._logger.error(self._boot_config_file_path + " file not found!")
            return

        with open(self._boot_config_file_path, 'r') as input_file:
            with open(temp_file, 'w') as output_file:

                # Write all lines from input to output, except those relating
                # to UART config
                for line in input_file:
                    line_to_write = line

                    for field_to_find in config_values:
                        if field_to_find in line:
                            if config_values_enabled[field_to_find]:

                                if not self.is_line_commented(line):
                                    line_to_write = self.comment_line(line) + "\n"

                            else:
                                if self.is_line_commented(line):
                                    # If value is correct, uncomment - else, leave alone
                                    # Check value is correct
                                    last_field = self.get_value_from_line(line)

                                    desired_value = config_values[
                                        field_to_find]

                                    if last_field == desired_value:
                                        line_to_write = self.uncomment_line(
                                            line) + "\n"
                                        config_values_enabled[
                                            field_to_find] = True
                                    # else:
                                        # Not correct -  leave commented out
                                else:
                                    # If value is not correct, comment out - else, leave alone
                                    # Check value is correct
                                    last_field = self.get_value_from_line(line)

                                    desired_value = config_values[
                                        field_to_find]

                                    if last_field == desired_value:
                                        # Correct -  leave uncommented
                                        config_values_enabled[
                                            field_to_find] = True

                                    else:
                                        # Not correct -  line needs to be
                                        # commented out
                                        line_to_write = self.comment_line(
                                            line) + "\n"

                            # Field was found - go to next line
                            break

                    output_file.write(line_to_write)

                for field in config_values:
                    value_is_enabled = config_values_enabled[field]

                    if value_is_enabled is False:
                        value = config_values[field]
                        output_file.write(field + "=" + str(value) + "\n")
                        output_file.write("\n")

        self._logger.info("Updating " + self._boot_config_file_path + " to configure serial...")
        copy(temp_file, self._boot_config_file_path)

    def remove_serial_from_cmdline(self):

        ptdm_common.CommonFunctions.sed_inplace('/boot/cmdline.txt', r'console=ttyAMA0,[0-9]+ ', '')
        ptdm_common.CommonFunctions.sed_inplace('/boot/cmdline.txt', r'console=serial0,[0-9]+ ', '')

    def _baud_rate_correctly_configured(self):

        clock_string = self.get_value_from_boot_config("init_uart_clock")
        baud_string = self.get_value_from_boot_config("init_uart_baud")
        enabled_string = self.get_value_from_boot_config("enable_uart")

        return (clock_string == "1627604") and (baud_string == "460800") and (enabled_string == "1")

    def get_value_from_boot_config(self, property_name):

        if not (path.isfile(self._boot_config_file_path)):
            self._logger.error("/boot/config.txt file not found!")
            return ""

        with open(self._boot_config_file_path) as config_file:
            for line in config_file:
                if (property_name in line):
                    if not line.strip().startswith("#"):
                        value = self.get_value_from_config_line(line)
                        return value

        return ""

    def get_value_from_config_line(self, line):

        value = ""
        index = 0

        while line[index] != "=" and index < len(line):
            index = index + 1

        while (line[index] == "=" or line[index] == " ") and index < len(line):
            index = index + 1

        while line[index].isdigit() and index < len(line):
            value = value + line[index]
            index = index + 1

        return value.strip()

    def create_temp_file(self):
        temp_file_tuple = mkstemp()
        close(temp_file_tuple[0])

        return temp_file_tuple[1]

    def determine_i2c_mode_from_system(self):
        try:
            i2c_output = int(str(check_output(
                ["/usr/bin/raspi-config", "nonint", "get_i2c"]).decode("utf-8")).rstrip())

            self._i2c_mode = (i2c_output == 0)

            if self._i2c_mode is False and i2c_output == 1:
                self._logger.error("Unable to verify I2C mode - assuming disabled")
        except Exception as e:
            self._logger.error("Unable to verify I2C mode. " + str(e))
            self._logger.info(traceback.format_exc())

    def determine_i2s_mode_from_system(self):
        self._i2s_mode_current = False
        self._i2s_mode_next = False

        try:
            i2s_output = check_output(["/usr/bin/pt-i2s"]).decode("utf-8").splitlines()

            for line in i2s_output:
                if 'I2S is currently enabled' in str(line):
                    self._i2s_mode_current = True

                elif 'I2S is due to be enabled on reboot' in str(line):
                    self._i2s_mode_next = True
        except Exception as e:
            self._logger.error("Unable to verify I2S mode. " + str(e))
            self._logger.info(traceback.format_exc())

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
            self._logger.debug(
                "Device " + current_device_name + " already enabled")

    def auto_initialise_peripherals(self):

        addresses = self.get_connected_device_addresses()

        for device in self._enabled_devices:

            if format(device['addr'], 'x') not in addresses:

                self._logger.debug(
                    "Device " + device['name'] + " was enabled but not detected.")

                self.remove_enabled_device(device)
                self.attempt_disable_device_by_name(device['name'])

        for address in addresses:

            current_device = self.get_device_by_address(address)

            if current_device is not None:
                self.attempt_enable_device_by_name(current_device['name'])

    def touch(self, fname, times=None):

        with open(fname, 'a'):
            utime(fname, times)

    def reboot_system(self):

        call(("/sbin/reboot"))

    def configure_hifiberry_alsactl(self):

        if self._i2s_mode_current is True and path.isfile(self._i2s_configured_file_path) is False:
            call(("/usr/sbin/alsactl", "-f", self._i2s_config_file_path, "restore"))
            self.touch(self._i2s_configured_file_path)
            self.reboot_system()

    def get_peripheral_enabled(self, peripheral_id):

        device = self.get_device_by_id(peripheral_id)
        if (device is not None):
            if (device in self._enabled_devices):
                return True

        return False
