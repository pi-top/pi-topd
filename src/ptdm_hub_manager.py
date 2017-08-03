
# Discovers which hub libraries are installed, and uses those to 
# determine the type of hub in use and communicate with it


class ptdm_hub_manager:

	def __init__(self, debug_level):
		
		self._debug_level = debug_level
