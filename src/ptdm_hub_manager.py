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
            self._module_hub_v1 = self._import_module("pthub")

            if (self._module_hub_v1.initialise() is True):
                self._active_hub_module = self._module_hub_v1
                self._logger.info("Connected to hub v1")
                return

        except Exception as e:
            self._logger.info("Failed to connect to a v1 hub")

        try:
            self._module_hub_v2 = self._import_module("pthubv2")

            if (self._module_hub_v2.initialise() is True):
                self._active_hub_module = self._module_hub_v2
                self._logger.info("Connected to hub v2")

                return

        except Exception as e:
            self._logger.info("Failed to connect to a v2 hub")

        self._logger.error("Could not connect to a hub!")

    def start():
        _throw_error_if_hub_is_not_active()
        self._module_hub_v1.start()

    def stop():
        _throw_error_if_hub_is_not_active()
        self._module_hub_v1.stop()

    def register_client(controller_obj):
        _throw_error_if_hub_is_not_active()
        self._active_hub_module.register_client(
            controller_obj._on_hub_brightness_changed,
            controller_obj._on_screen_blank_state_changed,
            controller_obj._on_hub_shutdown_requested,
            controller_obj._on_device_name_changed,
            controller_obj._on_hub_battery_charging_state_changed,
            controller_obj._on_hub_battery_capacity_changed,
            controller_obj._on_hub_battery_time_remaining_changed
        )

    # def set_logging(stdout, log_to_file):
    #   _throw_error_if_hub_is_not_active()
    #   self._active_hub_module.set_logging(stdout, log_to_file)

    def set_speed(no_of_polls_per_second):
        _throw_error_if_hub_is_not_active()
        self._active_hub_module.set_speed(no_of_polls_per_second)

    def get_brightness(self):
        _throw_error_if_hub_is_not_active()
        return self._active_hub_module.get_brightness()

    def get_screen_off_state(self):
        _throw_error_if_hub_is_not_active()
        return self._active_hub_module.get_screen_off_state()

    def get_shutdown_state(self):
        _throw_error_if_hub_is_not_active()
        return self._active_hub_module.get_shutdown_state()

    def get_device_name(self):
        _throw_error_if_hub_is_not_active()
        return self._active_hub_module.get_device_name()

    def get_battery_charging_state(self):
        _throw_error_if_hub_is_not_active()
        return self._active_hub_module.get_battery_charging_state()

    def get_battery_time_state(self):
        _throw_error_if_hub_is_not_active()
        return self._active_hub_module.get_battery_time_state()

    def get_battery_capacity_state(self):
        _throw_error_if_hub_is_not_active()
        return self._active_hub_module.get_battery_capacity_state()

    def set_brightness(self, brightness):
        _throw_error_if_hub_is_not_active()
        self._active_hub_module.set_brightness(brightness)

    def increment_brightness(self):
        _throw_error_if_hub_is_not_active()
        self._active_hub_module.increment_brightness()

    def decrement_brightness(self):
        _throw_error_if_hub_is_not_active()
        self._active_hub_module.decrement_brightness()

    def blank_screen(self):
        _throw_error_if_hub_is_not_active()
        self._active_hub_module.blank_screen()

    def unblank_screen(self):
        _throw_error_if_hub_is_not_active()
        self._active_hub_module.unblank_screen()

    def _throw_error_if_hub_is_not_active(self):
        if (self._active_hub_module is None):
            raise RuntimeError("No hub connected")

    def _import_module(self, module_name):
        try:
            module_config_name = str(module_name + ".configuration")
            return import_module(module_config_name)

        except ImportError as e:
            print("Failed to import " + module_name + ". Error: " + str(e))
            raise e
