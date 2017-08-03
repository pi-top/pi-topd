# Instantiates and coordinates between the other classes

import ptdm_hub_manager
import ptdm_peripheral_manager
import ptdm_publish_server
import ptdm_logger

def initialise():
	
	ptdm_logger.info("Initialising device manager")	

	#ptdm_hub_manager.initialise(ptdm_logger)
	#ptdm_peripheral_manager.initialise(ptdm_logger)
	ptdm_publish_server.initialise(ptdm_logger, _on_get_brightness)

def run():

	ptdm_logger.info("Running device manager")

	ptdm_publish_server.start_listening()

	
def _on_get_brightness():

	# Get the brightness from the hub manager

	return 100