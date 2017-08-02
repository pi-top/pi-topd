
# Creates an IPC server for clients to connect to. Sends/receives messages 
# from these clients and responds accordingly.

class ptdm_ipc:

	def __init__(self, debug_level, controller):
		
      	self._debug_level = debug_level
      	self._controller = controller
