
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

	_logger.info ("Opening publisher socket...")

	_zmq_socket = _zmq_context.socket(zmq.PUB)
	_zmq_socket.bind("tcp://*:30003")

	time.sleep(5)

	for i in range(100):
		_logger.info ("Publishing message...")
		
		_zmq_socket.send("test")

		time.sleep(2)

	stop_listening()


def stop_listening():
	
	_logger.info ("Closing publisher socket...")

	_zmq_socket.close()

	_logger.info ("Done.")

