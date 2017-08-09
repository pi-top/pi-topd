
# Creates a server for clients to connect to, and publishes state change messages
# to these clients

import zmq
import time

_logger = None
_zmq_context = None
_zmq_socket = None
_continue = True

def initialise(logger):

	global _logger

	_logger = logger


def start_listening():

	global _zmq_context
	global _zmq_socket
	
	_logger.debug ("Opening publisher socket...")

	_zmq_context = zmq.Context()
	_zmq_socket = _zmq_context.socket(zmq.PUB)
	_zmq_socket.bind("tcp://*:3781")


def stop_listening():
	
	_logger.debug ("Closing publisher socket...")

	_zmq_socket.close()

	_logger.debug ("Done.")


def send_message(message):

    _logger.debug ("Publishing message: " + message)
	    
    _zmq_socket.send_text(message)