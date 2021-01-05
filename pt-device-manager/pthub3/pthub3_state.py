class State:
    def __init__(self):
        self.brightness = 16
        self.screen_blanked = False
        self.external_display_connected = False
        self.native_display_connected = False
        self.lid_open = True
        self.battery_charging_state = -1
        self.battery_remaining_time = -1
        self.battery_wattage = -1
        self.battery_capacity = -1
        self.button_direct_gpio_enabled = False
        self.oled_is_pi_controlled = False
        self.oled_is_using_spi0 = False
        self.up_button_press_state = False
        self.down_button_press_state = False
        self.select_button_press_state = False
        self.cancel_button_press_state = False

        self.battery_capacity_override_counter = 0

        self._brightness_change_func = None
        self._screen_blank_state_change_func = None
        self._native_display_connect_state_changed_func = None
        self._external_display_connect_state_changed_func = None
        self._lid_open_state_change_func = None
        self._shutdown_func = None
        self._battery_state_change_func = None
        self._button_press_state_changed_func = None
        self._oled_pi_controlled_state_change_func = None
        self._oled_spi_state_change_func = None
        self._direct_button_gpio_state_change_func = None

    def register_client(self,
                        on_brightness_changed_func=None,
                        on_screen_blank_state_change_func=None,
                        on_native_display_connect_state_changed_func=None,
                        on_external_display_connect_state_changed_func=None,
                        on_lid_open_state_change_func=None,
                        on_shutdown_requested_func=None,
                        on_battery_state_changed_func=None,
                        on_button_press_state_changed_func=None,
                        on_oled_pi_controlled_state_change_func=None,
                        on_oled_spi_state_change_func=None,
                        on_direct_button_gpio_state_change_func=None
                        ):
        self._brightness_change_func = on_brightness_changed_func
        self._screen_blank_state_change_func = on_screen_blank_state_change_func
        self._native_display_connect_state_changed_func = on_native_display_connect_state_changed_func
        self._external_display_connect_state_changed_func = on_external_display_connect_state_changed_func
        self._lid_open_state_change_func = on_lid_open_state_change_func
        self._shutdown_func = on_shutdown_requested_func
        self._battery_state_change_func = on_battery_state_changed_func
        self._button_press_state_changed_func = on_button_press_state_changed_func
        self._oled_pi_controlled_state_change_func = on_oled_pi_controlled_state_change_func
        self._oled_spi_state_change_func = on_oled_spi_state_change_func
        self._direct_button_gpio_state_change_func = on_direct_button_gpio_state_change_func

    def emit_battery_state_change(self):
        if callable(self._battery_state_change_func):
            self._battery_state_change_func(self.battery_charging_state, self.battery_capacity, self.battery_remaining_time,
                                            self.battery_wattage)

    def emit_brightness_change(self):
        if callable(self._brightness_change_func):
            self._brightness_change_func(self.brightness)

    def emit_oled_pi_control_state_changed(self):
        if callable(self._oled_pi_controlled_state_change_func):
            self._oled_pi_controlled_state_change_func(
                self.oled_is_pi_controlled)

    def emit_oled_spi_bus_state_changed(self):
        if callable(self._oled_spi_state_change_func):
            self._oled_spi_state_change_func(
                self.oled_is_using_spi0)

    def emit_button_direct_gpio_state_changed(self):
        if callable(self._direct_button_gpio_state_change_func):
            self._direct_button_gpio_state_change_func(
                self.button_direct_gpio_enabled)

    def emit_external_display_connected(self):
        if callable(self._external_display_connect_state_changed_func):
            self._external_display_connect_state_changed_func(True)

    def emit_external_display_disconnected(self):
        if callable(self._external_display_connect_state_changed_func):
            self._external_display_connect_state_changed_func(False)

    def emit_native_display_connected(self):
        if callable(self._native_display_connect_state_changed_func):
            self._native_display_connect_state_changed_func(True)

    def emit_native_display_disconnected(self):
        if callable(self._native_display_connect_state_changed_func):
            self._native_display_connect_state_changed_func(False)

    def emit_screen_blanked(self):
        if callable(self._screen_blank_state_change_func):
            self._screen_blank_state_change_func(True)

    def emit_screen_unblanked(self):
        if callable(self._screen_blank_state_change_func):
            self._screen_blank_state_change_func(False)

    def emit_lid_opened(self):
        if callable(self._lid_open_state_change_func):
            self._lid_open_state_change_func(True)

    def emit_lid_closed(self):
        if callable(self._lid_open_state_change_func):
            self._lid_open_state_change_func(False)

    def emit_shutdown(self):
        if callable(self._shutdown_func):
            self._shutdown_func()

    def emit_up_button_state_changed(self):
        if callable(self._button_press_state_changed_func):
            self._button_press_state_changed_func(
                "Up", self.up_button_press_state)

    def emit_down_button_state_changed(self):
        if callable(self._button_press_state_changed_func):
            self._button_press_state_changed_func(
                "Down", self.down_button_press_state)

    def emit_select_button_state_changed(self):
        if callable(self._button_press_state_changed_func):
            self._button_press_state_changed_func(
                "Select", self.select_button_press_state)

    def emit_cancel_button_state_changed(self):
        if callable(self._button_press_state_changed_func):
            self._button_press_state_changed_func(
                "Cancel", self.cancel_button_press_state)

    def set_battery_state(self, charging_state, capacity, remaining_time, wattage):
        state_changed = False

        if self.battery_charging_state != charging_state:
            state_changed = True
            self.battery_charging_state = charging_state

        if self.battery_capacity != capacity:
            state_changed = True
            self.battery_capacity = capacity

        if self.battery_remaining_time != remaining_time:
            state_changed = True
            self.battery_remaining_time = remaining_time

        if self.battery_wattage != wattage:
            state_changed = True
            self.battery_wattage = wattage

        if state_changed:
            self.emit_battery_state_change()

    def set_brightness(self, value):
        if self.brightness != value:
            self.brightness = value
            self.emit_brightness_change()

    def set_external_display_connected(self):
        if self.external_display_connected is False:
            self.external_display_connected = True
            self.emit_external_display_connected()

    def set_external_display_disconnected(self):
        if self.external_display_connected is True:
            self.external_display_connected = False
            self.emit_external_display_disconnected()

    def set_native_display_connected(self):
        if self.native_display_connected is False:
            self.native_display_connected = True
            self.emit_native_display_connected()

    def set_native_display_disconnected(self):
        if self.native_display_connected is True:
            self.native_display_connected = False
            self.emit_native_display_disconnected()

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

    def set_button_direct_gpio_state(self, button_direct_gpio_enabled):
        if self.button_direct_gpio_enabled is not button_direct_gpio_enabled:
            self.button_direct_gpio_enabled = button_direct_gpio_enabled
            self.emit_button_direct_gpio_state_changed()

    def set_oled_controller(self, is_pi_controlled):
        if self.oled_is_pi_controlled is not is_pi_controlled:
            self.oled_is_pi_controlled = is_pi_controlled
            self.emit_oled_pi_control_state_changed()

    def set_oled_using_spi0_state(self, is_using_spi0):
        if self.oled_is_using_spi0 is not is_using_spi0:
            self.oled_is_using_spi0 = is_using_spi0
            self.emit_oled_spi_bus_state_changed()

    def set_up_button_press_state(self, is_pressed):
        if self.up_button_press_state is not is_pressed:
            self.up_button_press_state = is_pressed
            self.emit_up_button_state_changed()

    def set_down_button_press_state(self, is_pressed):
        if self.down_button_press_state is not is_pressed:
            self.down_button_press_state = is_pressed
            self.emit_down_button_state_changed()

    def set_select_button_press_state(self, is_pressed):
        if self.select_button_press_state is not is_pressed:
            self.select_button_press_state = is_pressed
            self.emit_select_button_state_changed()

    def set_cancel_button_press_state(self, is_pressed):
        if self.cancel_button_press_state is not is_pressed:
            self.cancel_button_press_state = is_pressed
            self.emit_cancel_button_state_changed()
