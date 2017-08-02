
# Instantiates and coordinates between the other classes

class ptdm_controller:

	def __init__(self, debug_level):
		
      	self._debug_level = debug_level


    def start(self):

    	self.ipc_server = ptdm_ipc(self._debug_level, self)

    	# Do something cool