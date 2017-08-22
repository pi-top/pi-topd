
# Handles safe shutdown when the hub is communicating that its battery capacity is below a threshold set by ptdm_controller

from os import system


class Counter:
    """A simple counter class"""

    def __init__(self, max, current=0):
        self._current = current
        self._max = max

    def increment(self):
        if self._current < self._max:
            self._current += 1
            return True
        else:
            return False

    def reset(self):
        self._current = 0

    def maxed(self):
        return (self._current == self._max)


class ShutdownManager:
    pi_top_device_id = 2
    warning_battery_level = 5
    critical_battery_level = 3
    shutdown_warning_ctr = Counter(3)
    shutdown_critical_ctr = Counter(3)
    shown_shutdown_warning = False

    def __init__(self):
        self.battery_capacity = None
        self.battery_charging = None
        self.device_id = None

    def set_battery_capacity(self, new_value):
        self.battery_capacity = new_value

    def set_battery_charging(self, new_value):
        self.battery_charging = new_value

    def set_device_id(self, new_value):
        self.device_id = new_value

    def get_battery_capacity(self):
        return self.battery_capacity

    def get_battery_charging(self):
        return self.battery_charging

    def get_device_id(self):
        return self.device_id

    def device_is_pi_top(self):
        return (self.get_device_id() == self.pi_top_device_id)

    def battery_state_fully_defined(self):
        capacity_defined = (self.battery_capacity is not None)
        charging_defined = (self.battery_charging is not None)

        return (capacity_defined and charging_defined)

    def reset_counters(self):
        self.shutdown_warning_ctr.reset()
        self.shutdown_critical_ctr.reset()

    def update_counters_from_battery_state(self):
        under_critical_threshold = (self.battery_capacity <= self.critical_battery_level)
        under_warning_threshold = (self.battery_capacity <= self.warning_battery_level)

        if under_critical_threshold:
            self.shutdown_critical_ctr.increment()
        elif under_warning_threshold:
            self.shutdown_warning_ctr.increment()
        else:
            self.reset_counters()

    def process_battery_state(self):
        reset_ctrs = True
        # Is this necessary? Non-'pi-top' device would not be emitting battery events
        if self.device_is_pi_top():
            if self.battery_state_fully_defined():

                discharging = (self.battery_charging != "charging")
                if discharging:
                    self.update_counters_from_battery_state()
                    reset_ctrs = False

        if reset_ctrs:
            self.reset_counters()
            self.shown_shutdown_warning = False  # Need to be able to send warning messages again once the battery state is determined to be safe again
        else:
            if self.shutdown_critical_ctr.maxed():
                self.shutdown()
            elif self.shutdown_warning_ctr.maxed() and not self.shown_shutdown_warning:
                # show warning
                print("WARNING")
                self.shown_shutdown_warning = True

    def shutdown(self):
        system("shutdown -h now")
