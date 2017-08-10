
# Creates a server for clients to connect to, and publishes state change messages
# to these clients

import zmq
import time
import ptdm_messages

_logger = None
_zmq_context = None
_zmq_socket = None
_continue = True

def initialise(logger):

	global _logger

	_logger = logger


def start_listening():

	global _zmq_context
	global _zmq_socket
	
	_logger.debug ("Opening publisher socket...")

	_zmq_context = zmq.Context()
	_zmq_socket = _zmq_context.socket(zmq.PUB)
	_zmq_socket.bind("tcp://*:3781")

	_logger.info ("Publish server ready...")


def stop_listening():
	
	_logger.debug ("Closing publisher socket...")

	_zmq_socket.close()
	_zmq_context.destroy()

	_logger.debug ("Done.")


def publish_brightness_changed(new_brightness):

	_logger.debug ("Publishing brightness changed")
	_send_message(ptdm_messages.PUB_BRIGHTNESS_CHANGED, [ new_brightness ])


def publish_peripheral_connected(peripheral_id):

	_logger.debug ("Publishing peripheral connected")
	_send_message(ptdm_messages.PUB_PERIPHERAL_CONNECTED, [ peripheral_id ])


def publish_peripheral_disconnected(peripheral_id):

	_logger.debug ("Publishing peripheral disconnected")
	_send_message(ptdm_messages.PUB_PERIPHERAL_DISCONNECTED, [ peripheral_id ])


def publish_shutdown_requested():

	_logger.debug ("Publishing shutdown requested")
	_send_message(ptdm_messages.PUB_SHUTDOWN_REQUESTED, [ ])


def publish_reboot_required():

	_logger.debug ("Publishing reboot required")
	_send_message(ptdm_messages.PUB_REBOOT_REQUIRED, [ ])


def publish_battery_charging_state_changed(connected_int):

	_logger.debug ("Publishing battery charging state changed")

	_send_message(ptdm_messages.PUB_BATTERY_CHARGING_STATE_CHANGED, [ connected_int ])


def publish_battery_capacity_changed(new_capacity):

	_logger.debug ("Publishing battery capacity changed")
	_send_message(ptdm_messages.PUB_BATTERY_CAPACITY_CHANGED, [ new_capacity ])


def publish_battery_time_remaining_changed(new_time):

	_logger.debug ("Publishing battery time remaining changed")
	_send_message(ptdm_messages.PUB_BATTERY_TIME_REMAINING_CHANGED, [ new_time ])


# Internal functions

def _send_message(message_id, parameters):

	message_to_send = ptdm_messages.build_message(message_id, parameters)

	_logger.debug ("Publishing message: " + message_to_send)
		
	_zmq_socket.send_string(message_to_send)