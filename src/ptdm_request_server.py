
# Creates a server for clients to connect to, and then responds to
# queries from these clients for device-related debugrmation.

import zmq
import time
import threading
import ptdm_messages

_logger = None
_zmq_context = None
_zmq_socket = None
_thread = None
_continue = True

# Callback methods

_fn_on_get_brightness = None
_fn_on_set_brightness = None

def initialise(logger, fn_on_get_brightness, fn_on_set_brightness):

	global _logger
	global _fn_on_get_brightness
	global _fn_on_set_brightness

	_logger = logger
	_fn_on_get_brightness = fn_on_get_brightness
	_fn_on_set_brightness = fn_on_set_brightness


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

		message_type, parameters = ptdm_messages.parse_message(request)

		if (message_type == ptdm_messages.REQ_PING):

			ptdm_messages.validate_parameters(parameters, 0)

			return ptdm_messages.build_message(ptdm_messages.RSP_PONG, [])

		elif (message_type == ptdm_messages.REQ_GET_HUB_INFO):

			ptdm_messages.validate_parameters(parameters, 0)

			device_id = _fn_on_get_hub_info()

			return ptdm_messages.build_message(ptdm_messages.RSP_GET_HUB_INFO, [ device_id ])

		elif (message_type == ptdm_messages.REQ_GET_BRIGHTNESS):

			ptdm_messages.validate_parameters(parameters, 0)

			brightness = _fn_on_get_brightness()

			return ptdm_messages.build_message(ptdm_messages.RSP_GET_BRIGHTNESS, [ brightness ])

		elif (message_type == ptdm_messages.REQ_SET_BRIGHTNESS):

			ptdm_messages.validate_parameters(parameters, 1)
			
			_fn_on_set_brightness(parameters[0])

			return ptdm_messages.build_message(ptdm_messages.RSP_SET_BRIGHTNESS, [])

		else:

			_logger.error("Unsupported request received: " + request)
			return ptdm_messages.build_message(ptdm_messages.RSP_ERR_UNSUPPORTED, [])

	except ValueError as ex:
		
		_logger.error("Error processing message: " + str(ex))
		return ptdm_messages.build_message(ptdm_messages.RSP_ERR_MALFORMED, [])

	except Exception as ex:

		_logger.error("Unknown error processing message: " + str(ex))
		return ptdm_messages.build_message(ptdm_messages.RSP_ERR_SERVER, [])
