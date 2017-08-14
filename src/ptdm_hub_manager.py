
# Discovers which hub libraries are installed, and uses those to 
# determine the type of hub in use and communicate with it

class HubManager():

	def initialise(self, logger, callback_client):

		self._logger = logger
		self._callback_client = callback_client


	def get_brightness(self):

		return 100


	def set_brightness(self, brightness):

		print ("Brightness set to " + str(brightness))


	def get_hub_info(self):

		return 1
