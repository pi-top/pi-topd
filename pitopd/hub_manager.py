import logging
from time import sleep

from pitop.common.common_ids import DeviceID

from .pthub import pthub
from .pthub2 import pthub2
from .pthub3 import pthub3

logger = logging.getLogger(__name__)


class HubManager:
    """Determines which type of pi-top device hub (if any) is connected and
    communicates with it."""

    def __init__(self):
        self._callback_client = None
        self._active_hub_module = None

    def initialise(self, callback_client):
        self._callback_client = callback_client

    def connect_to_hub(self):

        # Enable I2C for hub checking
        self._callback_client.on_i2c_state_required(True)

        # Attempt to connect to a v3 hub first, then v2, and finally v1.
        # This is because we can positively identify v2 and v3 on i2c.
        # We can also positively identify a v1 pi-top, however we cannot
        # do this for a pi-topCEED. Hence this is the fall-through case.

        logger.info("Attempting to find pi-topHUB v3...")
        if pthub3.initialise() is True:
            self._active_hub_module = pthub3
            logger.info("Connected to pi-topHUB v3")
            self._register_client()
            return True
        else:
            logger.warning("Could not initialise v3 hub")

        logger.info("Attempting to find pi-topHUB v2...")
        if pthub2.initialise() is True:
            self._active_hub_module = pthub2
            logger.info("Connected to pi-topHUB v2")
            self._register_client()
            return True
        else:
            logger.warning("Could not initialise v2 hub")

        logger.info("Attempting to find pi-topHUB v1...")

        spi_was_enabled = self._callback_client.on_spi0_state_requested()
        # Enable SPI for hub checking
        if not spi_was_enabled:
            self._callback_client.on_spi0_state_required(True)

        if pthub.initialise() is True:
            self._active_hub_module = pthub
            logger.info("Connected to pi-topHUB v1")
            self._register_client()
            return True
        else:
            logger.warning("Could not initialise v1 hub")

            # Disable SPI if it was not already running
            if not spi_was_enabled:
                self._callback_client.on_spi0_state_required(False)

        logger.error("Could not connect to a hub!")

        return False

    def start(self):
        if self._hub_connected():
            self._active_hub_module.start()
        else:
            logger.warning("Attempted to call start when there was no active hub")

    def stop(self):

        # When stopping, we unblank the screen and set the brightness to full
        # to prevent restarting with no display

        logger.info("Stopping hub manager...")

        if self._hub_connected():
            self.unblank_screen()

            logger.info("Stopping hub module...")
            self._active_hub_module.stop()

    def wait_for_device_identification(self):

        logger.debug("Waiting for device id to be established...")

        time_waited = 0
        while time_waited < 5:

            device_id = self.get_device_id()
            if device_id == DeviceID.unknown:

                sleep(0.25)
                time_waited += 0.25

            else:
                logger.debug(
                    "Got device id ("
                    + str(device_id)
                    + "). Waited "
                    + str(time_waited)
                    + " seconds"
                )
                return

        logger.warning("Timed out waiting for device identification.")

    def get_device_id(self):
        if self._hub_connected():
            return self._active_hub_module.get_device_id()
        else:
            logger.debug("Attempted to call get_device_id when there was no active hub")
            return DeviceID.unknown

    def get_brightness(self):
        if self._hub_connected():
            return self._active_hub_module.get_brightness()
        else:
            logger.warning(
                "Attempted to call get_brightness when there was no active hub"
            )
            return None

    def get_screen_blanked_state(self):
        if self._hub_connected():
            return self._active_hub_module.get_screen_blanked_state()
        else:
            logger.warning(
                "Attempted to call get_screen_blanked_state() when there was no active hub"
            )
            return None

    def get_shutdown_state(self):
        if self._hub_connected():
            return self._active_hub_module.get_shutdown_state()
        else:
            logger.warning(
                "Attempted to call get_shutdown_state when there was no active hub"
            )
            return None

    def get_lid_open_state(self):
        if self._hub_connected():
            return self._active_hub_module.get_lid_open_state()
        else:
            logger.warning(
                "Attempted to call get_lid_open_state when there was no active hub"
            )
            return None

    def get_battery_state(self):
        if self._hub_connected():
            return self._active_hub_module.get_battery_state()
        else:
            logger.warning(
                "Attempted to call get_battery_state when there was no active hub"
            )
            return None

    def set_brightness(self, brightness):
        logger.info("Setting brightness to " + str(brightness))
        if self._hub_connected():
            self.unblank_screen()
            self._active_hub_module.set_brightness(brightness)
        else:
            logger.warning(
                "Attempted to call set_brightness when there was no active hub"
            )

    def increment_brightness(self):
        logger.info("Incrementing brightness")
        if self._hub_connected():
            self.unblank_screen()
            self._active_hub_module.increment_brightness()
        else:
            logger.warning(
                "Attempted to call increment_brightness when there was no active hub"
            )

    def decrement_brightness(self):
        logger.info("Decrementing brightness")
        if self._hub_connected():
            self.unblank_screen()
            self._active_hub_module.decrement_brightness()
        else:
            logger.warning(
                "Attempted to call decrement_brightness when there was no active hub"
            )

    def blank_screen(self):
        logger.info("Blanking screen")
        if self._hub_connected():
            self._active_hub_module.blank_screen()
        else:
            logger.warning(
                "Attempted to call blank_screen when there was no active hub"
            )

    def unblank_screen(self):
        logger.info("Unblanking screen")
        if self._hub_connected():
            self._active_hub_module.unblank_screen()
        else:
            logger.warning(
                "Attempted to call unblank_screen when there was no active hub"
            )

    def get_oled_pi_control_state(self):
        if self._hub_connected():
            return self._active_hub_module.get_oled_pi_control_state()
        else:
            logger.warning(
                "Attempted to call get_oled_pi_control_state when there was no active hub"
            )
            return None

    def set_oled_pi_control_state(self, is_pi_controlled):
        logger.info("Setting OLED Pi control state to " + str(is_pi_controlled))
        if self._hub_connected():
            self._active_hub_module.set_oled_pi_control_state(is_pi_controlled)
        else:
            logger.warning(
                "Attempted to call set_oled_pi_control_state when there was no active hub"
            )

    def shutdown(self):
        logger.info("Shutting down the hub")
        if self._hub_connected():
            self._active_hub_module.shutdown()
        else:
            logger.warning("Attempted to call shutdown when there was no active hub")

    def enable_hdmi_to_i2s_audio(self):
        logger.info("Switching HDMI to I2S mux on")
        if self._hub_connected():
            self._active_hub_module.enable_hdmi_to_i2s_audio()
        else:
            logger.warning(
                "Attempted to call enable_hdmi_to_i2s_audio when there was no active hub"
            )

    def disable_hdmi_to_i2s_audio(self):
        logger.info("Switching HDMI to I2S mux off")
        if self._hub_connected():
            self._active_hub_module.disable_hdmi_to_i2s_audio()
        else:
            logger.warning(
                "Attempted to call disable_hdmi_to_i2s_audio when there was no active hub"
            )

    def get_oled_spi_bus(self):
        if self._hub_connected():
            if self.get_oled_use_spi0():
                return 0
            else:
                return 1
        else:
            logger.warning(
                "Attempted to call get_oled_spi_state when there was no active hub"
            )
            return None

    def get_oled_use_spi0(self):
        if self._hub_connected():
            return self._active_hub_module.get_oled_use_spi0()
        else:
            logger.warning(
                "Attempted to call get_oled_spi_state when there was no active hub"
            )
            return None

    def set_oled_use_spi0(self, use_spi0):
        if self._hub_connected():
            logger.info(f"Setting OLED to use SPI bus {0 if use_spi0 else 1}")
            return self._active_hub_module.set_oled_use_spi0(use_spi0)
        else:
            logger.warning(
                "Attempted to call set_oled_spi_state when there was no active hub"
            )
            return None

    def _hub_connected(self):
        return self._active_hub_module is not None

    def _register_client(self):
        if self._hub_connected():
            __c = self._callback_client
            if self._active_hub_module.__name__ == "pitopd.pthub3.pthub3":
                self._active_hub_module.register_client(
                    {
                        "hub_brightness": __c.on_hub_brightness_changed,
                        "screen_blank_state": __c.on_screen_blank_state_changed,
                        "lid_open_state": __c.on_lid_open_state_changed,
                        "hub_shutdown_requested": __c.on_hub_shutdown_requested,
                        "hub_battery_state": __c.on_hub_battery_state_changed,
                        "button_press_state": __c.on_button_press_state_changed,
                        "power_press_state": __c.on_power_button_press_state_changed,
                        "oled_pi_controlled_state": __c.on_oled_pi_controlled_state_changed,
                        "oled_spi_state": __c.on_oled_spi_bus_changed,
                        # "buttons_route_to_gpio": __c.on_buttons_route_to_gpio_state_changed,
                    }
                )
                self._active_hub_module.set_speed(10)
            else:
                self._active_hub_module.register_client(
                    __c.on_hub_brightness_changed,
                    __c.on_screen_blanked,
                    __c.on_screen_unblanked,
                    __c.on_lid_opened,
                    __c.on_lid_closed,
                    __c.on_hub_shutdown_requested,
                    __c.on_hub_battery_state_changed,
                )

    def get_serial_id(self):
        if self._hub_connected():
            if hasattr(self._active_hub_module, "get_serial_id"):
                return self._active_hub_module.get_serial_id()
        else:
            logger.warning(
                "Attempted to call get_serial_id when there was no active hub"
            )

    def get_battery_serial_number(self):
        if self._hub_connected():
            if hasattr(self._active_hub_module, "get_battery_serial_number"):
                return self._active_hub_module.get_battery_serial_number()
        else:
            logger.warning(
                "Attempted to call get_battery_serial_number when there was no active hub"
            )

    def get_display_serial_id(self):
        if self._hub_connected():
            if hasattr(self._active_hub_module, "get_display_serial_id"):
                return self._active_hub_module.get_display_serial_id()
        else:
            logger.warning(
                "Attempted to call get_display_serial_id when there was no active hub"
            )
