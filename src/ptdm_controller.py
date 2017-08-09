# Instantiates and coordinates between the other classes

import ptdm_hub_manager
import ptdm_peripheral_manager
import ptdm_publish_server
import ptdm_request_server
import ptdm_logger
import time

def initialise():
	
	ptdm_logger.info("Initialising device manager")	

	#ptdm_hub_manager.initialise(ptdm_logger)
	#ptdm_peripheral_manager.initialise(ptdm_logger)
    
	ptdm_publish_server.initialise(ptdm_logger)
	ptdm_request_server.initialise(ptdm_logger)


def run():

	ptdm_logger.info("Running device manager")

	ptdm_publish_server.start_listening()
	ptdm_request_server.start_listening()

	time.sleep(30)

	ptdm_request_server.stop_listening()
	ptdm_publish_server.stop_listening()

	
def _on_get_brightness():

	# Get the brightness from the hub manager

	return 100