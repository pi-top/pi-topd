from ptcommon.common_ids import DeviceID
from ptcommon.logger import PTLogger
from importlib import import_module
import traceback
from os import makedirs
from os import path
from time import sleep

# Discovers which hub libraries are installed, and uses those to
# determine the type of hub in use and communicate with it


class HubManager():

    def initialise(self, callback_client):

        self._callback_client = callback_client
        self._active_hub_module = None

    def connect_to_hub(self):

        # Attempt to connect to a v2 hub first. This is because we can
        # positively identify v2 on i2c. We can also positively identify
        # a v1 pi-top, however we cannot do this for a CEED. Hence this
        # is the fall-through case.

        PTLogger.info("Attempting to find pi-topHUB v2...")

        try:
            self._module_hub_v2 = self._import_module("pthub2.pthub2")

            if (self._module_hub_v2.initialise() is True):
                self._active_hub_module = self._module_hub_v2
                PTLogger.info("Connected to pi-topHUB v2")
                self._register_client()
                return True
            else:
                PTLogger.warning("Could not initialise v2 hub")

        except Exception as e:
            PTLogger.warning("Failed to connect to a v2 hub. " + str(e))
            PTLogger.info(traceback.format_exc())

        PTLogger.info("Attempting to find pi-topHUB v1...")

        try:
            self._module_hub_v1 = self._import_module("pthub.pthub")

            if (self._module_hub_v1.initialise() is True):
                self._active_hub_module = self._module_hub_v1
                PTLogger.info("Connected to pi-topHUB v1")
                self._register_client()
                return True
            else:
                PTLogger.warning("Could not initialise v1 hub")

        except Exception as e:
            PTLogger.warning("Failed to connect to a v1 hub. " + str(e))
            PTLogger.info(traceback.format_exc())

        PTLogger.error("Could not connect to a hub!")
        return False

    def start(self):
        if (self._hub_connected()):
            self._active_hub_module.start()
        else:
            PTLogger.warning("Attempted to call start when there was no active hub")

    def stop(self):

        # When stopping, we unblank the screen and set the brightness to full
        # to prevent restarting with no display

        PTLogger.info("Stopping hub manager...")

        if (self._hub_connected()):
            self.unblank_screen()

            PTLogger.info("Stopping hub module...")
            self._active_hub_module.stop()

    def wait_for_device_identification(self):

        PTLogger.debug("Waiting for device id to be established...")

        time_waited = 0
        while (time_waited < 5):

            device_id = self.get_device_id()
            if (device_id == DeviceID.unknown):

                sleep(0.25)
                time_waited += 0.25

            else:
                PTLogger.debug("Got device id (" + str(device_id) + "). Waited " + str(time_waited) + " seconds")
                return

        PTLogger.warning("Timed out waiting for device identification.")

    def get_device_id(self):
        if (self._hub_connected()):
            return self._active_hub_module.get_device_id()
        else:
            PTLogger.warning("Attempted to call get_device_id when there was no active hub")
            return DeviceID.unknown

    def get_brightness(self):
        if (self._hub_connected()):
            return self._active_hub_module.get_brightness()
        else:
            PTLogger.warning("Attempted to call get_brightness when there was no active hub")

    def get_screen_off_state(self):
        if (self._hub_connected()):
            return self._active_hub_module.get_screen_off_state()
        else:
            PTLogger.warning("Attempted to call get_screen_off_state when there was no active hub")

    def get_shutdown_state(self):
        if (self._hub_connected()):
            return self._active_hub_module.get_shutdown_state()
        else:
            PTLogger.warning("Attempted to call get_shutdown_state when there was no active hub")

    def get_battery_charging_state(self):
        if (self._hub_connected()):
            return self._active_hub_module.get_battery_charging_state()
        else:
            PTLogger.warning("Attempted to call get_battery_charging_state when there was no active hub")

    def get_battery_time_state(self):
        if (self._hub_connected()):
            return self._active_hub_module.get_battery_time_state()
        else:
            PTLogger.warning("Attempted to call get_battery_time_state when there was no active hub")

    def get_battery_state(self):
        if (self._hub_connected()):
            return self._active_hub_module.get_battery_state()
        else:
            PTLogger.warning("Attempted to call get_battery_state when there was no active hub")

    def set_brightness(self, brightness):
        PTLogger.info("Setting brightness to " + str(brightness))
        if (self._hub_connected()):
            self._active_hub_module.set_brightness(brightness)
        else:
            PTLogger.warning("Attempted to call set_brightness when there was no active hub")

    def increment_brightness(self):
        PTLogger.info("Incrementing brightness")
        if (self._hub_connected()):
            self._active_hub_module.increment_brightness()
        else:
            PTLogger.warning("Attempted to call increment_brightness when there was no active hub")

    def decrement_brightness(self):
        PTLogger.info("Decrementing brightness")
        if (self._hub_connected()):
            self._active_hub_module.decrement_brightness()
        else:
            PTLogger.warning("Attempted to call decrement_brightness when there was no active hub")

    def blank_screen(self):
        PTLogger.info("Blanking screen")
        if (self._hub_connected()):
            self._active_hub_module.blank_screen()
        else:
            PTLogger.warning("Attempted to call blank_screen when there was no active hub")

    def unblank_screen(self):
        PTLogger.info("Unblanking screen")
        if (self._hub_connected()):
            self._active_hub_module.unblank_screen()
        else:
            PTLogger.warning("Attempted to call unblank_screen when there was no active hub")

    def shutdown(self):
        PTLogger.info("Shutting down the hub")
        if (self._hub_connected()):
            self._active_hub_module.shutdown()
        else:
            PTLogger.warning("Attempted to call shutdown when there was no active hub")

    def enable_hdmi_to_i2s_audio(self):
        PTLogger.info("Switching HDMI to I2S mux on")
        if (self._hub_connected()):
            self._active_hub_module.enable_hdmi_to_i2s_audio()
        else:
            PTLogger.warning("Attempted to call enable_hdmi_to_i2s_audio when there was no active hub")

    def disable_hdmi_to_i2s_audio(self):
        PTLogger.info("Switching HDMI to I2S mux off")
        if (self._hub_connected()):
            self._active_hub_module.disable_hdmi_to_i2s_audio()
        else:
            PTLogger.warning("Attempted to call disable_hdmi_to_i2s_audio when there was no active hub")

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
                self._on_hub_brightness_changed,
                self._on_screen_blanked,
                self._on_screen_unblanked,
                self._on_lid_opened,
                self._on_lid_closed,
                self._on_hub_shutdown_requested,
                self._on_hub_battery_state_changed)

    # Hub callbacks

    def _on_hub_shutdown_requested(self):
        self._callback_client._on_hub_shutdown_requested()

    def _on_hub_brightness_changed(self, new_value):
        self._callback_client._on_hub_brightness_changed(new_value)

    def _on_hub_battery_state_changed(self, charging_state, capacity, time_remaining, wattage):
        self._callback_client._on_hub_battery_state_changed(charging_state, capacity, time_remaining, wattage)

    def _on_screen_blanked(self):
        self._callback_client._on_screen_blanked()

    def _on_screen_unblanked(self):
        self._callback_client._on_screen_unblanked()

    def _on_lid_opened(self):
        self._callback_client._on_lid_opened()

    def _on_lid_closed(self):
        self._callback_client._on_lid_closed()
