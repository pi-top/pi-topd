import traceback
from os import path
from sys import exit

from pitop.common.common_ids import DeviceID
from pitop.common.current_session_info import get_user_using_first_display
from pitop.common.logger import PTLogger
from smbus import SMBus
from sys_config import HDMI, I2C, I2S

_BUS_ID = 1
_I2C_BUS = None
_v1_i2c_addr = 0x18
_v1_i2c_ce_reg = 0x00

_host_device_id = None
_speaker_type_name = None

CFG_FILE_PATH = path.dirname(path.realpath(__file__)) + "/setup.cfg"


def _set_hdmi_as_audio_output():
    if not HDMI.set_as_audio_output(user=get_user_using_first_display()):
        PTLogger.error("Failed to configure HDMI output")


def _enable_i2c_if_disabled():
    try:
        # Switch on I2C if it's not enabled
        if I2C.get_state() is False:
            I2C.set_state(True)

        if I2C.get_state() is False:
            PTLogger.error("Unable to initialise I2C")
    except Exception as e:
        PTLogger.error("Failed to configure pi-topSPEAKER. Error: " + str(e))
        PTLogger.info(traceback.format_exc())


def _set_write_to_v1_speaker_enabled(address, enable):
    global _I2C_BUS

    if enable:
        PTLogger.info("Enabling write to pi-topSPEAKER (" + str(address) + ")")
    else:
        PTLogger.info("Disabling write to pi-topSPEAKER (" + str(address) + ")")

    try:
        _I2C_BUS = SMBus(_BUS_ID)
        value = 0x01 if enable else 0x00
        _I2C_BUS.write_byte_data(address, _v1_i2c_ce_reg, value)

    except Exception as e:
        PTLogger.info("Failed to write to pi-topSPEAKER: " + str(e))
        return False

    return True


def _parse_v1_speaker_playback_mode_file(mode):

    PTLogger.info("Writing config data to pi-topSPEAKER")

    try:
        index = 0
        with open(CFG_FILE_PATH) as file_data:
            for line in file_data:
                if (line[0] == "W") or (line[0].lower() == mode):
                    array = line.split()
                    if len(array) < 4:
                        PTLogger.info(
                            "Error parsing line " + str(index) + " - exiting..."
                        )
                        exit(0)
                    else:
                        # Write all values from 4th to the end of the line

                        if len(array) > 3:
                            values = [int(i, 16) for i in array[3:]]
                            _I2C_BUS.write_i2c_block_data(
                                _v1_i2c_addr, int(array[2], 16), values
                            )
                        else:
                            _I2C_BUS.write_byte_data(
                                _v1_i2c_addr, int(array[2], 16), int(array[3], 16)
                            )
                index = index + 1

        return True

    except Exception as e:
        PTLogger.info("Failed to write configuration data to pi-topSPEAKER: " + str(e))
        return False


def _enable_v1_speaker(mode):
    PTLogger.info("Initialising speaker (mode " + mode + ")")

    if not path.exists(CFG_FILE_PATH):
        PTLogger.info("Error: playback configuration file does not exist")
        return None

    if mode == "l" or str(mode) == "71":
        mode = "l"
        address = 0x71
    elif mode == "r" or str(mode) == "72":
        mode = "r"
        address = 0x72
    elif mode == "m" or str(mode) == "73":
        mode = "m"
        address = 0x73
    else:
        PTLogger.info("Mode not recognised")
        return False

    if _set_write_to_v1_speaker_enabled(address, True) is False:
        PTLogger.info("Error enabling write to pi-topSPEAKER")
        return False

    if _parse_v1_speaker_playback_mode_file(mode) is False:
        PTLogger.info("Error parsing and writing mode file to pi-topSPEAKER")
        return False

    if _set_write_to_v1_speaker_enabled(address, False) is False:
        PTLogger.info("Error disabling write to pi-topSPEAKER")
        return False

    return True


def _initialise_v1_hub_v1_speaker(mode):
    # HDMI w/ config

    enabled = False
    reboot_required = False

    i2s_mode_current, i2s_mode_next = I2S.get_states()
    if i2s_mode_current is True:
        # If in I2S mode
        if i2s_mode_next is True:
            PTLogger.debug("I2S appears to be enabled - disabling...")
            I2S.set_state(False)
            reboot_required = True
    else:
        PTLogger.debug("Initialising pi-topSPEAKER...")
        _set_hdmi_as_audio_output()
        _enable_i2c_if_disabled()
        enabled = _enable_v1_speaker(mode)

    reboot_required = HDMI.set_hdmi_drive_in_boot_config(2) or reboot_required
    enabled = enabled and not reboot_required

    v2_hub_hdmi_to_i2s_required = False

    return enabled, reboot_required, v2_hub_hdmi_to_i2s_required


def _initialise_v1_hub_v2_speaker():
    # Enable I2S

    enabled = False
    reboot_required = False

    i2s_mode_current, i2s_mode_next = I2S.get_states()

    if i2s_mode_current is False:
        # If not in I2S mode
        if i2s_mode_next is False:
            PTLogger.debug("I2S appears to be disabled - enabling...")
            I2S.set_state(True)
            reboot_required = True
    else:
        PTLogger.debug("Initialising pi-topSPEAKER...")
        enabled = True

    reboot_required = HDMI.set_hdmi_drive_in_boot_config(2) or reboot_required
    enabled = enabled and not reboot_required

    v2_hub_hdmi_to_i2s_required = False

    return enabled, reboot_required, v2_hub_hdmi_to_i2s_required


def _initialise_v2_hub_v2_speaker():
    # Disable I2S

    enabled = False
    reboot_required = False

    i2s_mode_current, i2s_mode_next = I2S.get_states()
    if i2s_mode_current is True:
        # If in I2S mode
        if i2s_mode_next is True:
            PTLogger.debug("I2S appears to be enabled - disabling...")
            I2S.set_state(False)
            reboot_required = True
    else:
        PTLogger.debug("Initialising pi-topSPEAKER v2...")
        _set_hdmi_as_audio_output()
        _enable_i2c_if_disabled()
        enabled = True

    reboot_required = HDMI.set_hdmi_drive_in_boot_config(2) or reboot_required
    enabled = enabled and not reboot_required

    v2_hub_hdmi_to_i2s_required = True

    return enabled, reboot_required, v2_hub_hdmi_to_i2s_required


def initialise(host_device_id, speaker_type_name):
    global _host_device_id
    global _speaker_type_name

    _host_device_id = host_device_id
    _speaker_type_name = speaker_type_name


def enable_device():
    enabled = False
    reboot_required = False
    v2_hub_hdmi_to_i2s_required = False

    is_pi_top = _host_device_id == DeviceID.pi_top
    is_pi_top_ceed = _host_device_id == DeviceID.pi_top_ceed
    hub_is_v1 = is_pi_top or is_pi_top_ceed

    is_pi_top_3 = _host_device_id == DeviceID.pi_top_3

    if is_pi_top_3:
        if "pi-topSPEAKER-v1" in _speaker_type_name:
            PTLogger.info("pi-topSPEAKER v1 is not supported on pi-top v2")
        elif "pi-topSPEAKER-v2" in _speaker_type_name:
            (
                enabled,
                reboot_required,
                v2_hub_hdmi_to_i2s_required,
            ) = _initialise_v2_hub_v2_speaker()
        else:
            PTLogger.error("Error - unrecognised device: " + _speaker_type_name)
    elif hub_is_v1 or (_host_device_id == DeviceID.unknown):
        if "pi-topSPEAKER-v1-" in _speaker_type_name:
            mode_long = _speaker_type_name.replace("pi-topSPEAKER-v1-", "")
            mode_first_lower_char = mode_long[0].lower()
            (
                enabled,
                reboot_required,
                v2_hub_hdmi_to_i2s_required,
            ) = _initialise_v1_hub_v1_speaker(mode_first_lower_char)
        elif "pi-topSPEAKER-v2" in _speaker_type_name:
            (
                enabled,
                reboot_required,
                v2_hub_hdmi_to_i2s_required,
            ) = _initialise_v1_hub_v2_speaker()
        else:
            PTLogger.error("Error - unrecognised device: " + _speaker_type_name)

    else:
        PTLogger.error(
            "Error - unrecognised device ID '"
            + str(_host_device_id)
            + "' - unsure how to initialise "
            + _speaker_type_name
        )

    return enabled, reboot_required, v2_hub_hdmi_to_i2s_required


def disable_device():
    disabled = True
    return disabled
