#!/usr/bin/env python

from pitop.utils.logger import PTLogger
from .pthub2_state import State
from .pthub2_connection import HubConnection
from pitop.utils.common_ids import DeviceID


def initialise():
    global _state
    global _hub_connection

    _state = State()
    _hub_connection = HubConnection()

    PTLogger.info("Initialising I2C connection...")

    if _hub_connection.initialise(_state) is False:
        PTLogger.warning("Unable to detect pi-topHUB v2 connection")
        return False

    PTLogger.info("Initialised")

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
    PTLogger.debug("Hub connection loop starting...")
    _hub_connection.start()
    PTLogger.info("Hub connection loop started")


def stop():
    PTLogger.debug("Hub connection loop stopping...")
    _hub_connection.stop()
    PTLogger.info("Hub connection loop stopped")


def increment_brightness():
    _hub_connection.increment_brightness()


def decrement_brightness():
    _hub_connection.decrement_brightness()


def set_brightness(val):
    _hub_connection.set_brightness(val)


def blank_screen():
    _hub_connection.blank_screen()


def unblank_screen():
    _hub_connection.unblank_screen()


def shutdown():
    _hub_connection.shutdown()


def get_brightness():
    return _state.brightness


def get_lid_open_state():
    return _state.lid_open


def get_screen_blanked_state():
    return _state.screen_blanked


# Deprecated
def get_screen_off_state():
    return _state.screen_blanked


def get_device_id():
    return DeviceID.pi_top_3


def get_battery_state():
    return (
        _state.battery_charging_state,
        _state.battery_capacity,
        _state.battery_time,
        _state.battery_wattage,
    )


def get_battery_time_state():
    return _state.battery_time


def get_battery_capacity_state():
    return _state.battery_capacity


def enable_hdmi_to_i2s_audio():
    _hub_connection.enable_hdmi_audio()


def disable_hdmi_to_i2s_audio():
    _hub_connection.disable_hdmi_audio()


def set_speed(no_of_polls_per_second=4):
    _hub_connection.set_speed(no_of_polls_per_second)
