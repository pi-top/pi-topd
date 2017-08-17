
# Creates a server for clients to connect to,
# and publishes state change messages to these clients

import zmq
import time
from ptdm_message import Message


class PublishServer():

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

    def publish_brightness_changed(self, new_brightness):
        self._send_message(Message.PUB_BRIGHTNESS_CHANGED, [new_brightness])

    def publish_peripheral_connected(self, peripheral_id):
        self._send_message(Message.PUB_PERIPHERAL_CONNECTED, [peripheral_id])

    def publish_peripheral_disconnected(self, peripheral_id):
        self._send_message(Message.PUB_PERIPHERAL_DISCONNECTED, [peripheral_id])

    def publish_shutdown_requested(self):
        self._send_message(Message.PUB_SHUTDOWN_REQUESTED, [])

    def publish_reboot_required(self):
        self._send_message(Message.PUB_REBOOT_REQUIRED, [])

    def publish_battery_charging_state_changed(self, connected_int):
        self._send_message(Message.PUB_BATTERY_CHARGING_STATE_CHANGED, [connected_int])

    def publish_battery_capacity_changed(self, new_capacity):
        self._send_message(Message.PUB_BATTERY_CAPACITY_CHANGED, [new_capacity])

    def publish_battery_time_remaining_changed(self, new_time):
        self._send_message(Message.PUB_BATTERY_TIME_REMAINING_CHANGED, [new_time])

    def publish_screen_blank_state_changed(blanked_bool):
        if blanked_bool is True:
            self._send_message(Message.PUB_SCREEN_BLANKED, [])
        else:
            self._send_message(Message.PUB_SCREEN_UNBLANKED, [])

    def publish_device_id_changed(device_id_int):
        self._logger.debug("Publishing device ID changed")
        self._send_message(Message.PUB_DEVICE_ID_CHANGED, [device_id_int])

    # Internal functions

    def _send_message(self, message_id, parameters):

        message = Message.from_parts(message_id, parameters)
        self._logger.info("Publishing message: " + message.message_friendly_string())

        try:
            self._zmq_socket.send_string(message.to_string())

        except zmq.error.ZMQError as e:
            self._logger.error("Communication error in publish server: " + str(e))
