
# Discovers which hub libraries are installed, and uses those to 
# determine the type of hub in use and communicate with it

from importlib import import_module

class HubManager():

	def initialise(self, logger, callback_client):

		self._logger = logger
		self._callback_client = callback_client
		self._active_hub_module = None


	def connect_to_hub(self):

		try:
			self._module_hub_v1 = self._import_module("pthub")	

			if (self._module_hub_v1.initialise() == True):
				self._active_hub_module = self._module_hub_v1
				self._logger.info("Connected to hub v1")

				return

		except Exception as e:
			self._logger.info("Failed to connect to a v1 hub")
			

		try:			
			self._module_hub_v2 = self._import_module("pthubv2")

			if (self._module_hub_v2.initialise() == True):
				self._active_hub_module = self._module_hub_v2
				self._logger.info("Connected to hub v2")

				return

		except Exception as e:
			self._logger.info("Failed to connect to a v2 hub")
			
		self._logger.error("Could not connect to a hub!")


	def get_brightness(self):

		if (self._active_hub_module == None):
			raise RuntimeError("No hub connected")

		return self._active_hub_module.get_brightness()


	def set_brightness(self, brightness):

		if (self._active_hub_module == None):
			raise RuntimeError("No hub connected")

		self._active_hub_module.set_brightness(brightness)


	def get_hub_info(self):

		if (self._active_hub_module == None):
			raise RuntimeError("No hub connected")

		return self._active_hub_module.get_hub_info()


	def _import_module(self, module_name):

		try:
			module_config_name = str(module_name + ".configuration")
			return import_module(module_config_name)

		except ImportError as e:
			print("Failed to import " + module_name + ". Error: " + str(e))
			raise e
