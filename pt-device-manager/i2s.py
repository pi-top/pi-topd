import os
import re
import shutil
import subprocess

# Switch I2S on/off, specifically when targeting pi-topSPEAKER/pi-topPULSE.
# This is **only** used in conjunction with pi-topHUB v1,
# as I2S is handled automatically on pi-topHUB v2.
# To configure for I2S, a custom `asound.conf` file is used to enable mixing
# multiple audio sources.
# As well as this, some settings in `/boot/config.txt` are altered:
#   * `dtoverlay=hifiberry-dac` - enables I2S audio on subsequent boots
#   * `#dtparam=audio=on` - disables default sound driver
#   * `dtoverlay=i2s-mmap` - allows multiple audio sources to be mixed together
#
# Disabling I2S reverses these changes.


TEMP_ASOUND_CONF = "/tmp/asound.conf.tmp"
BAK_ASOUND_CONF = "/etc/asound.conf.bak"
ASOUND_CONF = "/etc/asound.conf"

# If we can't access this, there's issues
with open("/boot/config.txt", "r") as f:
    contents = f.read()

lines = contents.split("\n")


def get_matching_lines(regex):
    return filter(re.compile(regex).match, lines)


def activeOverlayExists(overlay):
    return len(get_matching_lines(f"^dtoverlay={overlay}$")) > 0


def inactiveOverlayExists(overlay):
    return len(get_matching_lines(f"^#dtoverlay={overlay}$")) > 0


def activeParamExists(param):
    return len(get_matching_lines(f"^dtparam={param}=on$")) > 0


def inactiveParamExists(param):
    return len(get_matching_lines(f"#^dtparam={param}=on$")) > 0


def i2sIsEnabledThisSession():
    return (
        "rpi_simple_soundcard" in subprocess.run(["lsmod"], capture_output=True).stdout
    )


def i2sIsToBeEnabledNextSession():
    return (
        activeOverlayExists("i2s-mmap")
        and activeOverlayExists("hifiberry-dac")
        and not activeParamExists("audio")
    )


def setDTOverlayState(overlay, enable):
    if enable:
        print(f"Attempting to enable {overlay} overlay...")
        if activeOverlayExists(overlay):
            print(f"{overlay} overlay already active - nothing to do")
        else:
            print(f"{overlay} overlay not active - enabling")
            # line = f"dtoverlay={overlay}"
            if inactiveOverlayExists(overlay):
                # sudo sed -i "s/^#$line$/$line/1" $CONFIG
                pass
            else:
                # echo "$line" | sudo tee -a $CONFIG &>/dev/null
                pass

    else:
        print(f"Attempting to disable {overlay} overlay...")
        if activeOverlayExists(overlay):
            print(f"{overlay} overlay active - disabling")
            # sudo sed -i "s/^$line/#&/1" $CONFIG
            pass
        else:
            print(f"{overlay} overlay not in device tree - nothing to do")


def setDTParamState(param, enable):
    if enable:
        print(f"Attempting to enable {param} param...")
        if activeParamExists(param):
            print(f"{param} param already active - nothing to do")
        else:
            print(f"{param} param not active - enabling")
            # line = f"dtparam={param}=on"
            if inactiveParamExists(param):
                # sudo sed -i "s/^#$line$/$line/1" $CONFIG
                pass
            else:
                # echo "$line" | sudo tee -a $CONFIG &>/dev/null
                pass

    else:
        print(f"Attempting to disable {param} param...")
        if activeParamExists(param):
            print(f"{param} param active - disabling")
            # sudo sed -i "s/^$line/#&/1" $CONFIG
            pass
        else:
            print(f"{param} param not in device tree - nothing to do")


def backupOrigAsoundConf():
    try:
        os.remove(BAK_ASOUND_CONF)
    except OSError:
        pass

    try:
        shutil.move(ASOUND_CONF, BAK_ASOUND_CONF)
    except OSError:
        pass


def restoreOrigAsoundConf():
    try:
        os.remove(ASOUND_CONF)
    except OSError:
        pass

    try:
        shutil.move(BAK_ASOUND_CONF, ASOUND_CONF)
    except OSError:
        pass


def setCustomAsoundConfState(enableCustomConf):
    if enableCustomConf == 0:
        backupOrigAsoundConf()

        print("Configuring custom asound.conf")

        with open(TEMP_ASOUND_CONF, "w") as f:
            f.writelines(
                [
                    "pcm.real {",
                    "  type hw",
                    "  card 0",
                    "  device 0",
                    "}",
                    "pcm.dmixer {",
                    "  type dmix",
                    "  ipc_key 1024",
                    "  ipc_perm 0666",
                    '  slave.pcm "real"',
                    "  slave {",
                    "    period_time 0",
                    "    period_size 1024",
                    "    buffer_size 8192",
                    "    rate 44100",
                    "  }",
                    "  bindings {",
                    "    0 0",
                    "    1 1",
                    "  }",
                    "}",
                    "ctl.dmixer {",
                    "  type hw",
                    "  card 0",
                    "}" "pcm.softvol {",
                    "  type softvol",
                    '  slave.pcm "dmixer"',
                    "  control {",
                    '    name "PCM"',
                    "    card 0",
                    "   }",
                    "}",
                    "pcm.\041default {",
                    "   type plug",
                    '   slave.pcm "softvol"',
                    "}",
                ]
            )

        shutil.move(TEMP_ASOUND_CONF, ASOUND_CONF)
    else:
        restoreOrigAsoundConf()


def setI2S(command):
    if command is None or command == "status":
        desired_i2s_enabled_state = -1
    elif command == "enable":
        desired_i2s_enabled_state = 0
    elif command == "disable":
        desired_i2s_enabled_state = 1
    else:
        return

    if i2sIsEnabledThisSession():
        print("I2S is currently enabled")
    else:
        print("I2S is currently disabled")

    if i2sIsToBeEnabledNextSession:
        print("I2S is due to be enabled on reboot")
        if desired_i2s_enabled_state == 0:
            print("Nothing to do")
            return
    else:
        print("I2S is due to be disabled on reboot")
        if desired_i2s_enabled_state == 1:
            print("Nothing to do")
            return

    if command is None or command == "status":
        return

    setDTOverlayState("i2s-mmap", desired_i2s_enabled_state)
    setDTOverlayState("hifiberry-dac", desired_i2s_enabled_state)
    setDTParamState("audio", 1 - desired_i2s_enabled_state)
    setDTParamState("i2s", desired_i2s_enabled_state)
    setCustomAsoundConfState(desired_i2s_enabled_state)
