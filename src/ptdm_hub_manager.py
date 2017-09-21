from importlib import import_module
import traceback
from ptcommon import common_ids
from time import sleep

# Discovers which hub libraries are installed, and uses those to
# determine the type of hub in use and communicate with it


class HubManager():

    def initialise(self, logger, callback_client):
        self._logger = logger
        self._callback_client = callback_client
        self._active_hub_module = None

    def connect_to_hub(self):

        # Attempt to connect to a v2 hub first. This is because we can
        # positively identify v2 on i2c. We can also positively identify
        # a v1 pi-top, however we cannot do this for a CEED. Hence this
        # is the fall-through case.

        self._logger.info("Attempting to find pi-topHUB v2...")

        try:
            self._module_hub_v2 = self._import_module("pthub2.pthub2")

            if (self._module_hub_v2.initialise(self._logger) is True):
                self._active_hub_module = self._module_hub_v2
                self._logger.info("Connected to hub v2")
                self._register_client()
                return True
            else:
                self._logger.warning("Could not initialise v2 hub")

        except Exception as e:
            self._logger.warning("Failed to connect to a v2 hub. " + str(e))
            self._logger.info(traceback.format_exc())

        self._logger.info("Attempting to find pi-topHUB v1...")

        try:
            self._module_hub_v1 = self._import_module("pthub.pthub")

            if (self._module_hub_v1.initialise(self._logger) is True):
                self._active_hub_module = self._module_hub_v1
                self._logger.info("Connected to hub v1")
                self._register_client()
                return True
            else:
                self._logger.warning("Could not initialise v1 hub")

        except Exception as e:
            self._logger.warning("Failed to connect to a v1 hub. " + str(e))
            self._logger.info(traceback.format_exc())

        self._logger.error("Could not connect to a hub!")
        return False

    def start(self):
        if (self._hub_connected()):
            self._active_hub_module.start()

    def stop(self):

        # When stopping, we unblank the screen and set the brightness to full
        # to prevent restarting with no display

        self._logger.info("Stopping hub manager...")

        if (self._hub_connected()):
            self._active_hub_module.stop()
            self.unblank_screen()

    def wait_for_device_id(self):

        self._logger.info("Waiting for device id to be established...")
        time_waited = 0
        while (time_waited < 5):

            device_id = self._active_hub_module.get_device_id()
            if (device_id != common_ids.DeviceID.not_yet_known):

                self._logger.info("Got device id (" + str(self._active_hub_module.get_device_id()) + "). Waited " + str(time_waited) + " seconds")
                return
            else:
                sleep(0.25)
                time_waited += 0.25

        self._logger.info("Timed out waiting for device id.")

    def get_device_id(self):
        if (self._hub_connected()):
            return self._active_hub_module.get_device_id()

    def get_brightness(self):
        if (self._hub_connected()):
            return self._active_hub_module.get_brightness()

    def get_screen_off_state(self):
        if (self._hub_connected()):
            return self._active_hub_module.get_screen_off_state()

    def get_shutdown_state(self):
        if (self._hub_connected()):
            return self._active_hub_module.get_shutdown_state()

    def get_device_id(self):
        if (self._hub_connected()):
            return self._active_hub_module.get_device_id()

    def get_battery_charging_state(self):
        if (self._hub_connected()):
            return self._active_hub_module.get_battery_charging_state()

    def get_battery_time_state(self):
        if (self._hub_connected()):
            return self._active_hub_module.get_battery_time_state()

    def get_battery_state(self):
        if (self._hub_connected()):
            return self._active_hub_module.get_battery_state()

    def set_brightness(self, brightness):
        self._logger.info("Setting brightness to " + str(brightness))
        if (self._hub_connected()):
            self._active_hub_module.set_brightness(brightness)

    def increment_brightness(self):
        self._logger.info("Incrementing brightness")
        if (self._hub_connected()):
            self._active_hub_module.increment_brightness()

    def decrement_brightness(self):
        self._logger.info("Decrementing brightness")
        if (self._hub_connected()):
            self._active_hub_module.decrement_brightness()

    def blank_screen(self):
        self._logger.info("Blanking screen")
        if (self._hub_connected()):
            self._active_hub_module.blank_screen()

    def unblank_screen(self):
        self._logger.info("Unblanking screen")
        if (self._hub_connected()):
            self._active_hub_module.unblank_screen()

    def shutdown(self):
        self._logger.info("Shutting down")
        if (self._hub_connected()):
            self._active_hub_module.shutdown()

    def _hub_connected(self):
        return (self._active_hub_module is not None)

    def _import_module(self, module_name):
        try:
            return import_module(module_name)

        except ImportError as e:
            print("Failed to import " + module_name + ". Error: " + str(e))
            raise e

    def _register_client(self):
        if (self._hub_connected()):
            self._active_hub_module.register_client(
                self._callback_client._on_hub_brightness_changed,
                self._callback_client._on_screen_blanked,
                self._callback_client._on_screen_unblanked,
                self._callback_client._on_lid_opened,
                self._callback_client._on_lid_closed,
                self._callback_client._on_hub_shutdown_requested,
                self._callback_client._on_device_id_changed,
                self._callback_client._on_hub_battery_state_changed)
