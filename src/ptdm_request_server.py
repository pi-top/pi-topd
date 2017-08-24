
# Creates a server for clients to connect to, and then responds to
# queries from these clients for device-related debugrmation.

import zmq
import time
from threading import Thread
from ptdm_client import ptdm_message


class RequestServer():
    _thread = Thread()

    def __init__(self, publish_server):
        self._publish_server = publish_server
        self._thread = Thread(target=self._thread_method)

    def initialise(self, logger, callback_client):
        self._logger = logger
        self._callback_client = callback_client

    def start_listening(self):
        self._logger.debug("Opening request socket...")

        try:
            self._zmq_context = zmq.Context()
            self._zmq_socket = self._zmq_context.socket(zmq.REP)
            self._zmq_socket.bind("tcp://*:3782")
            self._logger.info("Responder server ready.")

        except zmq.error.ZMQError as e:
            self._logger.error("Error starting the request server: " + str(e))
            return

        time.sleep(0.5)

        self._continue = True
        self._thread.start()

    def stop_listening(self):

        self._logger.debug("Closing responder socket...")

        self._continue = False
        if self._thread.is_alive():
            self._thread.join()

        self._zmq_socket.close()
        self._zmq_context.destroy()

        self._logger.debug("Done.")

    def _thread_method(self):

        self._logger.info("Listening for requests...")

        while self._continue:

            poller = zmq.Poller()
            poller.register(self._zmq_socket, zmq.POLLIN)

            events = poller.poll(500)

            if (len(events) > 0):

                request = self._zmq_socket.recv_string()
                self._logger.debug("Request received: " + request)

                response = self._process_request(request)

                self._logger.debug("Sending response: " + response)
                self._zmq_socket.send_string(response)

    def _process_request(self, request):

        try:

            message = ptdm_message.Message.from_string(request)

            self._logger.info("Received request: " + message.message_friendly_string())

            if (message.message_id() == ptdm_message.Message.REQ_PING):

                message.validate_parameters([])

                response = ptdm_message.Message.from_parts(ptdm_message.Message.RSP_PING, [])

            elif (message.message_id() == ptdm_message.Message.REQ_TEST_PUB_EMITS):

                message.validate_parameters([])

                self._publish_server.test_all_publishes()

                response = ptdm_message.Message.from_parts(ptdm_message.Message.RSP_DONE_TEST_PUB_EMITS, [])

            elif (message.message_id() == ptdm_message.Message.REQ_GET_DEVICE_ID):

                message.validate_parameters([])

                device_id = self._callback_client._on_request_get_device_id()

                response = ptdm_message.Message.from_parts(ptdm_message.Message.RSP_GET_DEVICE_ID, [device_id.value])

            elif (message.message_id() == ptdm_message.Message.REQ_GET_BRIGHTNESS):

                message.validate_parameters([])

                brightness = self._callback_client._on_request_get_brightness()

                response = ptdm_message.Message.from_parts(ptdm_message.Message.RSP_GET_BRIGHTNESS, [brightness])

            elif (message.message_id() == ptdm_message.Message.REQ_SET_BRIGHTNESS):

                message.validate_parameters([int])

                self._callback_client._on_request_set_brightness(int(message.parameters()[0]))

                response = ptdm_message.Message.from_parts(ptdm_message.Message.RSP_SET_BRIGHTNESS, [])

            elif (message.message_id() == ptdm_message.Message.REQ_INCREMENT_BRIGHTNESS):

                message.validate_parameters([])

                self._callback_client._on_request_increment_brightness()

                response = ptdm_message.Message.from_parts(ptdm_message.Message.RSP_INCREMENT_BRIGHTNESS, [])

            elif (message.message_id() == ptdm_message.Message.REQ_DECREMENT_BRIGHTNESS):

                message.validate_parameters([])

                self._callback_client._on_request_decrement_brightness()

                response = ptdm_message.Message.from_parts(ptdm_message.Message.RSP_DECREMENT_BRIGHTNESS, [])

            elif (message.message_id() == ptdm_message.Message.REQ_BLANK_SCREEN):

                message.validate_parameters([])

                self._callback_client._on_request_blank_screen()

                response = ptdm_message.Message.from_parts(ptdm_message.Message.RSP_BLANK_SCREEN, [])

            elif (message.message_id() == ptdm_message.Message.REQ_UNBLANK_SCREEN):

                message.validate_parameters([])

                self._callback_client._on_request_unblank_screen()

                response = ptdm_message.Message.from_parts(ptdm_message.Message.RSP_UNBLANK_SCREEN, [])

            else:

                self._logger.error("Unsupported request received: " + request)
                response = ptdm_message.Message.from_parts(ptdm_message.Message.RSP_ERR_UNSUPPORTED, [])

        except ValueError as e:

            self._logger.error("Error processing message: " + str(e))
            response = ptdm_message.Message.from_parts(ptdm_message.Message.RSP_ERR_MALFORMED, [])

        except Exception as e:

            self._logger.error("Unknown error processing message: " + str(e))
            response = ptdm_message.Message.from_parts(ptdm_message.Message.RSP_ERR_SERVER, [])

        self._logger.info("Sending response: " + response.message_friendly_string())

        return response.to_string()
