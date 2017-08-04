
# Creates an IPC server for clients to connect to. Sends/receives messages 
# from these clients and responds accordingly.

import socketserver
import time
from threading import Thread

_logger = None
_on_get_brightness = None
_thread = None
_tcp_server = None

_max_clients = 5


class RequestHandler(socketserver.BaseRequestHandler):

	def handle(self):
		
		data = str(self.request.recv(1024).strip())

		_logger.info ("Received request:" + data)

		# Check the type of request and get a response

		if (True):

			response = _on_get_brightness()
			self.request.sendall(56)

		else:

			self.request.sendall("unknown request")

		_logger.info ("Reply sent")


def initialise(logger, on_get_brightness):

	global _logger
	global _on_get_brightness

	_logger = logger
	_on_get_brightness = on_get_brightness


def start_listening():

	global _thread

	_logger.info ("Opening server...")

	address = ("127.0.0.1", 30003)
	_tcp_server = socketserver.TCPServer(address, RequestHandler)

	_thread = Thread(target=_tcp_server.serve_forever)
	_thread.setDaemon(True)
	_thread.start()

	_thread.join()