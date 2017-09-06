from importlib import import_module
import traceback

# Discovers which hub libraries are installed, and uses those to
# determine the type of hub in use and communicate with it


class HubManager():

    def initialise(self, logger, callback_client):
        self._logger = logger
        self._callback_client = callback_client
        self._active_hub_module = None

    def connect_to_hub(self):

        self._logger.info("Attempting to find pi-topHUB v1...")

        try:
            self._module_hub_v1 = self._import_module("pthub.pthub")

            if (self._module_hub_v1.initialise(self._logger) is True):
                self._active_hub_module = self._module_hub_v1
                self._logger.info("Connected to hub v1")
                return True
            else:
                self._logger.warning("Could not initialise v1 hub")

        except Exception as e:
            self._logger.warning("Failed to connect to a v1 hub. " + str(e))
            self._logger.info(traceback.format_exc())

        self._logger.info("Attempting to find pi-topHUB v2...")

        try:
            self._module_hub_v2 = self._import_module("pthub2.pthub2")

            if (self._module_hub_v2.initialise(self._logger) is True):
                self._active_hub_module = self._module_hub_v2
                self._logger.info("Connected to hub v2")
                return True
            else:
                self._logger.warning("Could not initialise v2 hub")

        except Exception as e:
            self._logger.warning("Failed to connect to a v2 hub. " + str(e))
            self._logger.info(traceback.format_exc())

        self._logger.error("Could not connect to a hub!")
        return False

    def start(self):
        if (self._hub_connected()):
            self._active_hub_module.start()

    def stop(self):
        if (self._hub_connected()):
            self._active_hub_module.stop()

    def register_client(self, client):
        if (self._hub_connected()):
            self._active_hub_module.register_client(
                client._on_hub_brightness_changed,
                client._on_screen_blanked,
                client._on_screen_unblanked,
                client._on_lid_opened,
                client._on_lid_closed,
                client._on_hub_shutdown_requested,
                client._on_device_id_changed,
                client._on_hub_battery_state_changed)

    def set_speed(self, no_of_polls_per_second):
        if (self._hub_connected()):
            self._active_hub_module.set_speed(no_of_polls_per_second)

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

    def get_battery_capacity_state(self):
        if (self._hub_connected()):
            return self._active_hub_module.get_battery_capacity_state()

    def set_brightness(self, brightness):
        if (self._hub_connected()):
            self._active_hub_module.set_brightness(brightness)

    def increment_brightness(self):
        if (self._hub_connected()):
            self._active_hub_module.increment_brightness()

    def decrement_brightness(self):
        if (self._hub_connected()):
            self._active_hub_module.decrement_brightness()

    def blank_screen(self):
        if (self._hub_connected()):
            self._active_hub_module.blank_screen()

    def unblank_screen(self):
        if (self._hub_connected()):
            self._active_hub_module.unblank_screen()

    def _hub_connected(self):
        return (self._active_hub_module is not None)

    def _import_module(self, module_name):
        try:
            return import_module(module_name)

        except ImportError as e:
            print("Failed to import " + module_name + ". Error: " + str(e))
            raise e
