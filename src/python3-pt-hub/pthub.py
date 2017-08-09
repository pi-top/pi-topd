#!#!/usr/bin/env python

from datetime import datetime
from os import path
from os import remove
import subprocess
from time import sleep
from shutil import which
import enum
import threading
from sys import exit
from os import rename
from os import path
from os import makedirs

# Useful directories
_pt_sys_root_dir = '/etc/pi-top'
_hub_root_dir = _pt_sys_root_dir + '/pt-hub'

if not path.exists(_hub_root_dir):
    makedirs(_hub_root_dir)

# Time to pause between command sends
cycle_sleep_time = 0.25

#########
# State #
#########

# ENUMS
class MyEnum(enum.Enum):
    """Base enum class, with value fetching"""
    @classmethod
    def has_value(self, value):
        return value in self.__members__


class StateChangeType(MyEnum):
    """A simple state change type class, used by StateChange"""
    brightness = 'brightness'
    screen = 'screen'
    init = 'init'


class ScreenOperations(MyEnum):
    """A simple screen operations enum"""
    blank = 'blank'
    unblank = 'unblank'


# CLASSES
class Debug:
    """A simple debug class"""
    stdout = False
    log_to_file = True
    _current_log = _hub_root_dir + '/session_current.log'
    _previous_log = _hub_root_dir + '/session_previous.log'
    _print_ctr = None

    def __init__(self, print_counter):
        self._move_current_log_to_previous()
        self._print_ctr = print_counter

        # Make sure files exist
        self.touchFileIfDoesntExist(self._current_log)
        self.touchFileIfDoesntExist(self._previous_log)

    def touchFileIfDoesntExist(self, file_path):
        try:
            fh = open(file_path,'r')
        except:
        # if file does not exist, create it
            fh = open(file_path,'w')

    def _move_current_log_to_previous(self):
        if _file_exists(self._previous_log):
            # Remove previous output log
            remove(self._previous_log)

        if _file_exists(self._current_log):
            # Move last session's log to previous output log
            rename(self._current_log, self._previous_log)

    def _print_and_log(self, text, write_to_log):

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        if debug.stdout:
            print(timestamp + " " + text)

        if write_to_log and self.log_to_file:
            self._print_ctr._current += 1
            if self._print_ctr._current >= self._print_ctr._max:
                self._move_current_log_to_previous()

            with open(self._current_log, "a") as f:
                f.write(timestamp + " " + text + "\n")


class StateChange:
    """A simple state change class"""
    _type = None
    _operation = None

    def __init__(self, type, operation):
        permitted_types = [item.value for item in StateChangeType]
        if type.value in permitted_types:
            if type.value == 'brightness':
                if state.valid_brightness(operation):
                    self._type = type
                    self._operation = operation
                else:
                    print("Unable to create class - invalid operation")
            elif type.value == 'screen':
                self._type = type
                if ScreenOperations.has_value(operation):
                    self._type = type
                    self._operation = operation
                else:
                    print("Unable to create class - invalid operation")
            elif type.value == 'init':
                self._type = type
                if operation == True:
                    self._type = type
                    self._operation = operation
                else:
                    print("Unable to create class - invalid operation")
            else:
                print("Internal error: Unable to detect supposedly valid type")
                print("TYPE: " + str(type.value))

        else:
            print("Unable to create class - invalid type")
            print("TYPE: " + str(type))
            print("PERMITTED: " + str(permitted_types))


class MessageReceiveClient:
    brightness_change_func = None
    screen_change_func = None
    shutdown_change_func = None
    device_name_change_func = None

    def __init__(self, brightness_client=None, screen_client=None, shutdown_client=None, device_name_client=None):
        if brightness_client != None:
            if callable(brightness_client):
                brightness_change_func = brightness_client
            else:
                print("Message receive client: Brightness change parameter not a valid function")
        
        if screen_client != None:
            if screen_client != None and callable(screen_client):
                screen_change_func = screen_client
            else:
                print("Message receive client: Screen state change parameter not a valid function")

        if shutdown_client != None:
            if shutdown_client != None and callable(shutdown_client):
                shutdown_change_func = shutdown_client
            else:
                print("Message receive client: Shutdown state change parameter not a valid function")

        if device_name_client != None:
            if device_name_client != None and callable(device_name_client):
                device_name_change_func = device_name_client
            else:
                print("Message receive client: Device name change parameter not a valid function")


class State:
    device_id_path = _pt_sys_root_dir + '/device_id' # Needed for reboots...
    reboot_state_path = _hub_root_dir + '/reboot.state'

    _debug = None
    _client = None

    previous_brightness = 10
    current_brightness = 10
    screen_off = 0
    shutdown = 0
    device_name = ''

    init_state = StateChange(StateChangeType.init, True)
    queued_changes = [ init_state ]

    def __init__(self, debug_instance, previous_brightness=10, current_brightness=10, screen_off=0, shutdown=0, device_name='', client_instance=None):
        self._debug = debug_instance
        self._client = client_instance

    def _write_device_name_to_file(self):
        debug._print_and_log("Setting device ID: " + state.device_name, True)
        f = open(self.device_id_path, 'w')
        f.write(state.device_name + "\n")
        f.close()

    def init_handle_device_name(self):
        if _file_exists(self.reboot_state_path):
            debug._print_and_log("Came from reboot - device ID is already set", True)
            state.config_device_name_from_reboot()
        else:
            # Clear device ID from path
            f = open(self.device_id_path, 'w').close()

    def set_screen_off_from_current_screen_blank_state(self):
        xscreensaver_cmd = "xscreensaver-command"
        if which(xscreensaver_cmd) is not None:
            # Check if response is valid
            # Check current screen_off state
            self._debug._print_and_log("Reading screen state", False)
            try:
                output = subprocess.check_output([xscreensaver_cmd, "-time"])
                current_screen_state = output.split()[3]
            except subprocess.CalledProcessError:
                # Assume non-blanked
                current_screen_state = "non-blanked"

            if current_screen_state == "blanked":
                self.set_screen_off(1)
            else:
                self.set_screen_off(0)

    def config_device_name_from_reboot(self):
        remove(reboot_state_path)
        device_id = "ALREADY_SET"
        # Need to rewrite to current device ID back to file
        f = open(self.device_id_path, 'r')
        self.set_device_name(f.read().strip())
        f.close()

    def pop_from_queue(self):
        if len(self.queued_changes) > 0:
            state_change = self.queued_changes[0]
            self.queued_changes.remove(self.queued_changes[0])
        else:
            state_change = None

        return state_change

    def valid_brightness(self, val):
        return _represents_int(val) and (int(val) >= 0) and (int(val) <= 10)

    def emit_brightness_change_msg(self, msg):
        client_set = self._client != None
        if client_set:
            func_set = self._client.brightness_change_func != None
            if func_set:
                return self._client.brightness_change_func()

    def emit_screen_change_msg(self, msg):
        client_set = self._client != None
        if client_set:
            func_set = self._client.screen_change_func != None
            if func_set:
                return self._client.screen_change_func()

    def emit_shutdown_change_msg(self, msg):
        client_set = self._client != None
        if client_set:
            func_set = self._client.shutdown_change_func != None
            if func_set:
                return self._client.shutdown_change_func()

    def emit_device_name_change_msg(self, msg):
        client_set = self._client != None
        if client_set:
            func_set = self._client.device_name_change_func != None
            if func_set:
                return self._client.device_name_change_func()

    def update_previous_brightness(self):
        self.previous_brightness = self.current_brightness

    def set_current_brightness(self, val):
        if self.valid_brightness(val):
            self.current_brightness = val
            self.emit_brightness_change_msg(val)

    def set_screen_off(self, val):
        self.screen_off = val
        self.emit_screen_change_msg(val)

    def handle_shutdown(self, val):
        self.shutdown = val
        shutdown_func_not_defined = (self.shutdown_change_func == None)
        shutdown_confirmed = (self.emit_shutdown_change_msg(val) == True)
        if shutdown_func_not_defined or shutdown_confirmed:
            self.do_shutdown()

    def do_shutdown(self):
        # Shutdown Pi
        subprocess.call(['sudo', 'shutdown', '-h', 'now'])

    def set_device_name(self, val):
        self.device_name = val
        self.emit_device_name_change_msg(val)
        # Write device ID to path
        self._write_device_name_to_file()


class SPIHandler:
    spi = None
    _debug = None
    _state = None

    def __init__(self, debug_instance, state_instance):
        self._debug = debug_instance
        self._state = state_instance
        self._setup_spi()
        self._get_init_data()
        self._state.update_previous_brightness()

    def _setup_spi(self):
        if self.spi == None:
            from spidev import SpiDev
            self.spi = SpiDev()
            self.spi.open(0, 1)  # Bus 0, Chip Select 1
            self.spi.max_speed_hz = 9600
            self.spi.mode = 0b00
            self.spi.bits_per_word = 8
            self.spi.cshigh = True
            self.spi.lsbfirst = False

    def _process_spi_resp(self, resp, init=False):

        # Check shutdown bit
        shutdown_bit = resp[7]
        if shutdown_bit == "1":
            # Increment shutdown counter
            _shutdown_ctr._current += 1

            if _shutdown_ctr._current == _shutdown_ctr._max:
                # Reset counter
                _shutdown_ctr._current = 0
                
                self._state.handle_shutdown()

        elif _shutdown_ctr._current != 0:
            _shutdown_ctr._current = 0

        # Convert brightness binary to int
        received_brightness_value = int(resp[1:5], 2)

        # If received brightness value is valid
        if received_brightness_value >= 0 and received_brightness_value <= 10:
            if init:
                self._state.set_current_brightness(received_brightness_value)
            else:
                no_new_brightness = (_sent_new_br_ctr._current == 0)
                new_br_confirmed = (_sent_new_br_ctr._current == _sent_new_br_ctr._max)
                if no_new_brightness or new_br_confirmed:
                    # If hub is reporting a new brightness
                    if received_brightness_value != self._state.current_brightness:
                        # If second time the hub is reporting a new brightness
                        if received_brightness_value == self._state.previous_brightness:
                            # Set current brightness level to hub's if valid
                            self._state.set_current_brightness(received_brightness_value)
                    else:
                        # If second time the hub is reporting a new brightness
                        if received_brightness_value != self._state.previous_brightness:
                            # Set current brightness level to hub's
                            self._state.set_current_brightness(received_brightness_value)
                    
                    _sent_new_br_ctr._current = 0
                    self._state.update_previous_brightness()
                else:
                    # Increment counter to wait for hub to respond
                    _sent_new_br_ctr._current += 1

    def _transceive_spi(self, bits_to_send):
        hex_str_to_send = '0x' + str(hex(bits_to_send))[2:].zfill(2)
        bin_str_to_send = '{0:b}'.format(int(hex_str_to_send[2:], 16)).zfill(8)
        self._debug._print_and_log("Pi: " + bin_str_to_send, True)
        
        # Initiate receiving communication from hub
        self.spi.cshigh = False
        # Transfer data with hub
        resp = self.spi.xfer2([bits_to_send], self.spi.max_speed_hz)
        self.spi.cshigh = True

        resp_hex = hex(resp[0])
        resp_hex_str = '0x' + str(resp_hex)[2:].zfill(2)
        resp_bin_str = '{0:b}'.format(int(resp_hex_str[2:], 16)).zfill(8)
        self._debug._print_and_log("Hub: " + resp_bin_str, True)

        return resp_bin_str

    def _get_init_data(self):

        valid = False
        init_attempt = 0

        # This will cycle through forever until the Pi communicates with the hub
        while valid is not True:
            # Send 0xFF to get data from hub
            resp_bin_str = self._transceive_spi(255)

            byte_type = _determine_byte(resp_bin_str)
            if byte_type == "device_id":
                self._debug._print_and_log("Valid response from hub - DEVICE ID", True)
                # Process SPI resp, store brightness signal for check next loop
                _process_device_name(resp_bin_str)
                valid = True
            elif byte_type == "VALID_STATE":
                self._debug._print_and_log("Valid response from hub - STATE", True)
                valid = True
            else:
                self._debug._print_and_log("Invalid response from hub", True)

            sleep(cycle_sleep_time)

        self._process_spi_resp(resp=resp_bin_str, init=True)


class Counter:
    """A simple counter class"""
    _current = 0
    _max = 0

    def __init__(self, current, max):
        self._current = current
        self._max = max


######################
# EXTERNAL FUNCTIONS #
######################
def start():
    initialise()
    main_thread.start()

def stop():
    main_thread.join()

def increment_brightness():
    current_brightness = get_brightness_state()

    if current_brightness < 10:
        _add_state_change_to_stack(StateChangeType.brightness,
            current_brightness + 1)


def decrement_brightness():
    current_brightness = get_brightness_state()

    if current_brightness > 0:
        _add_state_change_to_stack(StateChangeType.brightness,
                                   current_brightness - 1)


def set_brightness(brightness_val):
    if state.valid_brightness(brightness_val):
        _add_state_change_to_stack(StateChangeType.brightness,
                                   brightness_val)
    else:
        print("Not a valid brightness - doing nothing")


def blank_screen():
    _add_state_change_to_stack(StateChangeType.screen,
                               ScreenOperations.blank)


def unblank_screen():
    _add_state_change_to_stack(StateChangeType.screen,
                               ScreenOperations.unblank)


def get_brightness_state():
    return state.current_brightness


def get_screen_off_state():
    return state.screen_off


def get_shutdown_state():
    return state.shutdown


def get_device_name_state():
    return state.device_name


def register_client(brightness_change_func = None,
                    screen_change_func = None,
                    shutdown_change_func = None,
                    device_name_change_func = None):

    client.brightness_change_func = brightness_change_func
    client.screen_change_func = screen_change_func
    client.shutdown_change_func = shutdown_change_func
    client.device_name_change_func = device_name_change_func


def set_logging(stdout=False, log_to_file=True):
    debug.stdout = stdout
    debug.log_to_file = log_to_file


def set_speed(no_of_polls_per_second=4):
    global cycle_sleep_time

    cycle_sleep_time = float(1/no_of_polls_per_second)

######################
# INTERNAL FUNCTIONS #
######################

def _append_to_queued_state_changes(state_change):

    state.queued_changes.append(state_change)

def _add_state_change_to_stack(state_change_type, state_change_operation):
    pending_state_change = StateChange(state_change_type,
                                       state_change_operation)
    _add_state_change_class_to_stack(pending_state_change)


def _add_state_change_class_to_stack(pending_state_change):
    valid_type = (pending_state_change._type != None)
    valid_operation = (pending_state_change._operation != None)
    if valid_type and valid_operation:
        _append_to_queued_state_changes(pending_state_change)
    else:
        print("Unable to process state change - invalid type or operation")


def _parity_of(int_type):
    '''
    Calculates the parity of an integer,
    returning 0 if there are an even number of set bits,
    and 1 if there are an odd number
    '''
    parity = 0
    for bit in bin(int_type)[2:]:
        parity ^= int(bit)
    return parity


def _represents_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def _parse_state_to_bits():

    # Set bits to send according to state variables
    state_change = state.pop_from_queue()

    # If state is to change, update appropriate bit(s)
    if state_change is not None:
    
        if state_change._type.value == 'screen':
            if state_change._operation == 'blank':
                state.set_screen_off(1)
            elif state_change._operation == 'unblank':
                state.set_screen_off(0)
            else:
                print("Unrecognised screen state change - unable to parse into bits. Ignoring...")
        
        elif state_change._type.value == 'brightness':
            if _represents_int(state_change._operation):
                # Manually set brightness level
                # Check that brightness level is valid
                brightness_level = int(state_change._operation)
                if brightness_level >= 0 and brightness_level <= 10:
                    # Set brightness bits to desired level
                    state.set_current_brightness(brightness_level)
                    _sent_new_br_ctr._current = 1

    br_parity_bits = str(_parity_of(state.current_brightness))
    state_parity_bits = str(_parity_of((2 * int(state.screen_off)) + state.shutdown))
    
    if state_change is not None:
        debug._print_and_log("Brightness parity: " + str(_parity_of(state.current_brightness)), True)
        debug._print_and_log("State parity: " + state_parity_bits, True)

    # Determine new bits to send
    # bs = bitshifted
    # br = brightness
    # par = parity
    bs_br_par = (128 * int(br_parity_bits))
    bs_br = (8 * state.current_brightness)
    bs_state_par = (4 * int(state_parity_bits))
    bs_screen_off = (2 * int(state.screen_off))
    bits_to_send = bs_br_par + bs_br + bs_state_par + bs_screen_off + state.shutdown
    # e.g. bits = "10101010"
    # brightness parity = 1
    # brightness = 5
    # state parity = 0
    # screen_off = 1
    # shutdown = 0

    return bits_to_send


def _determine_byte(resp):

    # Check parity bit
    parity_bit = resp[0]
    brightness = resp[1:5]

    if parity_bit == "0" and brightness == "1111":
        return "device_id"
    else:
        correct_parity_val = str(_parity_of(int(resp[1:8], 2)))

        if parity_bit != correct_parity_val:
            debug._print_and_log("Invalid parity bit", True)
            return "INVALID"

        # Check that screen_off bit has valid value
        # (i.e. 1 if lid is 0 or matches state sent by Pi)
        lid_bit = resp[5]
        screen_off_bit = resp[6]

        if lid_bit == "0" and screen_off_bit == "0":
            debug._print_and_log("Invalid: lid cannot be closed and screen on", True)
            return "INVALID"
        # Lid is open and screen_off does not match
        elif lid_bit == "1" and screen_off_bit != str(state.screen_off):
            return "INVALID"

        # If none of the parity bits are wrong and state.screen_off
        # is in the correct state, then return True
        return "VALID_STATE"


def _process_device_name(resp):
    # Get ID from resp_bin_str and write to global variable device_id
    device_id = resp[5:8]

    # Parse device_id to a name
    if device_id == "000":
        state.set_device_name("pi-top")
    elif device_id == "001":
        state.set_device_name("pi-topCEED")


def _file_exists(file_path):
    if not file_path:
        return False
    elif not path.isfile(file_path):
        return False
    else:
        return True


def initialise():
    global spi_handler

    state.set_screen_off_from_current_screen_blank_state()
    state.init_handle_device_name()
    spi_handler = SPIHandler(debug, state)


def communicate():
    if spi_handler == None:
        print("FATAL ERROR: SPI has not been initialised - call initialise() first")
        exit()


    # Set bits to transfer accordingly
    bits_to_send = _parse_state_to_bits()

    # Transmit bits and capture response in hex
    resp_bin_str = spi_handler._transceive_spi(bits_to_send)

    byte_type = _determine_byte(resp_bin_str)
    # Determine if received byte represents device ID or state
    if byte_type == "device_id" and state.device_name == "":
        debug._print_and_log("Valid response from hub - DEVICE ID", False)
        # Process SPI resp, store brightness signal for check next loop
        _process_device_name(resp_bin_str)
    elif byte_type == "VALID_STATE":
        
        if state.device_name is "":
            _stop_get_device_id_ctr._current += 1

            # IF MANY STATES HAVE BEEN RECEIVED, AND ID NOT SET, SET TO PI-TOP
            if _stop_get_device_id_ctr._current is _stop_get_device_id_ctr._max:
                state.set_device_name("pi-top")

        debug._print_and_log("Valid response from hub - STATE", False)
        # Process SPI resp, store brightness signal for check next loop
        spi_handler._process_spi_resp(resp_bin_str)
    else:
        debug._print_and_log("Invalid response from hub", True)

    debug._print_and_log("", True)


def main_thread_loop():
    '''
        ///////////////////////////
        // MAIN CODE STARTS HERE //
        ///////////////////////////
    '''

    initialise()

    while main_thread.is_alive():
        communicate()
        sleep(cycle_sleep_time)



# CLASS INSTANCES
_print_ctr = Counter(current=0, max=10000)

# Ensures hub doesn't reset stored brightness value before updated value sends
_sent_new_br_ctr = Counter(current=0, max=3)
_shutdown_ctr = Counter(current=0, max=2)
# Necessary to set pi-top ID when firmware does not send ID
_stop_get_device_id_ctr = Counter(current=0, max=10)

debug = Debug(_print_ctr)
client = MessageReceiveClient()
state = State(debug)
spi_handler = None

main_thread = threading.Thread(target=main_thread_loop)