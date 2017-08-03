# Instantiates and coordinates between the other classes

from ptdm_hub_manager import ptdm_hub_manager
from ptdm_peripheral_manager import ptdm_peripheral_manager
from ptdm_ipc_server import ptdm_ipc_server

class ptdm_controller:

	def __init__(self, debug_level):
		
		self._debug_level = debug_level
		self._hub_manager = ptdm_hub_manager(self._debug_level)
		self._peripheral_manager = ptdm_peripheral_manager(self._debug_level)
		self._ipc_server = ptdm_ipc_server(self._debug_level, self)


	def start(self):

		#self._ipc_server.send_message()
		self._ipc_server.start_listening()
		
		

	def on_get_brightness(self):

		# Get the brightness from the hub manager

		return 100