
# Creates a server for clients to connect to,
# and publishes state change messages to these clients

import zmq
import time
from ptdm_messages import Message


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
            raise e

    def stop_listening(self):
        self._logger.debug("Closing publisher socket...")

        self._zmq_socket.close()
        self._zmq_context.destroy()
        self._logger.debug("Done.")

    def publish_brightness_changed(self, new_brightness):
        self._logger.debug("Publishing brightness changed")
        self._send_message(Message.PUB_BRIGHTNESS_CHANGED, [new_brightness])

    def publish_peripheral_connected(self, peripheral_id):
        self._logger.debug("Publishing peripheral connected")
        self._send_message(Message.PUB_PERIPHERAL_CONNECTED, [peripheral_id])

    def publish_peripheral_disconnected(self, peripheral_id):
        self._logger.debug("Publishing peripheral disconnected")
        self._send_message(Message.PUB_PERIPHERAL_DISCONNECTED, [peripheral_id])

    def publish_shutdown_requested(self):
        self._logger.debug("Publishing shutdown requested")
        self._send_message(Message.PUB_SHUTDOWN_REQUESTED, [])

    def publish_reboot_required(self):
        self._logger.debug("Publishing reboot required")
        self._send_message(Message.PUB_REBOOT_REQUIRED, [])

    def publish_brightness_changed(new_value):
        self._logger.debug("Publishing battery charging state changed")
        self._send_message(Message.PUB_BRIGHTNESS_CHANGED, [new_value])

    def publish_battery_charging_state_changed(self, connected_int):
        self._logger.debug("Publishing battery charging state changed")
        self._send_message(Message.PUB_BATTERY_CHARGING_STATE_CHANGED, [connected_int])

    def publish_battery_capacity_changed(self, new_capacity):
        self._logger.debug("Publishing battery capacity changed")
        self._send_message(Message.PUB_BATTERY_CAPACITY_CHANGED, [new_capacity])

    def publish_battery_time_remaining_changed(self, new_time):
        self._logger.debug("Publishing battery time remaining changed")
        self._send_message(Message.PUB_BATTERY_TIME_REMAINING_CHANGED, [new_time])

    def publish_screen_blank_state_changed(blanked_bool):
        self._logger.debug("Publishing screen blank state changed")
        self._send_message(Message.PUB_SCREEN_BLANK_STATE_CHANGED, [int(blanked_bool)])

    def publish_device_id_changed(device_id_int):
        self._logger.debug("Publishing device ID changed")
        self._send_message(Message.PUB_DEVICE_ID_CHANGED, [device_id_int])

    def publish_peripheral_connected(peripheral_device_id_int):
        self._logger.debug("Publishing new peripheral connection")
        self._send_message(Message.PUB_PERIPHERAL_CONNECTED, [peripheral_device_id_int])

    def publish_peripheral_disconnected(peripheral_device_id_int):
        self._logger.debug("Publishing new peripheral disconnection")
        self._send_message(Message.PUB_PERIPHERAL_DISCONNECTED, [peripheral_device_id_int])

    # Internal functions

    def _send_message(self, message_id, parameters):
        message_to_send = Message.build_message_string(message_id, parameters)
        self._logger.debug("Publishing message: " + message_to_send)

        try:
            self._zmq_socket.send_string(message_to_send)

        except zmq.error.ZMQError as e:
            self._logger.error("Communication error in publish server: " + str(e))
