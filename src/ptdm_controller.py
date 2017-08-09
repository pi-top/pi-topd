# Instantiates and coordinates between the other classes

import ptdm_hub_manager
import ptdm_peripheral_manager
import ptdm_publish_server
import ptdm_request_server
import ptdm_logger
import time
import signal
import sys

_continue_running = True

def _signal_handler(signal, frame):

    ptdm_logger.info("Signal received. Stopping...")
    stop()


def initialise():
	
	ptdm_logger.info("Initialising device manager")	

	#ptdm_hub_manager.initialise(ptdm_logger)
	#ptdm_peripheral_manager.initialise(ptdm_logger)
    
	ptdm_publish_server.initialise(ptdm_logger)
	ptdm_request_server.initialise(ptdm_logger, _on_get_brightness)


def run():

	ptdm_logger.info("Running device manager")

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


def _on_get_brightness():

	# Get the brightness from the hub manager

	return 100


# Capture interrupts

signal.signal(signal.SIGINT, _signal_handler)