from os import environ
from signal import SIGINT, SIGTERM, signal

import click
from pitop.common.logger import PTLogger
from systemd.daemon import notify

from .app import App


# TODO: import these functions
def do_poweroff_legacy():
    from distutils.version import StrictVersion
    from platform import uname
    from time import sleep

    from spidev import SpiDev

    MASK_SHUTDOWN = 0x01  # 00000001
    MASK_SCREEN_OFF = 0x02  # 00000010
    MASK_LID_CLOSED = 0x04  # 00000100
    MASK_BRIGHTNESS = 0x78  # 01111000
    MASK_PARITY = 0x80  # 10000000

    screen_off = False
    brightness = 0
    request_shutdown = False

    def using_old_kernel():
        current_version_name = uname().release.split("-")[0]
        return StrictVersion(current_version_name) < StrictVersion("5.0.0")

    def parity7(data):
        p = False
        for _ in range(7):
            if data & 1:
                p = not p

            data = data >> 1

        return p

    def calculate():
        data = brightness << 3

        if parity7(brightness):
            data += MASK_PARITY

        if request_shutdown:
            data += MASK_SHUTDOWN

        if screen_off:
            data += MASK_SCREEN_OFF

        if parity7(data & 3):
            data += MASK_LID_CLOSED  # parity of the two state bits

        return data

    def setup_spi_obj():
        spi_obj = SpiDev()
        spi_obj.open(0, 1)
        spi_obj.max_speed_hz = 9600
        spi_obj.mode = 0b00
        spi_obj.bits_per_word = 8
        spi_obj.cshigh = True
        spi_obj.lsbfirst = False

        return spi_obj

    def send_data(spi_obj, data):
        print(f"Sending: {hex(data)}")

        if using_old_kernel():
            spi_obj.cshigh = False

        resp = spi_obj.xfer2([data], spi_obj.max_speed_hz)

        spi_obj.cshigh = True

        print(f"Receiving: {hex(resp[0])}")

        return resp[0]

    print("pi-top poweroff-legacy (for v1 hubs - Original pi-top/pi-topCEED")
    sleep(5)  # Let other things finish first

    spi = setup_spi_obj()

    resp = send_data(spi, 0xFF)

    brightness = resp & MASK_BRIGHTNESS >> 3
    print(f"Current brightness = {brightness}")

    # Fix brightness if not within acceptable range
    if brightness > 10:
        brightness = 10

    if brightness < 3:
        brightness = 3

    # Calculate data to send
    request_shutdown = True
    screen_off = True

    send_data(spi, calculate())


def do_poweroff():
    from os.path import isfile
    from sys import argv

    from pitop.common.i2c_device import I2CDevice

    try:
        device_id = argv[1]
    except Exception as e:
        print("Error getting pi-top version from pt-poweroff: " + str(e))
        exit(1)

    i2c_address = 0x11 if device_id == "pi_top_4" else 0x10

    PWR__SHUTDOWN_CTRL = 0xA0
    PWR__SHUTDOWN_CTRL__MODE1 = 0x08
    PWR__SHUTDOWN_CTRL__MODE4 = 0x20

    try:

        hub = I2CDevice("/dev/i2c-1", i2c_address)
        hub.connect()

        # Get the current power control register
        shutdown_control = hub.read_unsigned_byte(PWR__SHUTDOWN_CTRL)

        if isfile("/tmp/.com.pi-top.pi-topd.pt-poweroff.reboot-on-shutdown"):
            # Set shutdown mode to 4
            shutdown_control = shutdown_control | PWR__SHUTDOWN_CTRL__MODE4
        else:
            # Set shutdown mode to 1
            shutdown_control = shutdown_control | PWR__SHUTDOWN_CTRL__MODE1

        # Write back to the device
        hub.write_byte(PWR__SHUTDOWN_CTRL, shutdown_control)

    except Exception as e:
        print("Error shutting down the hub: " + str(e))


def reboot():
    from os.path import exists

    from pitop.common.i2c_device import I2CDevice

    i2c_address = 0x11
    PWR__SHUTDOWN_CTRL = 0xA0
    PWR__SHUTDOWN_CTRL__MODE5 = 0x28

    device_version_file = "/etc/pi-top/pi-topd/device_version"

    try:
        device_version = ""
        if exists(device_version_file):
            with open(device_version_file, "r") as f:
                device_version = f.readline().strip()

        if device_version == "pi_top_4":
            hub = I2CDevice("/dev/i2c-1", i2c_address)
            hub.connect()

            # Get the current power control register
            shutdown_control = hub.read_unsigned_byte(PWR__SHUTDOWN_CTRL)

            # Set the shutdown mode to 5
            shutdown_control = shutdown_control | PWR__SHUTDOWN_CTRL__MODE5

            # Write back to the device
            hub.write_byte(PWR__SHUTDOWN_CTRL, shutdown_control)

    except Exception as e:
        print("Error starting reboot service: " + str(e))


def poweroff():
    from os.path import exists

    try:
        # TODO: get from correct place
        device_version_file = "/etc/pi-top/pi-topd/device_version"

        if exists(device_version_file):

            device_version = ""
            with open(device_version_file, "r") as f:
                device_version = f.readline().strip()

            print(f"Device: {device_version}")
            if device_version in ["pi_top", "pi_top_ceed"]:
                # TODO: 15s timeout?
                do_poweroff_legacy()
            elif device_version in ["pi_top_3", "pi_top_4"]:
                # TODO: 5s timeout?
                do_poweroff()
            else:
                print("pt-poweroff did not receive a valid pt product version number.")
                exit(0)

    except Exception as e:
        print("Error starting shutdown service: " + str(e))


@click.command()
@click.option(
    "--log-level",
    type=int,
    help="set logging level from 10 (more verbose) to 50 (less verbose)",
    default=20,
    show_default=True,
)
@click.version_option()
def main(log_level) -> None:
    # Set the display env var
    environ["DISPLAY"] = ":0.0"

    PTLogger.setup_logging(
        logger_name="pi-topd", logging_level=log_level, log_to_journal=False
    )

    app = App()

    for sig in [SIGINT, SIGTERM]:
        signal(sig, lambda x, _: app.stop())

    # Blocking
    successful_start = app.start()

    # After main loop
    notify("STOPPING=1")

    if not successful_start:
        PTLogger.error("Unable to start pi-topd")
        app.stop()

    # Exiting with 1 will cause systemd service to restart - we should only do this if we failed to determine a device ID
    exit(0 if app.device_id is not None else 1)
