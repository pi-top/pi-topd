
# Creates a server for clients to connect to, and then responds to
# queries from these clients for device-related debugrmation.

import zmq
import time
import threading

_logger = None
_zmq_context = None
_zmq_socket = None
_thread = None
_continue = True
_continue = True

# Callback methods

_fn_on_get_brightness = None

def initialise(logger, fn_on_get_brightness):

	global _logger
	global _fn_on_get_brightness

	_logger = logger
	_fn_on_get_brightness = fn_on_get_brightness


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

			message = _zmq_socket.recv_string()
			_logger.debug ("Request received: " + message)
			
			response = _route_request(message)
			response_string = str(response)

			_logger.debug ("Sending response: " + response_string)
			_zmq_socket.send_string(response_string)


def _route_request(message):

	if ("brightness" in message):

		return _fn_on_get_brightness()

	else:

		_logger.error("Unknown request received: " + message)

		return "bad request"