
# Handles safe shutdown when the hub is communicating that its battery capacity is below a threshold set by ptdm_controller

from ptcommon.logger import PTLogger
from ptcommon import common_ids
from ptcommon import counter as c
from os import system


class ShutdownManager:
    warning_battery_level = 5
    warning_battery_ctr = c.Counter(3)

    critical_battery_level = 3
    critical_battery_ctr = c.Counter(3)

    shutdown_battery_level = 2
    shutdown_battery_ctr = c.Counter(3)

    shown_warning_battery_message = False
    shown_critical_battery_message = False
    shutdown_initiated = False

    def __init__(self):
        self._callback = None
        self._battery_capacity = None
        self._battery_charging = None

        self._device_id = common_ids.DeviceID.not_yet_known

    def initialise(self, callback):
        self._callback = callback

    def set_battery_capacity(self, new_value):
        self._battery_capacity = new_value

    def set_battery_charging(self, new_value):
        self._battery_charging = new_value

    def set_device_id(self, new_value):

        device_id_already_established = (self._device_id != common_ids.DeviceID.not_yet_known and self._device_id != common_ids.DeviceID.unknown)
        device_id_changing = (self._device_id != new_value)

        if (device_id_already_established is False):
            self._device_id = new_value

        elif (device_id_changing is True):
            PTLogger.warning("The device id has changed! This is likely due to moving an SD card between different devices. Rebooting to re-initialise...")
            self.reboot()

    def get_battery_capacity(self):
        return self._battery_capacity

    def get_battery_charging(self):
        return self._battery_charging

    def device_has_battery(self):
        return (self._device_id == common_ids.DeviceID.pi_top or
                self._device_id == common_ids.DeviceID.pi_top_v2)

    def battery_state_fully_defined(self):
        capacity_defined = (self._battery_capacity is not None)
        charging_defined = (self._battery_charging is not None)

        return (capacity_defined and charging_defined)

    def reset_counters(self):
        self.warning_battery_ctr.reset()
        self.critical_battery_ctr.reset()
        self.shutdown_battery_ctr.reset()

    def update_counters_from_battery_state(self):
        under_shutdown_threshold = (self._battery_capacity <= self.shutdown_battery_level)
        under_critical_threshold = (self._battery_capacity <= self.critical_battery_level)
        under_warning_threshold = (self._battery_capacity <= self.warning_battery_level)

        if under_shutdown_threshold:
            self.shutdown_battery_ctr.increment()
            if (self.shutdown_initiated is False):
                PTLogger.info("Battery: shutdown threshold reached " + str(self.shutdown_battery_ctr._current) + " of " + str(self.shutdown_battery_ctr._max))
        else:
            self.shutdown_battery_ctr.reset()

        if under_critical_threshold:
            self.critical_battery_ctr.increment()
            if (self.shown_critical_battery_message is False):
                PTLogger.info("Battery: critical threshold reached " + str(self.critical_battery_ctr._current) + " of " + str(self.critical_battery_ctr._max))
        else:
            self.critical_battery_ctr.reset()

        if under_warning_threshold:
            self.warning_battery_ctr.increment()
            if (self.shown_warning_battery_message is False):
                PTLogger.info("Battery: warning threshold reached " + str(self.warning_battery_ctr._current) + " of " + str(self.warning_battery_ctr._max))
        else:
            self.warning_battery_ctr.reset()

    def process_battery_state(self):
        reset_ctrs = True

        if self.device_has_battery():
            if self.battery_state_fully_defined():

                # If the battery has not been removed altogther and the battery is not being charged, then evaluate
                # whether we want to show warning messages or shutdown

                battery_removed = (self._battery_capacity == 0)

                if (battery_removed is False and self._battery_charging == 0):
                    self.update_counters_from_battery_state()
                    reset_ctrs = False

        if reset_ctrs:
            self.reset_counters()
            # Need to be able to send warning messages again once the battery state is determined to be safe again
            self.shown_warning_battery_message = False
            self.shown_critical_battery_message = False
        else:
            if self.shutdown_battery_ctr.maxed() and not self.shutdown_initiated:
                self.shutdown()
            elif self.critical_battery_ctr.maxed() and not self.shown_critical_battery_message:
                self._callback._on_critical_battery_warning()
                self.shown_critical_battery_message = True
            elif self.warning_battery_ctr.maxed() and not self.shown_warning_battery_message:
                self._callback._on_low_battery_warning()
                self.shown_warning_battery_message = True

    def shutdown(self):
        if (self.shutdown_initiated is True):
            PTLogger.warning("Shutdown already initiated")
            return

        PTLogger.info("Shutting down OS...")
        system("shutdown -h now")
        self.shutdown_initiated = True
        PTLogger.info("OS shutdown command issued")

    def reboot(self):
        PTLogger.info("Rebooting OS")
        system("reboot")
        PTLogger.info("OS reboot command issued")
