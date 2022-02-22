from pyee import EventEmitter


class State:
    def __init__(self):
        self.brightness = 16
        self.screen_blanked = False
        self.lid_open = True
        self.battery_charging_state = -1
        self.battery_remaining_time = -1
        self.battery_wattage = -1
        self.battery_capacity = -1
        self.buttons_route_to_gpio_enabled = False
        self.oled_is_pi_controlled = False
        self.oled_is_using_spi0 = False
        self.up_button_press_state = False
        self.down_button_press_state = False
        self.select_button_press_state = False
        self.cancel_button_press_state = False

        self.battery_capacity_override_counter = 0

        self.funcs = None
        self.ee = EventEmitter()

    def register_client(self, funcs):
        self.funcs = funcs

    def emit_battery_state_change(self):
        func = self.funcs.get("hub_battery_state")
        if callable(func):
            func(
                self.battery_charging_state,
                self.battery_capacity,
                self.battery_remaining_time,
                self.battery_wattage,
            )

    def emit_brightness_change(self):
        func = self.funcs.get("hub_brightness")
        if callable(func):
            func(self.brightness)

    def emit_oled_pi_control_state_changed(self):
        func = self.funcs.get("oled_pi_controlled_state")
        if callable(func):
            func(self.oled_is_pi_controlled)

    def emit_oled_spi_bus_state_changed(self):
        self.ee.emit("SPI_BUS_CHANGED", 0 if self.oled_is_using_spi0 else 1)

        func = self.funcs.get("oled_spi_state")
        if callable(func):
            func(self.oled_is_using_spi0)

    def emit_buttons_route_to_gpio_state_changed(self):
        func = self.funcs.get("buttons_route_to_gpio")
        if callable(func):
            func(self.buttons_route_to_gpio_enabled)

    def emit_screen_blanked(self):
        func = self.funcs.get("screen_blank_state")
        if callable(func):
            func(True)

    def emit_screen_unblanked(self):
        func = self.funcs.get("screen_blank_state")
        if callable(func):
            func(False)

    def emit_lid_opened(self):
        func = self.funcs.get("lid_open_state")
        if callable(func):
            func(True)

    def emit_lid_closed(self):
        func = self.funcs.get("lid_open_state")
        if callable(func):
            func(False)

    def emit_shutdown(self):
        func = self.funcs.get("hub_shutdown_requested")
        if callable(func):
            func()

    def emit_up_button_state_changed(self):
        func = self.funcs.get("button_press_state")
        if callable(func):
            func("Up", self.up_button_press_state)

    def emit_down_button_state_changed(self):
        func = self.funcs.get("button_press_state")
        if callable(func):
            func("Down", self.down_button_press_state)

    def emit_select_button_state_changed(self):
        func = self.funcs.get("button_press_state")
        if callable(func):
            func("Select", self.select_button_press_state)

    def emit_cancel_button_state_changed(self):
        func = self.funcs.get("button_press_state")
        if callable(func):
            func("Cancel", self.cancel_button_press_state)

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

    def set_buttons_route_to_gpio_state(self, buttons_route_to_gpio_enabled):
        if self.buttons_route_to_gpio_enabled is not buttons_route_to_gpio_enabled:
            self.buttons_route_to_gpio_enabled = buttons_route_to_gpio_enabled
            self.emit_buttons_route_to_gpio_state_changed()

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
