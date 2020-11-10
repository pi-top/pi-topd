from pitop.core.logger import PTLogger
from pitop.core.ptdm_message import Message
from pitop.core.common_ids import DeviceID
from threading import Thread
from time import sleep
import traceback
import zmq


# Creates a server for clients to connect to, and then responds to
# queries from these clients for device-related debug information.
class RequestServer:
    _thread = Thread()

    def __init__(self):
        self._thread = Thread(target=self._thread_method)
        self._continue = False
        self._callback_client = None
        self._zmq_context = zmq.Context()
        self._zmq_socket = self._zmq_context.socket(zmq.REP)

    def initialise(self, callback_client):
        self._callback_client = callback_client

    def start_listening(self):
        PTLogger.debug("Opening request socket...")

        try:
            self._zmq_socket.bind("tcp://*:3782")
            PTLogger.info("Responder server ready.")

        except zmq.error.ZMQError as e:
            PTLogger.error("Error starting the request server: " + str(e))
            PTLogger.info(traceback.format_exc())

            return False

        sleep(0.5)

        self._continue = True
        self._thread.start()

        return True

    def stop_listening(self):
        PTLogger.info("Closing responder socket...")

        self._continue = False
        if self._thread.is_alive():
            self._thread.join()

        self._zmq_socket.close()
        self._zmq_context.destroy()

        PTLogger.debug("Closed responder socket.")

    def _thread_method(self):
        PTLogger.info("Listening for requests...")

        while self._continue:
            poller = zmq.Poller()
            poller.register(self._zmq_socket, zmq.POLLIN)

            events = poller.poll(500)

            if len(events) > 0:
                request = self._zmq_socket.recv_string()
                PTLogger.debug("Request received: " + request)

                response = self._process_request(request)

                PTLogger.debug("Sending response: " + response)
                self._zmq_socket.send_string(response)

    def _process_request(self, request):
        valid_message_format = False
        try:
            message = Message.from_string(request)
            PTLogger.debug("Received request: " +
                           message.message_friendly_string())

            if message.message_id() == Message.REQ_PING:
                message.validate_parameters(list())
                response = Message.from_parts(Message.RSP_PING, list())

            elif message.message_id() == Message.REQ_GET_DEVICE_ID:
                message.validate_parameters(list())
                device_id = self._callback_client.on_request_get_device_id()
                if device_id is None:
                    device_id = -1
                if isinstance(device_id, DeviceID):
                    device_id = device_id.value

                response = Message.from_parts(
                    Message.RSP_GET_DEVICE_ID, [device_id])

            elif message.message_id() == Message.REQ_GET_BRIGHTNESS:
                message.validate_parameters(list())
                brightness = self._callback_client.on_request_get_brightness()
                if brightness is None:
                    brightness = -1
                response = Message.from_parts(
                    Message.RSP_GET_BRIGHTNESS, [brightness])

            elif message.message_id() == Message.REQ_SET_BRIGHTNESS:
                message.validate_parameters([int])
                self._callback_client.on_request_set_brightness(
                    int(message.parameters()[0])
                )
                response = Message.from_parts(
                    Message.RSP_SET_BRIGHTNESS, list())

            elif message.message_id() == Message.REQ_INCREMENT_BRIGHTNESS:
                message.validate_parameters(list())
                self._callback_client.on_request_increment_brightness()
                response = Message.from_parts(
                    Message.RSP_INCREMENT_BRIGHTNESS, list())

            elif message.message_id() == Message.REQ_DECREMENT_BRIGHTNESS:
                message.validate_parameters(list())
                self._callback_client.on_request_decrement_brightness()
                response = Message.from_parts(
                    Message.RSP_DECREMENT_BRIGHTNESS, list())

            elif message.message_id() == Message.REQ_BLANK_SCREEN:
                message.validate_parameters(list())
                self._callback_client.on_request_blank_screen()
                response = Message.from_parts(Message.RSP_BLANK_SCREEN, list())

            elif message.message_id() == Message.REQ_UNBLANK_SCREEN:
                message.validate_parameters(list())
                self._callback_client.on_request_unblank_screen()
                response = Message.from_parts(
                    Message.RSP_UNBLANK_SCREEN, list())

            elif message.message_id() == Message.REQ_GET_SCREEN_BACKLIGHT_STATE:
                message.validate_parameters(list())
                backlight_state = (
                    self._callback_client.on_request_get_screen_backlight_state()
                )
                if backlight_state is None:
                    backlight_state = -1
                response = Message.from_parts(
                    Message.RSP_GET_SCREEN_BACKLIGHT_STATE, [backlight_state]
                )

            elif message.message_id() == Message.REQ_SET_SCREEN_BACKLIGHT_STATE:
                message.validate_parameters([int])
                self._callback_client.on_request_set_screen_backlight_state(
                    int(message.parameters()[0])
                )
                response = Message.from_parts(
                    Message.RSP_SET_SCREEN_BACKLIGHT_STATE, list()
                )

            elif message.message_id() == Message.REQ_GET_OLED_CONTROL:
                message.validate_parameters(list())
                oled_pi_control_state = (
                    self._callback_client.on_request_get_oled_control()
                )
                if oled_pi_control_state is None:
                    oled_pi_control_state = -1
                response = Message.from_parts(
                    Message.RSP_GET_OLED_CONTROL, [oled_pi_control_state]
                )

            elif message.message_id() == Message.REQ_SET_OLED_CONTROL:
                message.validate_parameters([int])
                self._callback_client.on_request_set_oled_pi_control(
                    int(message.parameters()[0])
                )
                response = Message.from_parts(
                    Message.RSP_SET_OLED_CONTROL, list())

            elif message.message_id() == Message.REQ_GET_BATTERY_STATE:
                message.validate_parameters(list())
                charging_state, capacity, time_remaining, wattage = (
                    self._callback_client.on_request_battery_state()
                )
                response = Message.from_parts(
                    Message.RSP_GET_BATTERY_STATE,
                    [charging_state, capacity, time_remaining, wattage],
                )

            elif message.message_id() == Message.REQ_GET_PERIPHERAL_ENABLED:
                message.validate_parameters([int])
                enabled_bool = self._callback_client.on_request_get_peripheral_enabled(
                    int(message.parameters()[0])
                )
                enabled_int = int(enabled_bool is True)
                response = Message.from_parts(
                    Message.RSP_GET_PERIPHERAL_ENABLED, [enabled_int]
                )

            elif message.message_id() == Message.REQ_GET_SCREEN_BLANKING_TIMEOUT:
                message.validate_parameters(list())
                timeout = self._callback_client.on_request_get_screen_blanking_timeout()
                if timeout is None:
                    timeout = -1
                response = Message.from_parts(
                    Message.RSP_GET_SCREEN_BLANKING_TIMEOUT, [timeout]
                )

            elif message.message_id() == Message.REQ_SET_SCREEN_BLANKING_TIMEOUT:
                message.validate_parameters([int])
                self._callback_client.on_request_set_screen_blanking_timeout(
                    int(message.parameters()[0])
                )
                response = Message.from_parts(
                    Message.RSP_SET_SCREEN_BLANKING_TIMEOUT, list()
                )

            else:
                PTLogger.error("Unsupported request received: " + request)
                response = Message.from_parts(
                    Message.RSP_ERR_UNSUPPORTED, list())

            valid_message_format = True

        except ValueError as e:
            PTLogger.error("Error processing message: " + str(e))
            PTLogger.info(traceback.format_exc())
            response = Message.from_parts(Message.RSP_ERR_MALFORMED, list())

        except Exception as e:
            PTLogger.error("Unknown error processing message: " + str(e))
            PTLogger.info(traceback.format_exc())
            response = Message.from_parts(Message.RSP_ERR_SERVER, list())

        if valid_message_format:
            # Reduce output noise from RPi's polling lxpanel plugin
            if message.message_id() != Message.REQ_GET_BATTERY_STATE:
                PTLogger.info(
                    "Recv: "
                    + message.message_friendly_string()
                    + " - Send: "
                    + response.message_friendly_string()
                )

        return response.to_string()
