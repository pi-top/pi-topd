from importlib import import_module

# Discovers which hub libraries are installed, and uses those to
# determine the type of hub in use and communicate with it


class HubManager():

    def initialise(self, logger, callback_client):
        self._logger = logger
        self._callback_client = callback_client
        self._active_hub_module = None

    def connect_to_hub(self):
        try:
            self._module_hub_v1 = self._import_module("pthub.pthub")

            if (self._module_hub_v1.initialise(self._logger) is True):
                self._active_hub_module = self._module_hub_v1
                self._logger.info("Connected to hub v1")
                return
            else:
                self._logger.warning("Could not initialise v1 hub")

        except Exception as e:
            self._logger.info("Failed to connect to a v1 hub. " + str(e))

        try:
            self._module_hub_v2 = self._import_module("pthubv2")

            if (self._module_hub_v2.initialise(self._logger) is True):
                self._active_hub_module = self._module_hub_v2
                self._logger.info("Connected to hub v2")
                return
            else:
                self._logger.warning("Could not initialise v2 hub")

        except Exception as e:
            self._logger.info("Failed to connect to a v2 hub. " + str(e))

        self._logger.error("Could not connect to a hub!")

    def start(self):
        self.check_hub_connected()
        self._active_hub_module.start()

    def stop(self):
        self.check_hub_connected()
        self._active_hub_module.stop()

    def register_client(self, client):
        self.check_hub_connected()
        self._active_hub_module.register_client(
            client._on_hub_brightness_changed,
            client._on_screen_blank_state_changed,
            client._on_hub_shutdown_requested,
            client._on_device_id_changed,
            client._on_hub_battery_charging_state_changed,
            client._on_hub_battery_capacity_changed,
            client._on_hub_battery_time_remaining_changed)

    # def set_logging(stdout, log_to_file):
    #   self.check_hub_connected()
    #   self._active_hub_module.set_logging(stdout, log_to_file)

    def set_speed(self, no_of_polls_per_second):
        self.check_hub_connected()
        self._active_hub_module.set_speed(no_of_polls_per_second)

    def get_brightness(self):
        self.check_hub_connected()
        return self._active_hub_module.get_brightness()

    def get_screen_off_state(self):
        self.check_hub_connected()
        return self._active_hub_module.get_screen_off_state()

    def get_shutdown_state(self):
        self.check_hub_connected()
        return self._active_hub_module.get_shutdown_state()

    def get_device_id(self):
        self.check_hub_connected()
        return self._active_hub_module.get_device_id()

    def get_battery_charging_state(self):
        self.check_hub_connected()
        return self._active_hub_module.get_battery_charging_state()

    def get_battery_time_state(self):
        self.check_hub_connected()
        return self._active_hub_module.get_battery_time_state()

    def get_battery_capacity_state(self):
        self.check_hub_connected()
        return self._active_hub_module.get_battery_capacity_state()

    def set_brightness(self, brightness):
        self.check_hub_connected()
        self._active_hub_module.set_brightness(brightness)

    def increment_brightness(self):
        self.check_hub_connected()
        self._active_hub_module.increment_brightness()

    def decrement_brightness(self):
        self.check_hub_connected()
        self._active_hub_module.decrement_brightness()

    def blank_screen(self):
        self.check_hub_connected()
        self._active_hub_module.blank_screen()

    def unblank_screen(self):
        self.check_hub_connected()
        self._active_hub_module.unblank_screen()

    def check_hub_connected(self):
        if (self._active_hub_module is None):
            raise RuntimeError("No hub connected")

    def _import_module(self, module_name):
        try:
            return import_module(module_name)

        except ImportError as e:
            print("Failed to import " + module_name + ". Error: " + str(e))
            raise e
