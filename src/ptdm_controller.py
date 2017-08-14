# Instantiates and coordinates between the other classes

from ptdm_logger import Logger
import ptdm_hub_manager
import ptdm_peripheral_manager
import ptdm_publish_server
import ptdm_request_server
import time
import sys
import logging



LOG_LEVEL = logging.DEBUG


class Controller():

	def initialise(self):
		
		self._continue_running = True
		self._logger = Logger(LOG_LEVEL)

		self._logger.info("Initialising device manager")	

		#ptdm_hub_manager.initialise(self._logger)
		#ptdm_peripheral_manager.initialise(self._logger)
		ptdm_publish_server.initialise(self._logger)
		ptdm_request_server.initialise(self._logger, self)


	def run(self):

		self._logger.info("Running device manager")

		ptdm_publish_server.start_listening()
		ptdm_request_server.start_listening()

		while (self._continue_running):

			time.sleep(0.5)

		ptdm_request_server.stop_listening()
		ptdm_publish_server.stop_listening()

		sys.exit(0)

		
	def stop(self):

		self._logger.info("Stopping...")
		self._continue_running = False


	# Callback methods

	def _on_request_get_brightness(self):

		# Get the brightness from the hub manager

		return 100


	def _on_request_set_brightness(self, brightness):

		# Set the brightness in the hub manager
		print ("Brightness set to " + str(brightness))


	def _on_request_get_hub_info(self):

		# Get the device id
		return 1


