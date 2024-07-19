import logging
import threading
import traceback
from enum import Enum
from time import sleep

from pitop.common.common_ids import DeviceID
from pitop.common.counter import Counter

logger = logging.getLogger(__name__)

_spi_handler = None
_main_thread = None
_run_main_thread = False

# Time to pause between command sends
_cycle_sleep_time = 0.25


class SPIResponseType(Enum):
    """A simple state change type class, used by StateChange."""

    invalid = 0
    device_id = 1
    state = 2


class SPIStateChangeType(Enum):
    """A simple state change type class, used by StateChange."""

    brightness = "brightness"
    screen = "screen"
    init = "init"


class SPIScreenOperations(Enum):
    """A simple screen operations enum."""

    blank = "blank"
    unblank = "unblank"

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)


class StateChange:
    """A simple state change class."""

    def __init__(self, type, operation):
        permitted_types = [item.value for item in SPIStateChangeType]
        if type.value in permitted_types:
            if type == SPIStateChangeType.brightness:
                if _spi_handler._state.valid_brightness(operation):
                    self._type = type
                    self._operation = operation
                else:
                    logger.error(
                        "Unable to create class - invalid operation (brightness)"
                    )
            elif type == SPIStateChangeType.screen:
                self._type = type
                if SPIScreenOperations.has_value(operation.value):
                    self._operation = operation
                else:
                    logger.error("Unable to create class - invalid operation (screen)")
            elif type == SPIStateChangeType.init:
                self._type = type
                if operation is True:
                    self._operation = operation
                else:
                    logger.error("Unable to create class - invalid operation (init)")
            else:
                logger.error("Unable to detect supposedly valid type")
                logger.error("TYPE: " + str(type.value))

        else:
            logger.error("Unable to create class - invalid type")
            logger.error("TYPE: " + str(type))
            logger.error("PERMITTED: " + str(permitted_types))


class SPIHandler:
    def __init__(self, state_instance):
        self._shutdown_ctr = Counter(2)

        logger.debug("\t\tCreating SPI handler")
        self._state = state_instance
        self.spi = None

        logger.debug("\t\t\tSetting up SPI")
        self._setup_spi()

        logger.debug("\t\t\tGetting initial state data")
        assert self._get_state_from_hub(init=True)

        init_state = StateChange(SPIStateChangeType.init, True)
        self.queued_changes = [init_state]

    def _update_state_from_pending_state_change(self, state_change_to_send):
        # If state is to change, update appropriate bit(s)
        if state_change_to_send is not None:

            if state_change_to_send._type == SPIStateChangeType.screen:
                if state_change_to_send._operation == SPIScreenOperations.blank:
                    self._state.set_screen_blanked()
                elif state_change_to_send._operation == SPIScreenOperations.unblank:
                    self._state.set_screen_unblanked()
                else:
                    msg = "Unrecognised screen state change"
                    msg += " - unable to parse into bits. Ignoring..."
                    logger.info(msg)

            elif state_change_to_send._type == SPIStateChangeType.brightness:

                if _represents_int(state_change_to_send._operation):
                    brightness_level = int(state_change_to_send._operation)
                    if brightness_level >= 0 and brightness_level <= 10:
                        self._state.set_brightness(brightness_level)

    def transceive_and_process(self):
        state_change_to_send = self.pop_from_queue()
        self._update_state_from_pending_state_change(
            state_change_to_send
        )  # Should this be here?

        # Set bits to send according to state variables
        if state_change_to_send is not None:
            # Pi's current state
            bits_to_send = self._parse_state_to_bits()
        else:
            # Probe for hub's state
            bits_to_send = 255

        hub_response_bstring = self._transceive_spi(bits_to_send)
        byte_type = self._determine_byte(hub_response_bstring)

        # Determine if received byte represents device ID or state
        if byte_type == SPIResponseType.device_id:

            logger.debug("Valid response from hub - DEVICE ID")
            self._process_device_id(hub_response_bstring)

        elif byte_type == SPIResponseType.state:

            self._process_spi_resp(hub_response_bstring)

            # State update has been sent to hub: perform another transceive to sync states
            self._get_state_from_hub(process_state=False)

        else:

            logger.warning("Invalid response from hub")
            return False

        return True

    def pop_from_queue(self):
        if len(self.queued_changes) > 0:
            state_change_to_send = self.queued_changes[0]
            self.queued_changes.remove(self.queued_changes[0])
        else:
            state_change_to_send = None

        return state_change_to_send

    def _process_device_id(self, resp):
        device_id = resp[5:8]

        if device_id == "000":
            logger.info("Hub reports it's a pi-top v1")
            self._state.set_device_id(DeviceID.pi_top)
        elif device_id == "001":
            logger.info("Hub reports it's a CEED")
            self._state.set_device_id(DeviceID.pi_top_ceed)

    def _parity_of(self, int_type):
        """Calculates the parity of an integer, returning 0 if there are an
        even number of set bits, and 1 if there are an odd number."""
        parity = 0
        for bit in bin(int_type)[2:]:
            parity ^= int(bit)
        return parity

    def _parse_state_to_bits(self):
        br_parity_bits = str(self._parity_of(self._state._brightness))
        scaled_screen_off = 2 * int(self._state._screen_blanked)
        state_bits_val = scaled_screen_off + self._state._shutdown
        state_parity_bits = str(self._parity_of(state_bits_val))

        # Determine new bits to send
        # bs = bitshifted
        # br = brightness
        # par = parity
        bs_br_par = 128 * int(br_parity_bits)
        bs_br = 8 * self._state._brightness
        bs_state_par = 4 * int(state_parity_bits)
        bs_screen_off = 2 * int(self._state._screen_blanked)
        bits_to_send = bs_br_par
        bits_to_send += bs_br
        bits_to_send += bs_state_par
        bits_to_send += bs_screen_off
        bits_to_send += self._state._shutdown
        # e.g. bits = "10101010"
        # brightness parity = 1
        # brightness = 5
        # state parity = 0
        # screen_off = 1
        # shutdown = 0

        return bits_to_send

    def _setup_spi(self):
        if self.spi is None:
            from spidev import SpiDev

            self.spi = SpiDev()
            self.spi.open(0, 1)
            self.spi.max_speed_hz = 9600
            self.spi.mode = 0b00
            self.spi.bits_per_word = 8
            self.spi.lsbfirst = False

    def _determine_byte(self, resp):
        # Check parity bit
        parity_bit_brightness = resp[0]
        brightness = resp[1:5]

        if parity_bit_brightness == "0" and brightness == "1111":
            return SPIResponseType.device_id
        else:
            correct_parity_val = str(self._parity_of(int(resp[1:8], 2)))

            if parity_bit_brightness != correct_parity_val:
                logger.warning("Invalid parity bit")
                return SPIResponseType.invalid

            return SPIResponseType.state

    def _process_spi_resp_shutdown(self, spi_shutdown_bit_int):
        if spi_shutdown_bit_int == 1:

            # Increment shutdown counter
            self._shutdown_ctr.increment()

            logger.info(
                "Received shutdown indication from hub ("
                + str(self._shutdown_ctr.current)
                + " of "
                + str(self._shutdown_ctr.max)
                + ")"
            )

            if self._shutdown_ctr.maxed():
                self._shutdown_ctr.reset()
                self._state.set_shutdown(1)

        else:
            self._shutdown_ctr.reset()

    def _process_spi_resp(self, resp, init=False):
        # Message from hub bits:

        # 0     : check sum: set if odd number of set bits in rest of message
        # 1 - 4 : Brightness of screen backlight
        # 5     : Lid state, 1 if open, 0 if closed
        # 6     : Screen blank state, 0 if unblanked, 1 if blanked
        # 7     : Shutdown requested from hub, 1 if shutting down

        # If we're communicating, but we still haven't decided what device
        # we're on, then we must be on a CEED, as if we were on a pi-top v1,
        # we would have identified this via connecting to the battery on i2c.

        if int(resp) != 0 and self._state._device_id == DeviceID.unknown:
            logger.info("Received comms from hub - assuming we're on a CEED")
            self._state.set_device_id(DeviceID.pi_top_ceed)

        # Check shutdown bit

        spi_shutdown_bit_int = int(resp[7])
        self._process_spi_resp_shutdown(spi_shutdown_bit_int)

        spi_screen_off_state = int(resp[6])
        if spi_screen_off_state == 1:
            self._state.set_screen_blanked()
        else:
            self._state.set_screen_unblanked()

        spi_lid_state = int(resp[5])
        if spi_lid_state == 1:
            self._state.set_lid_open()
        else:
            self._state.set_lid_closed()

        spi_brightness_int = int(resp[1:5], 2)
        screen_is_blanked = spi_screen_off_state == 1 and spi_brightness_int == 0
        if init or not screen_is_blanked:
            self._state.set_brightness(spi_brightness_int, False)

    def _transceive_spi(self, bits_to_send):
        hex_str_to_send = "0x" + str(hex(bits_to_send))[2:].zfill(2)
        bin_str_to_send = "{0:b}".format(int(hex_str_to_send[2:], 16)).zfill(8)

        log_brightness = str(int(bin_str_to_send[1:5], 2))
        log_screen = "On" if bin_str_to_send[6] == "0" else "Off"
        log_shutdown = "Shutting down" if bin_str_to_send[7] == "1" else "No shutdown"

        if bin_str_to_send == "11111111":
            logger.debug(
                "Pi sending:   " + bin_str_to_send + " [ fetch state from hub ]"
            )
        else:
            logger.debug(
                "Pi sending:   "
                + bin_str_to_send
                + " ["
                + log_brightness
                + ", "
                + log_screen
                + ", "
                + log_shutdown
                + "]"
            )

        # Transfer data with hub
        resp = self.spi.xfer2([bits_to_send], self.spi.max_speed_hz)

        resp_hex = hex(resp[0])
        resp_hex_str = "0x" + str(resp_hex)[2:].zfill(2)
        resp_bin_str = "{0:b}".format(int(resp_hex_str[2:], 16)).zfill(8)

        log_brightness = str(int(resp_bin_str[1:5], 2))
        log_lid = "Open" if resp_bin_str[5] == "1" else "Closed"
        log_screen = "On" if resp_bin_str[6] == "0" else "Off"
        log_shutdown = "Shutting down" if resp_bin_str[7] == "1" else "No shutdown"

        logger.debug(
            "Hub responds: "
            + resp_bin_str
            + " ["
            + log_brightness
            + ", "
            + log_lid
            + ", "
            + log_screen
            + ", "
            + log_shutdown
            + "]"
        )

        return resp_bin_str

    def _attempt_get_state(self, init=False):
        # Send 0xFF to get data from hub
        resp_bin_str = self._transceive_spi(255)

        valid = False

        if init and resp_bin_str == "00000000":
            # Invalid
            pass
        else:
            byte_type = self._determine_byte(resp_bin_str)

            if byte_type == SPIResponseType.state:
                logger.debug("Valid response from hub - STATE")
                valid = True
            else:
                if byte_type == SPIResponseType.device_id:
                    logger.debug("Valid response from hub - DEVICE ID")
                    # Process SPI resp, store brightness signal for check next loop
                    self._process_device_id(resp_bin_str)
                else:
                    logger.debug("Invalid response from hub")
                valid = False

        return valid, resp_bin_str

    def _get_state_from_hub(self, init=False, process_state=True):
        valid = False
        get_state_ctr = Counter(5)

        do_extra_read = init

        while not valid and not get_state_ctr.maxed():
            valid, resp_bin_str = self._attempt_get_state(init)

            if do_extra_read and valid:
                valid = False
                do_extra_read = False

            if not valid:
                get_state_ctr.current += 1
                sleep(_cycle_sleep_time)

        if valid:
            if process_state:
                self._process_spi_resp(resp_bin_str, init=init)
        else:
            logger.error(
                "Unable to communicate with hub. "
                + "init: "
                + str(init)
                + ", resp_bin_str: "
                + str(resp_bin_str)
            )

        return valid


def _represents_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def _append_to_queued_state_change_to_sends(state_change_to_send):
    _spi_handler.queued_changes.append(state_change_to_send)


def _add_state_change_to_send_to_stack(
    state_change_to_send_type, state_change_to_send_operation
):
    pending_state_change_to_send = StateChange(
        state_change_to_send_type, state_change_to_send_operation
    )
    _add_state_change_to_send_class_to_stack(pending_state_change_to_send)


def _add_state_change_to_send_class_to_stack(pending_state_change_to_send):
    valid_type = pending_state_change_to_send._type is not None
    valid_operation = pending_state_change_to_send._operation is not None
    if valid_type and valid_operation:
        _append_to_queued_state_change_to_sends(pending_state_change_to_send)
    else:
        logger.info("Unable to process state change - invalid type or operation")


def change_brightness_state(brightness_val):
    if is_initialised():

        if brightness_val > 10:
            brightness_val = 10

        if (
            brightness_val >= 0
            and brightness_val <= 10
            and _spi_handler._state.valid_brightness(brightness_val)
        ):
            if _spi_handler._state._screen_blanked == 1:
                change_screen_state(SPIScreenOperations.unblank)

            _add_state_change_to_send_to_stack(
                SPIStateChangeType.brightness, brightness_val
            )

            if not _main_thread.is_alive():
                communicate()
        else:
            logger.info(
                str(brightness_val) + " is not a valid brightness - doing nothing"
            )

    else:
        logger.error("Unable to change brightness - run initialise() first!")


def increment_brightness():
    current_brightness = _spi_handler._state._brightness
    new_brightness = current_brightness + 1
    change_brightness_state(new_brightness)


def decrement_brightness():
    current_brightness = _spi_handler._state._brightness
    new_brightness = current_brightness - 1
    change_brightness_state(new_brightness)


def set_brightness(brightness_val):
    change_brightness_state(brightness_val)


def change_screen_state(spi_screen_operation):
    if is_initialised():
        _add_state_change_to_send_to_stack(
            SPIStateChangeType.screen, spi_screen_operation
        )

        if not _main_thread.is_alive():
            communicate()
    else:
        logger.error("Unable to change screen state - run initialise() first!")


def blank_screen():
    change_screen_state(SPIScreenOperations.blank)


def unblank_screen():
    change_screen_state(SPIScreenOperations.unblank)


def start():
    global _main_thread
    global _run_main_thread

    if is_initialised():
        if _main_thread is None:
            _main_thread = threading.Thread(target=_main_thread_loop)

        _run_main_thread = True
        _main_thread.start()
    else:
        logger.error(
            "Unable to start pi-topHUB SPI communication - run initialise() first!"
        )


def stop():
    global _run_main_thread

    _run_main_thread = False
    _main_thread.join()


def is_initialised():
    return _spi_handler is not None


def initialise(state_instance):
    global _spi_handler

    try:
        _spi_handler = SPIHandler(state_instance)
        return True
    except Exception as e:
        logger.error("Error creating SPIHandler. " + str(e))
        logger.info(traceback.format_exc())
        _spi_handler = None
        return False


def communicate():
    if _spi_handler is None:
        logger.error("SPI has not been initialised - initialise first")
        return False

    try:
        return _spi_handler.transceive_and_process()
    except Exception as e:
        logger.error("Error transceiving SPI data from pi-topHUB. " + str(e))
        logger.info(traceback.format_exc())
        raise e
        return False


def _main_thread_loop():
    """///////////////////////////

    // MAIN CODE STARTS HERE // ///////////////////////////
    """
    while _run_main_thread:
        # Communicate regardless of any queued changes
        communicate()

        # Clean up queues state changes, if there are multiple
        while len(_spi_handler.queued_changes) > 0:
            communicate()
        sleep(_cycle_sleep_time)

    logger.info(
        "Hub v1 main loop exited. Sending "
        + str(len(_spi_handler.queued_changes))
        + " remaining queued changes..."
    )

    while len(_spi_handler.queued_changes) > 0:

        communicate()
        sleep(_cycle_sleep_time)


def set_speed(no_of_polls_per_second=4):
    global _cycle_sleep_time

    _cycle_sleep_time = float(1 / no_of_polls_per_second)
