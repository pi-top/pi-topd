from ptcommon.logger import PTLogger
from ptcommon.ptdm_message import Message
import zmq
import traceback
from threading import Lock

# Creates a server for clients to connect to,
# and publishes state change messages to these clients


class PublishServer():

    def initialise(self):
        self._socket_lock = Lock()
        self._shutting_down = False

    def start_listening(self):
        PTLogger.debug("Opening publisher socket...")

        try:
            self._socket_lock.acquire()

            self._zmq_context = zmq.Context()
            self._zmq_socket = self._zmq_context.socket(zmq.PUB)
            self._zmq_socket.bind("tcp://*:3781")
            PTLogger.info("Publish server ready...")

            return True

        except zmq.error.ZMQError as e:
            PTLogger.error("Error starting the publish server: " + str(e))
            PTLogger.info(traceback.format_exc())

            return False

        finally:
            self._socket_lock.release()

    def stop_listening(self):
        PTLogger.info("Closing publisher socket...")

        try:
            self._socket_lock.acquire()

            self._shutting_down = True

            self._zmq_socket.close()
            self._zmq_context.destroy()
            PTLogger.debug("Closed publisher socket.")

        except zmq.error.ZMQError as e:
            PTLogger.error("Error starting the publish server: " + str(e))
            PTLogger.info(traceback.format_exc())

        finally:
            self._socket_lock.release()

    def publish_brightness_changed(self, new_brightness: int):
        self._check_type(new_brightness, int)
        PTLogger.info("Publishing PUB_BRIGHTNESS_CHANGED " + str(new_brightness))
        self._send_message(Message.PUB_BRIGHTNESS_CHANGED, [new_brightness])

    def publish_peripheral_connected(self, peripheral_id: int):
        self._check_type(peripheral_id, int)
        PTLogger.info("Publishing PUB_PERIPHERAL_CONNECTED " + str(peripheral_id))
        self._send_message(Message.PUB_PERIPHERAL_CONNECTED, [peripheral_id])

    def publish_peripheral_disconnected(self, peripheral_id: int):
        self._check_type(peripheral_id, int)
        PTLogger.info("Publishing PUB_PERIPHERAL_DISCONNECTED " + str(peripheral_id))
        self._send_message(Message.PUB_PERIPHERAL_DISCONNECTED, [peripheral_id])

    def publish_shutdown_requested(self):
        PTLogger.info("Publishing PUB_SHUTDOWN_REQUESTED")
        self._send_message(Message.PUB_SHUTDOWN_REQUESTED, [])

    def publish_reboot_required(self):
        PTLogger.info("Publishing PUB_REBOOT_REQUIRED")
        self._send_message(Message.PUB_REBOOT_REQUIRED, [])

    def publish_battery_state_changed(self, connected: int, new_capacity: int, new_time: int, new_wattage: int):
        self._check_type(connected, int)
        self._check_type(new_capacity, int)
        self._check_type(new_time, int)
        self._check_type(new_wattage, int)
        self._send_message(Message.PUB_BATTERY_STATE_CHANGED, [connected, new_capacity, new_time, new_wattage])

    def publish_screen_blanked(self):
        PTLogger.info("Publishing PUB_SCREEN_BLANKED")
        self._send_message(Message.PUB_SCREEN_BLANKED, [])

    def publish_screen_unblanked(self):
        PTLogger.info("Publishing PUB_SCREEN_UNBLANKED")
        self._send_message(Message.PUB_SCREEN_UNBLANKED, [])

    def publish_low_battery_warning(self):
        PTLogger.info("Publishing PUB_LOW_BATTERY_WARNING")
        self._send_message(Message.PUB_LOW_BATTERY_WARNING, [])

    def publish_critical_battery_warning(self):
        PTLogger.info("Publishing PUB_CRITICAL_BATTERY_WARNING")
        self._send_message(Message.PUB_CRITICAL_BATTERY_WARNING, [])

    def publish_lid_opened(self):
        PTLogger.info("Publishing PUB_LID_OPENED")
        self._send_message(Message.PUB_LID_OPENED, [])

    def publish_lid_closed(self):
        PTLogger.info("Publishing PUB_LID_CLOSED")
        self._send_message(Message.PUB_LID_CLOSED, [])

    # Internal functions

    def _send_message(self, message_id, parameters):

        message = Message.from_parts(message_id, parameters)

        try:
            self._socket_lock.acquire()

            if (self._shutting_down is True):
                return

            self._zmq_socket.send_string(message.to_string())
            PTLogger.debug("Published message: " + message.message_friendly_string())

        except zmq.error.ZMQError as e:
            PTLogger.error("Communication error in publish server: " + str(e))
            PTLogger.info(traceback.format_exc())

        finally:
            self._socket_lock.release()

    def _check_type(self, var, type):

        if (isinstance(var, type) is False):
            raise TypeError("Wrong type to be sent in message")
