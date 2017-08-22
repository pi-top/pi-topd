
# Instantiates and coordinates between the other classes

from ptdm_logger import Logger
from ptdm_hub_manager import HubManager
from ptdm_peripheral_manager import PeripheralManager
from ptdm_publish_server import PublishServer
from ptdm_request_server import RequestServer
from ptdm_shutdown_client import ShutdownManager
import time
import sys
import logging


class Controller():

    def initialise(self, log_level):
        self._continue_running = True
        self._logger = Logger(log_level)

        self._logger.info("Initialising device manager")

        # Create classes

        self._shutdown_mgr = ShutdownManager()
        self._hub_manager = HubManager()
        self._peripheral_manager = PeripheralManager()
        self._publish_server = PublishServer()
        self._request_server = RequestServer(self._publish_server)

        # Initialise

        self._hub_manager.initialise(self._logger, self)
        self._peripheral_manager.initialise(self._logger, self)
        self._publish_server.initialise(self._logger)
        self._request_server.initialise(self._logger, self)

    def start(self):
        self._logger.info("Starting device manager")

        self._hub_manager.connect_to_hub()
        self._hub_manager.register_client(self)
        self._hub_manager.start()

        self._peripheral_manager.start()

        self._publish_server.start_listening()
        self._request_server.start_listening()

        while (self._continue_running):

            time.sleep(0.5)

        self._request_server.stop_listening()
        self._publish_server.stop_listening()

        self._peripheral_manager.stop()

        self._hub_manager.stop()

        sys.exit(0)

    def stop(self):
        self._logger.info("Stopping device manager")
        self._continue_running = False

    ###########################################
    # Request server callback methods
    ###########################################

    def _on_request_get_brightness(self):
        return self._hub_manager.get_brightness()

    def _on_request_set_brightness(self, brightness):
        self._hub_manager.set_brightness(brightness)

    def _on_request_get_device_id(self):
        return self._hub_manager.get_device_id()

    def _on_request_increment_brightness(self):
        self._hub_manager.increment_brightness()

    def _on_request_decrement_brightness(self):
        self._hub_manager.decrement_brightness()

    def _on_request_blank_screen(self):
        self._hub_manager.blank_screen()

    def _on_request_unblank_screen(self):
        self._hub_manager.unblank_screen()

    ###########################################
    # Hub Manager callback methods
    ###########################################

    def _on_hub_shutdown_requested(self):
        self._publish_server.publish_shutdown_requested()

    def _on_reboot_required(self):
        self._publish_server.publish_reboot_required()

    def _on_hub_brightness_changed(self, new_value):
        self._publish_server.publish_brightness_changed(new_value)

    def _on_hub_battery_charging_state_changed(self, new_value):
        self._publish_server.publish_battery_charging_state_changed(new_value)
        # self._publish_server.publish_battery_capacity_changed(new_value)
        self._shutdown_mgr.set_battery_charging_state(new_value)
        self._shutdown_mgr.process_battery_state()

    def _on_hub_battery_capacity_changed(self, new_value):
        self._publish_server.publish_battery_capacity_changed(new_value)
        self._shutdown_mgr.set_battery_capacity(new_value)
        self._shutdown_mgr.process_battery_state()

    def _on_hub_battery_time_remaining_changed(self, new_value):
        self._publish_server.publish_battery_time_remaining_changed(new_value)

    def _on_screen_blank_state_changed(self, blanked_bool):
        self._publish_server.publish_screen_blank_state_changed(blanked_bool)

    def _on_lid_state_changed(self, lid_open_bool):
        self._publish_server.publish_lid_state_changed(lid_open_bool)

    def _on_device_id_changed(self, device_id_int):
        self._publish_server.publish_device_id_changed(device_id_int)
        self._shutdown_mgr.set_device_id(device_id_int)

    ###########################################
    # Peripheral Manager callback methods
    ###########################################

    def _on_peripheral_connected(self, peripheral_id_int):
        self._publish_server.publish_peripheral_connected(peripheral_id_int)

    def _on_peripheral_disconnected(self, peripheral_id_int):
        self._publish_server.publish_peripheral_disconnected(peripheral_id_int)
