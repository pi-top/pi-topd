# Instantiates and coordinates between the other classes

import ptdm_hub_manager
import ptdm_peripheral_manager
import ptdm_publish_server
import ptdm_request_server
from ptdm_logger import Logger
import time
import signal
import sys
import logging

_continue_running = True
_logger = None


# Settings

LOG_LEVEL = logging.DEBUG


def initialise():
	
	global _logger

	_logger = Logger(LOG_LEVEL)

	_logger.info("Initialising device manager")	

	#ptdm_hub_manager.initialise(_logger)
	#ptdm_peripheral_manager.initialise(_logger)
	ptdm_publish_server.initialise(_logger)
	ptdm_request_server.initialise(_logger, _on_get_brightness, _on_set_brightness)


def run():

	_logger.info("Running device manager")

	ptdm_publish_server.start_listening()
	ptdm_request_server.start_listening()

	while (_continue_running):

		time.sleep(0.5)

	ptdm_request_server.stop_listening()
	ptdm_publish_server.stop_listening()

	sys.exit(0)

	
def stop():

	global _continue_running

	_continue_running = False


# Internal methods

def _on_get_brightness():

	# Get the brightness from the hub manager

	return 100


def _on_set_brightness(brightness):

	# Set the brightness in the hub manager
	print ("Brightness set to " + str(brightness))
	

# Capture interrupts

def _signal_handler(signal, frame):

	_logger.info("Signal received. Stopping...")
	stop()


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)
