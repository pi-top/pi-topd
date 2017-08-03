
# Discovers which peripheral libraries are installed, and uses those to 
# detect, initialise, and communicate with the corresponding device

class ptdm_peripheral_manager:

	def __init__(self, debug_level):
		
		self._debug_level = debug_level
