from distutils.version import StrictVersion
from os.path import isfile
from platform import uname
from time import sleep

from pitop.common.common_ids import DeviceID
from pitop.common.i2c_device import I2CDevice
from spidev import SpiDev

from . import state


def _do_poweroff_legacy():
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


def _do_poweroff(device_id):
    i2c_address = 0x11 if device_id == DeviceID.pi_top_4 else 0x10

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


def _do_reboot():
    i2c_address = 0x11
    PWR__SHUTDOWN_CTRL = 0xA0
    PWR__SHUTDOWN_CTRL__MODE5 = 0x28

    hub = I2CDevice("/dev/i2c-1", i2c_address)
    hub.connect()

    # Get the current power control register
    shutdown_control = hub.read_unsigned_byte(PWR__SHUTDOWN_CTRL)

    # Set the shutdown mode to 5
    shutdown_control = shutdown_control | PWR__SHUTDOWN_CTRL__MODE5

    # Write back to the device
    hub.write_byte(PWR__SHUTDOWN_CTRL, shutdown_control)


def get_device_id():
    id_str = state.get("device", "type", fallback=str(DeviceID.unknown.name))
    return DeviceID[id_str]


def reboot():
    try:
        if get_device_id() == DeviceID.pi_top_4:
            _do_reboot()

    except Exception as e:
        print("Error starting reboot service: " + str(e))


def poweroff():
    try:
        device_id = get_device_id()
        if device_id in [DeviceID.pi_top, DeviceID.pi_top_ceed]:
            _do_poweroff_legacy()
        elif device_id in [DeviceID.pi_top_3, DeviceID.pi_top_4]:
            _do_poweroff(device_id)

    except Exception as e:
        print("Error starting shutdown service: " + str(e))
