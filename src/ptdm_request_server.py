
# Creates a server for clients to connect to, and then responds to
# queries from these clients for device-related information.

import zmq
import time
import threading

_logger = None
_zmq_context = None
_zmq_socket = None
_thread = None
_continue = True
_continue = True

def initialise(logger):

	global _logger

	_logger = logger


def start_listening():

	global _zmq_context
	global _zmq_socket
	global _thread
	
	_logger.info ("Opening responder socket...")

	_zmq_context = zmq.Context()
	_zmq_socket = _zmq_context.socket(zmq.REP)
	_zmq_socket.bind("tcp://*:3782")

	time.sleep(0.5)

	_thread = threading.Thread(target=_thread_method)
	_thread.start()


def stop_listening():
	
	global _continue

	_logger.info ("Closing responder socket...")

	_continue = False
	_thread.join()

	_zmq_socket.close()

	_logger.info ("Done.")


def _thread_method():

	_logger.info ("Listening for requests...")

	while _continue:

		poller = zmq.Poller()
		poller.register(_zmq_socket, zmq.POLLIN)
		
		events = poller.poll(500)

		if (len(events) > 0):

			message = _zmq_socket.recv_string()
			_logger.info ("Request received: " + message)
			
			time.sleep(0.1)

			_logger.info ("Sending response...")
			_zmq_socket.send_string("Hello")