
# Creates an IPC server for clients to connect to. Sends/receives messages 
# from these clients and responds accordingly.

import zmq
import time

_logger = None
_controller_callback = None
_zmq_context = None
_zmq_socket = None


def initialise(logger, controller):

	global _logger
	global _controller_callback
	global _zmq_context

	_logger = logger
	_controller_callback = controller

	_zmq_context = zmq.Context()


def start_listening():

	global _zmq_socket

	_logger.info ("Opening responder socket...")

	_zmq_socket = _zmq_context.socket(zmq.REP)
	_zmq_socket.bind("tcp://127.0.0.1:30004")



def stop_listening():
	
	_logger.info ("Closing responder socket...")

	_zmq_socket.close()

	_logger.info ("Done.")

