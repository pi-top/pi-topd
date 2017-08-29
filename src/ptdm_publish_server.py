
# Creates a server for clients to connect to,
# and publishes state change messages to these clients

import zmq
import time
from ptdm_client import ptdm_message


class PublishServer():
    test_device_id_vals = [0, 1, 2, 3]
    test_brightness_vals = [3, 6, 10]
    test_peripheral_id = 1
    test_battery_charging_state_vals = [1, 0]
    test_battery_capacity_vals = [95, 50]
    test_battery_time_remaining_vals = [300, 250]

    def initialise(self, logger):
        self._logger = logger

    def start_listening(self):
        self._logger.debug("Opening publisher socket...")

        try:
            self._zmq_context = zmq.Context()
            self._zmq_socket = self._zmq_context.socket(zmq.PUB)
            self._zmq_socket.bind("tcp://*:3781")
            self._logger.info("Publish server ready...")

        except zmq.error.ZMQError as e:
            self._logger.error("Error starting the publish server: " + str(e))
            return

    def stop_listening(self):
        self._logger.debug("Closing publisher socket...")

        self._zmq_socket.close()
        self._zmq_context.destroy()
        self._logger.debug("Done.")

    def test_all_publishes(self):
        for val in self.test_device_id_vals:
            self.publish_device_id_changed(val)

        for val in self.test_brightness_vals:
            self.publish_brightness_changed(val)

        self.publish_peripheral_connected(self.test_peripheral_id)
        self.publish_peripheral_disconnected(self.test_peripheral_id)

        for val in self.test_battery_charging_state_vals:
            self.publish_battery_charging_state_changed(val)

        for val in self.test_battery_capacity_vals:
            self.publish_battery_capacity_changed(val)

        for val in self.test_battery_time_remaining_vals:
            self.publish_battery_time_remaining_changed(val)

        self.publish_screen_blanked()
        self.publish_screen_unblanked()
        self.publish_shutdown_requested()
        self.publish_reboot_required()

    def publish_brightness_changed(self, new_brightness):
        self._send_message(ptdm_message.Message.PUB_BRIGHTNESS_CHANGED, [new_brightness])

    def publish_peripheral_connected(self, peripheral_id):
        self._send_message(ptdm_message.Message.PUB_PERIPHERAL_CONNECTED, [peripheral_id])

    def publish_peripheral_disconnected(self, peripheral_id):
        self._send_message(ptdm_message.Message.PUB_PERIPHERAL_DISCONNECTED, [peripheral_id])

    def publish_shutdown_requested(self):
        self._send_message(ptdm_message.Message.PUB_SHUTDOWN_REQUESTED, [])

    def publish_reboot_required(self):
        self._send_message(ptdm_message.Message.PUB_REBOOT_REQUIRED, [])

    def publish_battery_charging_state_changed(self, connected_int):
        self._send_message(ptdm_message.Message.PUB_BATTERY_CHARGING_STATE_CHANGED, [connected_int])

    def publish_battery_capacity_changed(self, new_capacity):
        self._send_message(ptdm_message.Message.PUB_BATTERY_CAPACITY_CHANGED, [new_capacity])

    def publish_battery_time_remaining_changed(self, new_time):
        self._send_message(ptdm_message.Message.PUB_BATTERY_TIME_REMAINING_CHANGED, [new_time])

    def publish_screen_blanked(self):
        self._send_message(ptdm_message.Message.PUB_SCREEN_BLANKED, [])

    def publish_screen_unblanked(self):
        self._send_message(ptdm_message.Message.PUB_SCREEN_UNBLANKED, [])

    def publish_device_id_changed(self, device_id_int):
        self._logger.debug("Publishing device ID changed")
        self._send_message(ptdm_message.Message.PUB_DEVICE_ID_CHANGED, [device_id_int])

    def publish_low_battery_warning(self):
        self._send_message(ptdm_message.Message.PUB_LOW_BATTERY_WARNING, [])

    def publish_critical_battery_warning(self):
        self._send_message(ptdm_message.Message.PUB_CRITICAL_BATTERY_WARNING, [])

    def publish_lid_opened(self):
        self._send_message(ptdm_message.Message.PUB_LID_OPENED, [])

    def publish_lid_closed(self):
        self._send_message(ptdm_message.Message.PUB_LID_CLOSED, [])

    # Internal functions

    def _send_message(self, message_id, parameters):

        message = ptdm_message.Message.from_parts(message_id, parameters)

        try:
            self._zmq_socket.send_string(message.to_string())
            self._logger.info("Published message: " + message.message_friendly_string())

        except zmq.error.ZMQError as e:
            self._logger.error(
                "Communication error in publish server: " + str(e))
