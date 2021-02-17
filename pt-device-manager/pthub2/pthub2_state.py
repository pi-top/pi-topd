class State:
    def __init__(self):

        self.brightness = 16
        self.screen_blanked = False
        self.lid_open = True
        self.battery_charging_state = -1
        self.battery_time = -1
        self.battery_wattage = -1
        self.battery_capacity = -1

        self.battery_capacity_override_counter = 0

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

    def emit_battery_charging_state_change(self):
        if callable(self._battery_state_change_func):
            self._battery_state_change_func(
                self.battery_charging_state,
                self.battery_capacity,
                self.battery_time,
                self.battery_wattage,
            )

    def emit_battery_capacity_change(self):
        if callable(self._battery_state_change_func):
            self._battery_state_change_func(
                self.battery_charging_state,
                self.battery_capacity,
                self.battery_time,
                self.battery_wattage,
            )

    def emit_battery_time_change(self):
        if callable(self._battery_state_change_func):
            self._battery_state_change_func(
                self.battery_charging_state,
                self.battery_capacity,
                self.battery_time,
                self.battery_wattage,
            )

    def emit_battery_wattage_change(self):
        if callable(self._battery_state_change_func):
            self._battery_state_change_func(
                self.battery_charging_state,
                self.battery_capacity,
                self.battery_time,
                self.battery_wattage,
            )

    def emit_brightness_change(self):
        if callable(self._brightness_change_func):
            self._brightness_change_func(self.brightness)

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

    def set_battery_charging_state(self, value):
        if self.battery_charging_state != value:
            self.battery_charging_state = value
            self.emit_battery_charging_state_change()

    def set_battery_capacity(self, value):
        if self.battery_capacity != value:
            self.battery_capacity = value
            self.emit_battery_capacity_change()

    def set_battery_time(self, value):
        if self.battery_time != value:
            self.battery_time = value
            self.emit_battery_time_change()

    def set_battery_wattage(self, value):
        if self.battery_wattage != value:
            self.battery_wattage = value
            self.emit_battery_wattage_change()

    def set_brightness(self, value):
        if self.brightness != value:
            self.brightness = value
            self.emit_brightness_change()

    def set_screen_blanked(self):
        if self.screen_blanked is False:
            self.screen_blanked = True
            self.emit_screen_blanked()

    def set_screen_unblanked(self):
        if self.screen_blanked is True:
            self.screen_blanked = False
            self.emit_screen_unblanked()

    def set_lid_open(self):
        if self.lid_open is False:
            self.lid_open = True
            self.emit_lid_opened()

    def set_lid_closed(self):
        if self.lid_open is True:
            self.lid_open = False
            self.emit_lid_closed()
