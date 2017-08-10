# Message definitions


# Requests

REQ_PING							= 110
REQ_GET_HUB_INFO					= 111
REQ_GET_BRIGHTNESS 					= 112
REQ_SET_BRIGHTNESS 					= 113
REQ_GET_BATTERY_STATUS 				= 114


# Responses

RSP_ERR_SERVER						= 201
RSP_ERR_MALFORMED					= 202
RSP_ERR_UNSUPPORTED					= 203

RSP_PONG							= 210
RSP_GET_HUB_INFO					= 211
RSP_GET_BRIGHTNESS 					= 212
RSP_SET_BRIGHTNESS 					= 213


# Broadcast/published messages

PUB_BRIGHTNESS_CHANGED 				= 300
PUB_PERIPHERAL_CONNECTED			= 301
PUB_PERIPHERAL_DISCONNECTED			= 302
PUB_SHUTDOWN_REQUESTED				= 303
PUB_REBOOT_REQUIRED					= 304
PUB_BATTERY_CHARGING_STATE_CHANGED	= 305
PUB_BATTERY_CAPACITY_CHANGED		= 306
PUB_BATTERY_TIME_REMAINING_CHANGED	= 307


# Peripheral IDs

PID_PT_SPEAKER						= 0
PID_PT_PULSE						= 1


def parse_message(message):

	message_parts = message.split("|")

	if (len(message_parts) < 1): 

		raise ValueError("Message did not have an id")

	if (_is_integer(message_parts[0]) == False):

		raise ValueError("Message id was not an integer")

	return int(message_parts[0]), message_parts[1:]



def build_message(message_id, parameters):	

	message_to_send = str(message_id)

	for message_param in parameters:
		message_to_send += "|"
		message_to_send += str(message_param)

	return message_to_send


def validate_parameters(parameter, required_count):

	if (len(parameter) != required_count):
		raise ValueError("Message did not have the correct number of parameters (" + str(required_count) + ")")
		

def _is_integer(string):
	
	try: 
		int(string)
		return True

	except ValueError:
		return False