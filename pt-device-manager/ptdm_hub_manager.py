from pitopcommon.common_ids import DeviceID
from pitopcommon.logger import PTLogger
from pitopcommon.command_runner import run_command

from pthub3 import pthub3
from pthub2 import pthub2
from pthub import pthub

from glob import glob
from time import sleep
from os import path
from os import remove
from json import dump as json_dump

# Determines which type of pi-top device hub (if any) is connected, and communicates with it


class HubManager:
    def __init__(self):
        self._callback_client = None
        self._active_hub_module = None

    def initialise(self, callback_client):
        self._callback_client = callback_client
        self._active_hub_module = None

    def connect_to_hub(self):

        # Enable I2C for hub checking
        run_command("raspi-config nonint do_i2c 0", timeout=3)

        # Attempt to connect to a v3 hub first, then v2, and finally v1.
        # This is because we can positively identify v2 and v3 on i2c.
        # We can also positively identify a v1 pi-top, however we cannot
        # do this for a pi-topCEED. Hence this is the fall-through case.

        PTLogger.info("Attempting to find pi-topHUB v3...")
        if pthub3.initialise() is True:
            self._active_hub_module = pthub3
            PTLogger.info("Connected to pi-topHUB v3")
            self._write_device_serial_numbers_to_file()
            self._register_client()
            return True
        else:
            PTLogger.warning("Could not initialise v3 hub")

        PTLogger.info("Attempting to find pi-topHUB v2...")
        if pthub2.initialise() is True:
            self._active_hub_module = pthub2
            PTLogger.info("Connected to pi-topHUB v2")
            self._register_client()
            return True
        else:
            PTLogger.warning("Could not initialise v2 hub")

        PTLogger.info("Attempting to find pi-topHUB v1...")
        spi_was_enabled = (len(glob("/dev/spidev0*")) > 0)
        # Enable SPI for hub checking
        if not spi_was_enabled:
            run_command("raspi-config nonint do_spi 0", timeout=3)

        if pthub.initialise() is True:
            self._active_hub_module = pthub
            PTLogger.info("Connected to pi-topHUB v1")
            self._register_client()
            return True
        else:
            PTLogger.warning("Could not initialise v1 hub")

            # Disable SPI if it was not already running
            if not spi_was_enabled:
                run_command("raspi-config nonint do_spi 1", timeout=3)

        PTLogger.error("Could not connect to a hub!")

        return False

    def start(self):
        if self._hub_connected():
            self._active_hub_module.start()
        else:
            PTLogger.warning(
                "Attempted to call start when there was no active hub")

    def stop(self):

        # When stopping, we unblank the screen and set the brightness to full
        # to prevent restarting with no display

        PTLogger.info("Stopping hub manager...")

        if self._hub_connected():
            self.unblank_screen()

            PTLogger.info("Stopping hub module...")
            self._active_hub_module.stop()

    def wait_for_device_identification(self):

        PTLogger.debug("Waiting for device id to be established...")

        time_waited = 0
        while time_waited < 5:

            device_id = self.get_device_id()
            if device_id == DeviceID.unknown:

                sleep(0.25)
                time_waited += 0.25

            else:
                PTLogger.debug(
                    "Got device id ("
                    + str(device_id)
                    + "). Waited "
                    + str(time_waited)
                    + " seconds"
                )
                return

        PTLogger.warning("Timed out waiting for device identification.")

    def get_device_id(self):
        if self._hub_connected():
            return self._active_hub_module.get_device_id()
        else:
            PTLogger.debug(
                "Attempted to call get_device_id when there was no active hub"
            )
            return DeviceID.unknown

    def get_brightness(self):
        if self._hub_connected():
            return self._active_hub_module.get_brightness()
        else:
            PTLogger.warning(
                "Attempted to call get_brightness when there was no active hub"
            )
            return None

    def get_screen_blanked_state(self):
        if self._hub_connected():
            return self._active_hub_module.get_screen_blanked_state()
        else:
            PTLogger.warning(
                "Attempted to call get_screen_blanked_state() when there was no active hub"
            )
            return None

    def get_shutdown_state(self):
        if self._hub_connected():
            return self._active_hub_module.get_shutdown_state()
        else:
            PTLogger.warning(
                "Attempted to call get_shutdown_state when there was no active hub"
            )
            return None

    def get_lid_open_state(self):
        if self._hub_connected():
            return self._active_hub_module.get_lid_open_state()
        else:
            PTLogger.warning(
                "Attempted to call get_lid_open_state when there was no active hub"
            )
            return None

    def get_battery_state(self):
        if self._hub_connected():
            return self._active_hub_module.get_battery_state()
        else:
            PTLogger.warning(
                "Attempted to call get_battery_state when there was no active hub"
            )
            return None

    def set_brightness(self, brightness):
        PTLogger.info("Setting brightness to " + str(brightness))
        if self._hub_connected():
            self.unblank_screen()
            self._active_hub_module.set_brightness(brightness)
        else:
            PTLogger.warning(
                "Attempted to call set_brightness when there was no active hub"
            )

    def increment_brightness(self):
        PTLogger.info("Incrementing brightness")
        if self._hub_connected():
            self.unblank_screen()
            self._active_hub_module.increment_brightness()
        else:
            PTLogger.warning(
                "Attempted to call increment_brightness when there was no active hub"
            )

    def decrement_brightness(self):
        PTLogger.info("Decrementing brightness")
        if self._hub_connected():
            self.unblank_screen()
            self._active_hub_module.decrement_brightness()
        else:
            PTLogger.warning(
                "Attempted to call decrement_brightness when there was no active hub"
            )

    def blank_screen(self):
        PTLogger.info("Blanking screen")
        if self._hub_connected():
            self._active_hub_module.blank_screen()
        else:
            PTLogger.warning(
                "Attempted to call blank_screen when there was no active hub"
            )

    def unblank_screen(self):
        PTLogger.info("Unblanking screen")
        if self._hub_connected():
            self._active_hub_module.unblank_screen()
        else:
            PTLogger.warning(
                "Attempted to call unblank_screen when there was no active hub"
            )

    def get_oled_pi_control_state(self):
        if self._hub_connected():
            return self._active_hub_module.get_oled_pi_control_state()
        else:
            PTLogger.warning(
                "Attempted to call get_oled_pi_control_state when there was no active hub"
            )
            return None

    def set_oled_pi_control_state(self, is_pi_controlled):
        PTLogger.info("Setting OLED Pi control state to " +
                      str(is_pi_controlled))
        if self._hub_connected():
            self._active_hub_module.set_oled_pi_control_state(is_pi_controlled)
        else:
            PTLogger.warning(
                "Attempted to call set_oled_pi_control_state when there was no active hub"
            )

    def shutdown(self):
        PTLogger.info("Shutting down the hub")
        if self._hub_connected():
            self._active_hub_module.shutdown()
        else:
            PTLogger.warning(
                "Attempted to call shutdown when there was no active hub")

    def enable_hdmi_to_i2s_audio(self):
        PTLogger.info("Switching HDMI to I2S mux on")
        if self._hub_connected():
            self._active_hub_module.enable_hdmi_to_i2s_audio()
        else:
            PTLogger.warning(
                "Attempted to call enable_hdmi_to_i2s_audio when there was no active hub"
            )

    def disable_hdmi_to_i2s_audio(self):
        PTLogger.info("Switching HDMI to I2S mux off")
        if self._hub_connected():
            self._active_hub_module.disable_hdmi_to_i2s_audio()
        else:
            PTLogger.warning(
                "Attempted to call disable_hdmi_to_i2s_audio when there was no active hub"
            )

    def get_oled_spi_state(self):
        if self._hub_connected():
            return self._active_hub_module.get_oled_use_spi0()
        else:
            PTLogger.warning(
                "Attempted to call get_oled_spi_state when there was no active hub"
            )
            return None

    def _hub_connected(self):
        return self._active_hub_module is not None

    def _register_client(self):
        if self._hub_connected():
            if self._active_hub_module.__name__ == "pthub3.pthub3":
                self._active_hub_module.register_client(
                    self._on_hub_brightness_changed,
                    self._on_screen_blank_state_changed,
                    self._on_native_display_connect_state_changed,
                    self._on_external_display_connect_state_changed,
                    self._on_lid_open_state_changed,
                    self._on_hub_shutdown_requested,
                    self._on_hub_battery_state_changed,
                    self._on_button_press_state_changed,
                )
                self._active_hub_module.set_speed(10)
            else:
                self._active_hub_module.register_client(
                    self._on_hub_brightness_changed,
                    self._on_screen_blanked,
                    self._on_screen_unblanked,
                    self._on_lid_opened,
                    self._on_lid_closed,
                    self._on_hub_shutdown_requested,
                    self._on_hub_battery_state_changed,
                )

    def _write_device_serial_numbers_to_file(self):
        PTLogger.info("Writing serial numbers to file")

        serial_device = pthub3.get_serial_id()
        serial_display = pthub3.get_display_serial_id()
        serial_battery = pthub3.get_battery_serial_number()

        json_data = {
            "primary": serial_device,
            "display": serial_display,
            "battery": serial_battery,
        }

        serial_numbers_file = "/etc/pi-top/device_serial_numbers.json"

        if path.exists(serial_numbers_file):
            remove(serial_numbers_file)

        with open(serial_numbers_file, "w") as output_file:
            json_dump(json_data, output_file)
            output_file.write("\n")

    # Hub callbacks

    def _on_hub_shutdown_requested(self):
        self._callback_client.on_hub_shutdown_requested()

    def _on_hub_brightness_changed(self, new_value):
        self._callback_client.on_hub_brightness_changed(new_value)

    def _on_hub_battery_state_changed(
        self, charging_state, capacity, time_remaining, wattage
    ):
        self._callback_client.on_hub_battery_state_changed(
            charging_state, capacity, time_remaining, wattage
        )

    def _on_button_press_state_changed(self, button_pressed, is_pressed):
        self._callback_client.on_button_press_state_changed(
            button_pressed, is_pressed)

    def _on_screen_blank_state_changed(self, blanked_state):
        self._callback_client.on_screen_blank_state_changed(blanked_state)

    def _on_external_display_connect_state_changed(self, connected_state):
        self._callback_client.on_external_display_connect_state_changed(
            connected_state)

    def _on_native_display_connect_state_changed(self, connected_state):
        self._callback_client.on_native_display_connect_state_changed(
            connected_state)

    def _on_screen_blanked(self):
        self._callback_client.on_screen_blanked()

    def _on_screen_unblanked(self):
        self._callback_client.on_screen_unblanked()

    def _on_lid_open_state_changed(self, lid_open_state):
        self._callback_client.on_lid_open_state_changed(lid_open_state)

    def _on_lid_opened(self):
        self._callback_client.on_lid_opened()

    def _on_lid_closed(self):
        self._callback_client.on_lid_closed()
