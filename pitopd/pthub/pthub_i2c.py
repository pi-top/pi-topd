import traceback
from threading import Thread
from time import sleep

from pitop.common.counter import Counter
from pitop.common.logger import PTLogger
from smbus2 import SMBus

_battery_state_handler = None
_main_thread = None
_run_main_thread = False

# Time to pause between command sends
_cycle_sleep_time = 1


class BatteryRegisters:
    current = 0x0A
    voltage = 0x09
    capacity = 0x0D
    charge_time = 0x13
    discharge_time = 0x12


class BatteryDataType:
    charging_state = "charging_state"
    capacity = "capacity"
    time = "time"
    current = "current"
    voltage = "voltage"


class BatteryStateHandler:
    def __init__(self, state_instance):
        self._state = state_instance
        self._bus_no = 1
        self._chip_address = 0x0B

        self._i2c_ctr = Counter(20)

        self._connected = self._setup_i2c()

    def set_charging_state(self, charging_state):
        PTLogger.debug("Setting battery charging state as " + str(charging_state))
        self._state.set_battery_charging_state(charging_state)

    def set_capacity(self, capacity):
        PTLogger.debug("Setting battery capacity as " + str(capacity))
        self._state.set_battery_capacity(capacity)

    def set_time(self, time):
        PTLogger.debug("Setting battery time as " + str(time))
        self._state.set_battery_time(time)

    def set_current(self, current):
        PTLogger.debug("Setting battery current as " + str(current))
        self._current = current

    def set_voltage(self, voltage):
        PTLogger.debug("Setting battery voltage as " + str(voltage))
        self._voltage = voltage

    def set_wattage_from_current_and_voltage(self):
        current_amps = self._current / 1000
        voltage_volts = self._voltage / 1000
        wattage_deciwatts = max(0, int(round((current_amps * voltage_volts) * 10)))
        PTLogger.debug("Setting battery wattage as " + str(wattage_deciwatts) + "dW")
        self._state.set_battery_wattage(wattage_deciwatts)

    def is_connected(self):
        return self._connected

    def _setup_i2c(self):
        try:
            PTLogger.debug("Setting up i2c connection to battery")
            self._bus = SMBus(self._bus_no)

            PTLogger.debug("Testing comms with battery")
            return self._refresh_state()
        except Exception:
            PTLogger.warning("Unable to find pi-topHUB battery")

        return False

    def _refresh_state(self):
        PTLogger.debug("Refreshing battery state...")

        # Current goes first - used to determine which time to get
        PTLogger.debug("Getting battery current...")
        if not self._get_battery_data(BatteryDataType.current):
            PTLogger.warning("Unable to get battery current")
            return False

        PTLogger.debug("Getting battery capacity...")
        if not self._get_battery_data(BatteryDataType.capacity):
            PTLogger.warning("Unable to get battery capacity")
            return False

        PTLogger.debug("Getting battery voltage...")
        if not self._get_battery_data(BatteryDataType.voltage):
            PTLogger.warning("Unable to get battery voltage")
            return False

        PTLogger.debug("Getting battery time...")
        if not self._get_battery_data(BatteryDataType.time):
            PTLogger.warning("Unable to get battery time")
            # return False - Don't return False - non essential

        PTLogger.debug("Wattage set from battery voltage and current")
        self.set_wattage_from_current_and_voltage()

        return True

    def _get_battery_register_to_read(self, data_to_get):
        if data_to_get == BatteryDataType.charging_state:
            register = BatteryRegisters.current
        elif data_to_get == BatteryDataType.capacity:
            register = BatteryRegisters.capacity
        elif data_to_get == BatteryDataType.time:
            # requires charging state to be correct...
            if self._state._battery_charging_state == 0:
                register = BatteryRegisters.discharge_time
            else:
                register = BatteryRegisters.charge_time
        elif data_to_get == BatteryDataType.current:
            register = BatteryRegisters.current
        elif data_to_get == BatteryDataType.voltage:
            register = BatteryRegisters.voltage
        else:
            raise ValueError("Unknown data type to read from battery")

        return register

    def _parse_response(self, resp, register):
        # Successful read, check that value is valid
        if register == BatteryRegisters.current:
            return self._process_current_and_charging_state_i2c_resp(resp)
        elif register == BatteryRegisters.voltage:
            return self._process_voltage_i2c_resp(resp)
        elif register == BatteryRegisters.capacity:
            return self._process_capacity_i2c_resp(resp)
        elif register == BatteryRegisters.discharge_time:
            return self._process_discharging_time_i2c_resp(resp)
        elif register == BatteryRegisters.charge_time:
            return self._process_charging_time_i2c_resp(resp)
        else:
            # Unknown register
            return False

    def _process_capacity_i2c_resp(self, resp):
        if resp <= 100 and resp >= 0:
            self.set_capacity(resp)

            return True
        else:
            PTLogger.debug("Invalid, not less than or equal to 100")
            return False

    def _process_discharging_time_i2c_resp(self, resp):
        if resp <= 1800 and resp >= 0:
            self.set_time(resp)
            return True
        else:
            PTLogger.debug("Invalid, not less than or equal to 1800")

    def _process_charging_time_i2c_resp(self, resp):
        if resp <= 2400 and resp >= 0:
            self.set_time(resp)
            return True
        else:
            PTLogger.debug("Invalid, not less than or equal to 2400: " + str(resp))
            return False

    def _process_current_and_charging_state_i2c_resp(self, resp):
        if resp < -2500 or resp > 2500:
            PTLogger.debug("Invalid current: " + str(resp) + "mA")
            return False

        if resp <= -10:
            self.set_charging_state(0)
        else:
            charging_state = (
                2 if (self._state._battery_time == 0) else 1
            )  # charging state
            self.set_charging_state(charging_state)

        self.set_current(resp)

        return True

    def _process_voltage_i2c_resp(self, resp):
        if resp <= 20000 and resp >= 0:
            self.set_voltage(resp)
            return True
        else:
            PTLogger.debug("Invalid voltage: " + str(resp) + "mV")
            return False

    def twos_comp(self, val, bits=16):
        if (val & (1 << (bits - 1))) != 0:
            val = val - (1 << bits)
        return val

    def _attempt_read(self, data_to_get):
        successful_read = False
        resp = ""
        register = None
        try:
            register = self._get_battery_register_to_read(data_to_get)
            resp = self.twos_comp(
                self._bus.read_word_data(self._chip_address, register)
            )
            successful_read = True
        except Exception:
            pass

        return successful_read, resp, register

    def _get_battery_data(self, data_to_get):
        reattempt_sleep_s = float(_cycle_sleep_time / self._i2c_ctr.max)

        self._i2c_ctr.reset()
        while not self._i2c_ctr.maxed():
            self._i2c_ctr.increment()
            successful_read, resp, register = self._attempt_read(data_to_get)
            if successful_read:
                return self._parse_response(resp, register)
            else:
                PTLogger.debug("Unsuccessful read...")
            sleep(reattempt_sleep_s)

        # Value was not fetched
        PTLogger.debug("Unable to read from I2C after multiple attempts")
        return False


def start():
    global _main_thread
    global _run_main_thread

    if is_initialised():
        if _main_thread is None:
            _main_thread = Thread(target=_main_thread_loop)

        _run_main_thread = True
        _main_thread.start()
    else:
        PTLogger.error(
            "Unable to start pi-topHUB SPI communication - run initialise() first!"
        )


def stop():
    global _run_main_thread

    _run_main_thread = False
    _main_thread.join()


def is_initialised():
    return (_battery_state_handler is not None) and (
        _battery_state_handler.is_connected() is True
    )


def initialise(state):
    global _battery_state_handler

    try:
        _battery_state_handler = BatteryStateHandler(state)
        return True
    except Exception as e:
        PTLogger.error("Error initialising I2C. " + str(e))
        PTLogger.info(traceback.format_exc())
        _battery_state_handler = None
        return False


def communicate():
    if not is_initialised():
        PTLogger.error("I2C has not been initialised - call initialise() first")
        return False

    try:
        _battery_state_handler._refresh_state()
        return True
    except Exception as e:
        PTLogger.error("Error refreshing the state of the battery handler. " + str(e))
        PTLogger.info(traceback.format_exc())
        return False


def _main_thread_loop():
    """///////////////////////////

    // MAIN CODE STARTS HERE // ///////////////////////////
    """

    while _run_main_thread:
        communicate()
        sleep(_cycle_sleep_time)


def set_speed(no_of_polls_per_second=4):
    global _cycle_sleep_time

    _cycle_sleep_time = float(1 / no_of_polls_per_second)
