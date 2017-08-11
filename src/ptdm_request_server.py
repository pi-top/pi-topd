
# Creates a server for clients to connect to, and then responds to
# queries from these clients for device-related debugrmation.

import zmq
import time
import threading
from ptdm_messages import Message

_logger = None
_zmq_context = None
_zmq_socket = None
_thread = None
_continue = True

# Callback methods

_fn_on_get_brightness = None
_fn_on_set_brightness = None
_fn_on_get_hub_info = None

def initialise(logger, fn_on_get_brightness, fn_on_set_brightness, fn_on_get_hub_info):

	global _logger
	global _fn_on_get_brightness
	global _fn_on_set_brightness
	global _fn_on_get_hub_info

	_logger = logger
	_fn_on_get_brightness = fn_on_get_brightness
	_fn_on_set_brightness = fn_on_set_brightness
	_fn_on_get_hub_info = fn_on_get_hub_info


def start_listening():

	global _zmq_context
	global _zmq_socket
	global _thread
	
	_logger.debug ("Opening responder socket...")

	_zmq_context = zmq.Context()
	_zmq_socket = _zmq_context.socket(zmq.REP)
	_zmq_socket.bind("tcp://*:3782")

	time.sleep(0.5)

	_thread = threading.Thread(target=_thread_method)
	_thread.start()


def stop_listening():
	
	global _continue

	_logger.debug ("Closing responder socket...")

	_continue = False
	_thread.join()

	_zmq_socket.close()
	_zmq_context.destroy()

	_logger.debug ("Done.")


def _thread_method():

	_logger.info ("Listening for requests...")

	while _continue:

		poller = zmq.Poller()
		poller.register(_zmq_socket, zmq.POLLIN)
		
		events = poller.poll(500)

		if (len(events) > 0):

			request = _zmq_socket.recv_string()
			_logger.info ("Request received: " + request)
			
			response = _process_request(request)

			_logger.info ("Sending response: " + response)
			_zmq_socket.send_string(response)


def _process_request(request):

	try:

		message = Message(request)

		if (message.message_id() == Message.REQ_PING):

			message.validate_parameters([])

			return Message.build_message_string(Message.RSP_PING, [])

		elif (message.message_id() == Message.REQ_GET_HUB_INFO):

			message.validate_parameters([])

			device_id = _fn_on_get_hub_info()

			return Message.build_message_string(Message.RSP_GET_HUB_INFO, [ device_id ])

		elif (message.message_id() == Message.REQ_GET_BRIGHTNESS):

			message.validate_parameters([])

			brightness = _fn_on_get_brightness()

			return Message.build_message_string(Message.RSP_GET_BRIGHTNESS, [ brightness ])

		elif (message.message_id() == Message.REQ_SET_BRIGHTNESS):

			message.validate_parameters([ int ])
			
			_fn_on_set_brightness(int(message.parameters()[0]))

			return Message.build_message_string(Message.RSP_SET_BRIGHTNESS, [])

		else:

			_logger.error("Unsupported request received: " + request)
			return Message.build_message_string(Message.RSP_ERR_UNSUPPORTED, [])

	except ValueError as ex:
		
		_logger.error("Error processing message: " + str(ex))
		return Message.build_message_string(Message.RSP_ERR_MALFORMED, [])

	except Exception as ex:

		_logger.error("Unknown error processing message: " + str(ex))
		return Message.build_message_string(Message.RSP_ERR_SERVER, [])
