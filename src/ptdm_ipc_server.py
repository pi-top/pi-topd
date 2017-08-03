
# Creates an IPC server for clients to connect to. Sends/receives messages 
# from these clients and responds accordingly.

import zmq
import time

class ptdm_ipc_server:

	def __init__(self, debug_level, controller):
		
		self._debug_level = debug_level
		self._controller = controller

	def start_listening(self):

		print ("Opening socket...")

		self._context = zmq.Context()
		self._server_socket = self._context.socket(zmq.PUB)
		self._server_socket.bind("tcp://*:12537")

		time.sleep(5)

		for i in range(15):
			print ("Publishing message...")
			self._server_socket.send("test")
			time.sleep(5)

		print ("Closing...")

		self._server_socket.close()

		print ("Done.")

