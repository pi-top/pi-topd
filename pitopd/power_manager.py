import logging
from subprocess import run

from pitop.common.common_ids import DeviceID
from pitop.common.counter import Counter

from . import state
from .utils import get_project_root

logger = logging.getLogger(__name__)


# Handles safe shutdown when the hub is communicating
# that its battery capacity is below a threshold set by ptdm_controller
class PowerManager:
    no_of_sequential_reads_to_verify = 5

    warning_battery_level = 5
    warning_battery_ctr = Counter(no_of_sequential_reads_to_verify)

    critical_battery_level = 3
    critical_battery_ctr = Counter(no_of_sequential_reads_to_verify)

    shutdown_battery_level = 2
    shutdown_battery_ctr = Counter(no_of_sequential_reads_to_verify)

    shown_warning_battery_message = False
    shown_critical_battery_message = False
    shutdown_initiated = False

    def __init__(self):
        self._callback = None
        self._battery_capacity = -1
        self._battery_charging = -1

        self._device_id = DeviceID.unknown

    def initialise(self, callback):
        self._callback = callback

    def set_battery_capacity(self, new_value):
        self._battery_capacity = new_value

    def play_battery_charging_state_change_sound(self, is_now_charging):
        # Only play sound if desired
        if state.get("sound", "charging_sound", fallback="true") == "false":
            return

        file_prefix = "" if is_now_charging else "dis"
        run(
            [
                "omxplayer",
                "--no-keys",
                "--vol",
                "-1500",
                "-o",
                "local",
                f"{get_project_root()}/assets/charger-{file_prefix}connected.mp3",
            ]
        )

    def set_battery_charging(self, new_value):
        previous_value = self._battery_charging
        self._battery_charging = new_value

        # Don't play sound if this is the first time getting the state
        if previous_value == -1:
            return

        # Only play sound if the state has changed
        # if new_value != previous_value:
        #     self.play_battery_charging_state_change_sound(new_value)

    def set_device_id(self, new_value):
        self._device_id = new_value

    def get_battery_capacity(self):
        return self._battery_capacity

    def get_battery_charging(self):
        return self._battery_charging

    def device_has_battery(self):
        return (
            self._device_id == DeviceID.pi_top
            or self._device_id == DeviceID.pi_top_3
            or self._device_id == DeviceID.pi_top_4
        )

    def battery_state_fully_defined(self):
        capacity_defined = self._battery_capacity > -1
        charging_defined = self._battery_charging > -1

        return capacity_defined and charging_defined

    def reset_counters(self):
        self.warning_battery_ctr.reset()
        self.critical_battery_ctr.reset()
        self.shutdown_battery_ctr.reset()

    def update_counters_from_battery_state(self):
        under_shutdown_threshold = self._battery_capacity <= self.shutdown_battery_level
        under_critical_threshold = self._battery_capacity <= self.critical_battery_level
        under_warning_threshold = self._battery_capacity <= self.warning_battery_level

        if under_shutdown_threshold:
            self.shutdown_battery_ctr.increment()
            if self.shutdown_initiated is False:
                logger.info(
                    "Battery: shutdown threshold reached "
                    + str(self.shutdown_battery_ctr.current)
                    + " of "
                    + str(self.shutdown_battery_ctr.max)
                    + " (charging state: "
                    + str(self._battery_charging)
                    + ", capacity: "
                    + str(self._battery_capacity)
                    + ")"
                )
        else:
            self.shutdown_battery_ctr.reset()

        if under_critical_threshold:
            self.critical_battery_ctr.increment()
            if self.shown_critical_battery_message is False:
                logger.info(
                    "Battery: critical threshold reached "
                    + str(self.critical_battery_ctr.current)
                    + " of "
                    + str(self.critical_battery_ctr.max)
                    + " (charging state: "
                    + str(self._battery_charging)
                    + ", capacity: "
                    + str(self._battery_capacity)
                    + ")"
                )
        else:
            self.critical_battery_ctr.reset()

        if under_warning_threshold:
            self.warning_battery_ctr.increment()
            if self.shown_warning_battery_message is False:
                logger.info(
                    "Battery: warning threshold reached "
                    + str(self.warning_battery_ctr.current)
                    + " of "
                    + str(self.warning_battery_ctr.max)
                    + " (charging state: "
                    + str(self._battery_charging)
                    + ", capacity: "
                    + str(self._battery_capacity)
                    + ")"
                )
        else:
            self.warning_battery_ctr.reset()

    def process_battery_state(self):
        reset_ctrs = True

        if self.device_has_battery():
            if self.battery_state_fully_defined():
                discharging = self._battery_charging == 0

                if discharging:
                    self.update_counters_from_battery_state()
                    reset_ctrs = False

        if reset_ctrs:
            self.reset_counters()
            # Need to be able to send warning messages again once the battery state is determined to be safe again
            self.shown_warning_battery_message = False
            self.shown_critical_battery_message = False
            self._callback.on_clear_battery_warning()
        else:
            if self.shutdown_battery_ctr.maxed() and not self.shutdown_initiated:
                self.shutdown()
            elif (
                self.critical_battery_ctr.maxed()
                and not self.shown_critical_battery_message
            ):
                self._callback.on_critical_battery_warning()
                self.shown_critical_battery_message = True
            elif (
                self.warning_battery_ctr.maxed()
                and not self.shown_warning_battery_message
            ):
                self._callback.on_low_battery_warning()
                self.shown_warning_battery_message = True

    def shutdown(self):
        if self.shutdown_initiated is True:
            logger.warning("Shutdown already initiated")
            return

        logger.info("Shutting down OS...")

        run(["shutdown", "-h", "now"])
        self.shutdown_initiated = True
        logger.info("OS shutdown command issued")

    def reboot(self):
        logger.info("Rebooting OS")

        run("reboot")
        logger.info("OS reboot command issued")
