from pitop.common.common_ids import DeviceID
from pitop.common.logger import PTLogger

from . import pthub_i2c, pthub_spi

_state = None

spi_cycle_sleep_time = pthub_spi._cycle_sleep_time


class State:
    def __init__(self):

        self._brightness = 10
        self._screen_blanked = False
        self._lid_closed = False
        self._shutdown = 0
        self._device_id = DeviceID.unknown
        self._battery_charging_state = -1
        self._battery_time = -1
        self._battery_capacity = -1
        self._battery_wattage = -1

        self._brightness_change_func = None
        self._screen_blanked_func = None
        self._screen_unblanked_func = None
        self._lid_opened_func = None
        self._lid_closed_func = None
        self._shutdown_func = None
        self._battery_state_change_func = None

    def register_client(
        self,
        on_brightness_changed_func=None,
        on_screen_blanked_func=None,
        on_screen_unblanked_func=None,
        on_lid_opened_func=None,
        on_lid_closed_func=None,
        on_shutdown_requested_func=None,
        on_battery_state_changed_func=None,
    ):

        self._brightness_change_func = on_brightness_changed_func
        self._screen_blanked_func = on_screen_blanked_func
        self._screen_unblanked_func = on_screen_unblanked_func
        self._lid_opened_func = on_lid_opened_func
        self._lid_closed_func = on_lid_closed_func
        self._shutdown_func = on_shutdown_requested_func
        self._battery_state_change_func = on_battery_state_changed_func

    def valid_brightness(self, val):
        return _represents_int(val) and (int(val) >= 0) and (int(val) <= 10)

    def emit_battery_state_change(self):
        if callable(self._battery_state_change_func):
            self._battery_state_change_func(
                int(self._battery_charging_state),
                int(self._battery_capacity),
                int(self._battery_time),
                int(self._battery_wattage),
            )

    def emit_brightness_change(self):
        if callable(self._brightness_change_func):
            self._brightness_change_func(self._brightness)

    def emit_screen_blanked(self):
        if callable(self._screen_blanked_func):
            self._screen_blanked_func()

    def emit_screen_unblanked(self):
        if callable(self._screen_unblanked_func):
            self._screen_unblanked_func()

    def emit_lid_opened(self):
        if callable(self._lid_opened_func):
            self._lid_opened_func()

    def emit_lid_closed(self):
        if callable(self._lid_closed_func):
            self._lid_closed_func()

    def emit_shutdown(self):
        if callable(self._shutdown_func):
            self._shutdown_func()

    def set_battery_charging_state(self, val):
        if self._battery_charging_state != val:
            self._battery_charging_state = val
            self.emit_battery_state_change()

    def set_battery_capacity(self, val):
        if self._battery_capacity != val:
            self._battery_capacity = val
            self.emit_battery_state_change()

    def set_battery_time(self, val):
        if self._battery_time != val:
            self._battery_time = val
            self.emit_battery_state_change()

    def set_battery_wattage(self, val):
        if self._battery_wattage != val:
            self._battery_wattage = val
            self.emit_battery_state_change()

    def set_brightness(self, val, emit=True):
        if self.valid_brightness(val):
            if self._brightness != val:
                self._brightness = val
                if emit is True:
                    self.emit_brightness_change()

    def set_screen_blanked(self):
        if self._screen_blanked is False:
            self._screen_blanked = True
            self.emit_screen_blanked()

    def set_screen_unblanked(self):
        if self._screen_blanked is True:
            self._screen_blanked = False
            self.emit_screen_unblanked()

    def set_lid_open(self):
        if self._lid_closed is True:
            self._lid_closed = False
            self.emit_lid_opened()

    def set_lid_closed(self):
        if self._lid_closed is False:
            self._lid_closed = True
            self.emit_lid_closed()

    def set_device_id(self, val):
        if self._device_id != val:
            self._device_id = val

    def set_shutdown(self, val):
        if self._shutdown != val:
            if val == 1 and self._shutdown_func is not None:
                self.emit_shutdown()


def initialise():
    global _state

    _state = State()

    PTLogger.info("Initialising I2C...")
    pthub_i2c.initialise(_state)

    PTLogger.info("Initialising SPI...")
    pthub_spi.initialise(_state)

    if pthub_spi.is_initialised() is False:
        PTLogger.error("Unable to detect pi-topHUB via SPI")
        _state.set_device_id(DeviceID.unknown)
        return False

    if pthub_i2c.is_initialised():
        PTLogger.info("Detected pi-top battery. This is a pi-top")
        _state.set_device_id(DeviceID.pi_top)

    else:
        PTLogger.info(
            "Unable to detect pi-topHUB's battery. If host is a CEED this will be established after initial communication"
        )

    return True


def register_client(
    on_brightness_changed_func=None,
    on_screen_blanked_func=None,
    on_screen_unblanked_func=None,
    on_lid_opened_func=None,
    on_lid_closed_func=None,
    on_shutdown_requested_func=None,
    on_battery_state_changed_func=None,
):

    _state.register_client(
        on_brightness_changed_func,
        on_screen_blanked_func,
        on_screen_unblanked_func,
        on_lid_opened_func,
        on_lid_closed_func,
        on_shutdown_requested_func,
        on_battery_state_changed_func,
    )


def start():
    _start_spi()
    _start_i2c()


def stop():
    _stop_spi()
    _stop_i2c()


def increment_brightness():
    pthub_spi.increment_brightness()


def decrement_brightness():
    pthub_spi.decrement_brightness()


def set_brightness(val):
    pthub_spi.set_brightness(val)


def blank_screen():
    pthub_spi.blank_screen()


def unblank_screen():
    pthub_spi.unblank_screen()


def get_brightness():
    return _state._brightness


def get_lid_open_state():
    return not _state._lid_closed


def get_screen_blanked_state():
    return _state._screen_blanked


def get_shutdown_state():
    return _state._shutdown


def get_device_id():
    return _state._device_id


def get_battery_state():
    return (
        _state._battery_charging_state,
        _state._battery_capacity,
        _state._battery_time,
        _state._battery_wattage,
    )


def shutdown():
    # v1 hub shuts down as follows: (1) OS shuts down (2) systemd service fires off
    # shutdown command to hub (3) Hub enters shutdown mode, waits for 5 seconds of
    # no comms from the pi (4) hub cuts power

    # Nothing to do here
    pass


def enable_hdmi_to_i2s_audio():
    PTLogger.warning(
        "V1 hub called to enable HDMI to I2S audio - this hub does not support this"
    )


def disable_hdmi_to_i2s_audio():
    PTLogger.warning(
        "V1 hub called to disable HDMI to I2S audio - this hub does not support this"
    )


def set_speed(no_of_polls_per_second=4):
    pthub_spi.set_speed(no_of_polls_per_second)


######################
# INTERNAL FUNCTIONS #
######################


def _start_spi():
    if pthub_spi.is_initialised():
        pthub_spi.start()
    else:
        PTLogger.error("SPI is not available")


def _start_i2c():
    if pthub_i2c.is_initialised():
        pthub_i2c.start()
    else:
        PTLogger.warning("I2C is not available")


def _stop_spi():
    if pthub_spi._run_main_thread:
        pthub_spi.stop()
    else:
        PTLogger.warning("Unable to stop SPI - not currently running")


def _stop_i2c():
    if pthub_i2c._run_main_thread:
        pthub_i2c.stop()
    else:
        PTLogger.warning("Unable to stop I2C - not currently running")


def _represents_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
