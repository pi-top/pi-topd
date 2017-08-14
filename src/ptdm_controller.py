# Instantiates and coordinates between the other classes

from ptdm_logger import Logger
from ptdm_hub_manager import HubManager
from ptdm_peripheral_manager import PeripheralManager
from ptdm_publish_server import PublishServer
from ptdm_request_server import RequestServer
import time
import sys
import logging

class Controller():

	def initialise(self, log_level):
		
		self._continue_running = True
		self._logger = Logger(log_level)

		self._logger.info("Initialising device manager")	

		# Create classes

		self._hub_manager = HubManager()
		self._peripheral_manager = PeripheralManager()
		self._publish_server = PublishServer()
		self._request_server = RequestServer()

		# Initialise

		self._hub_manager.initialise(self._logger, self)
		self._peripheral_manager.initialise(self._logger, self)
		self._publish_server.initialise(self._logger)
		self._request_server.initialise(self._logger, self)


	def run(self):

		self._logger.info("Running device manager")

		self._publish_server.start_listening()
		self._request_server.start_listening()

		while (self._continue_running):

			time.sleep(0.5)

		self._request_server.stop_listening()
		self._publish_server.stop_listening()

		sys.exit(0)

		
	def stop(self):

		self._logger.info("Stopping...")
		self._continue_running = False


	###########################################
	# Request server callback methods
	###########################################

	def _on_request_get_brightness(self):

		# Get the brightness from the hub manager

		return 100


	def _on_request_set_brightness(self, brightness):

		# Set the brightness in the hub manager
		print ("Brightness set to " + str(brightness))


	def _on_request_get_hub_info(self):

		# Get the device id
		return 1


	###########################################
	# Hub Manager callback methods
	###########################################
	