import logging
from threading import Thread
from time import sleep

from pitop.common.i2c_device import I2CDevice

logger = logging.getLogger(__name__)


class HubRegisters:
    PWR__SHUTDOWN_CTRL = 0xA0
    PWR__BUTT_SHORT_HOLD_TURNON = 0xA1
    PWR__BUTT_SHORT_HOLD_TURNOFF = 0xA2
    PWR__BUTT_LONG_HOLD = 0xA3
    PWR__M1_TIMEOUT_MIN = 0xAA
    PWR__M1_TIMEOUT_MAX = 0xAB
    PWR__M2_TIMEOUT_MIN = 0xAC
    PWR__M2_TIMEOUT_MAX = 0xAD
    PWR__M3_TIMEOUT = 0xAE
    BAT__TEMPERATURE = 0xB1
    BAT__VOLTAGE = 0xB2
    BAT__CURRENT = 0xB3
    BAT__RSOC = 0xB4
    BAT__TIME_TO_EMPTY = 0xB5
    BAT__TIME_TO_FULL = 0xB6
    AUD__CONFIG = 0xC0
    DIS__BACKLIGHT = 0xD1


class ShutdownRegister:

    # Bits
    PWR__SHUTDOWN_CTRL__HELD = 0x1
    PWR__SHUTDOWN_CTRL__BUTT = 0x2
    PWR__SHUTDOWN_CTRL__MODE_B1 = 0x8
    PWR__SHUTDOWN_CTRL__MODE_B2 = 0x10
    PWR__SHUTDOWN_CTRL__CANCEL = 0x80


class BacklightRegister:

    # Bits
    DIS__BACKLIGHT__PERC_B1 = 0x01
    DIS__BACKLIGHT__PERC_B2 = 0x02
    DIS__BACKLIGHT__PERC_B3 = 0x04
    DIS__BACKLIGHT__PERC_B4 = 0x08
    DIS__BACKLIGHT__PERC_B5 = 0x10
    DIS__BACKLIGHT__UNUSED_B1 = 0x20
    DIS__BACKLIGHT__LIDSW = 0x40
    DIS__BACKLIGHT__EN = 0x80

    # Combinations
    DIS__BACKLIGHT__PERC_ALL = (
        DIS__BACKLIGHT__PERC_B1
        | DIS__BACKLIGHT__PERC_B2
        | DIS__BACKLIGHT__PERC_B3
        | DIS__BACKLIGHT__PERC_B4
        | DIS__BACKLIGHT__PERC_B5
    )


class AudioRegister:

    # Bits
    AUD__CONFIG__HDMI = 0x01
    AUD__CONFIG__HPDET = 0x02


class HubConnection:

    POWER_OFF_TIMEOUT_SECONDS = 10

    def initialise(self, state):
        self._cycle_sleep_time = 0.25
        self._state = state
        self._main_thread = Thread(target=self._main_thread_loop)

        try:
            self._i2c_device = I2CDevice("/dev/i2c-1", 0x10)
            self._i2c_device.connect()
        except Exception as e:
            logger.warning("Unable to read from hub (v2) over i2c: " + str(e))
            return False

        return True

    def start(self):
        if self._main_thread is not None:
            self._run_polling_thread = True
            self._poll_hub()
            self._main_thread.start()
        else:
            logger.error(
                "Unable to start pi-topHUB SPI communication - run initialise() first!"
            )

    def stop(self):
        self._run_polling_thread = False
        self._main_thread.join()
        self._i2c_device.disconnect()

    def set_speed(self, no_of_polls_per_second=4):
        self._cycle_sleep_time = float(1 / no_of_polls_per_second)

    def increment_brightness(self):

        try:
            logger.debug("Hub: increment_brightness")
            backlight_settings = self._i2c_device.read_unsigned_byte(
                HubRegisters.DIS__BACKLIGHT
            )

            # get just the brightness part of the byte
            current_brightness_value = (
                backlight_settings & BacklightRegister.DIS__BACKLIGHT__PERC_ALL
            )

            if current_brightness_value < 16:
                self.set_brightness(current_brightness_value + 1)

        except Exception as e:
            logger.error("Error incrementing brightness: " + str(e))

    def decrement_brightness(self):

        try:
            logger.debug("Hub: decrement_brightness")
            backlight_settings = self._i2c_device.read_unsigned_byte(
                HubRegisters.DIS__BACKLIGHT
            )

            # get just the brightness part of the byte
            current_brightness_value = (
                backlight_settings & BacklightRegister.DIS__BACKLIGHT__PERC_ALL
            )

            if current_brightness_value > 0:
                self.set_brightness(current_brightness_value - 1)

        except Exception as e:
            logger.error("Error decrementing brightness: " + str(e))

    def set_brightness(self, value):

        try:
            logger.debug("Hub: set_brightness")

            if value < 0 or value > 16:
                logger.warning("Invalid brightness value provided: " + str(value))
                return

            backlight_settings = self._i2c_device.read_unsigned_byte(
                HubRegisters.DIS__BACKLIGHT
            )

            # clear the brightness part of the byte
            backlight_settings = backlight_settings & (
                ~BacklightRegister.DIS__BACKLIGHT__PERC_ALL & 0xFF
            )

            # Set the new brightness value into those bits
            backlight_settings = backlight_settings | value

            self._i2c_device.write_byte(HubRegisters.DIS__BACKLIGHT, backlight_settings)

        except Exception as e:
            logger.error("Error setting brightness: " + str(e))

    def blank_screen(self):

        try:
            logger.debug("Hub: blank_screen")
            backlight_settings = self._i2c_device.read_unsigned_byte(
                HubRegisters.DIS__BACKLIGHT
            )
            self._i2c_device.write_byte(
                HubRegisters.DIS__BACKLIGHT,
                backlight_settings & (~BacklightRegister.DIS__BACKLIGHT__EN & 0xFF),
            )

        except Exception as e:
            logger.error("Error blanking screen: " + str(e))

    def unblank_screen(self):

        try:
            logger.debug("Hub: unblank_screen")
            backlight_settings = self._i2c_device.read_unsigned_byte(
                HubRegisters.DIS__BACKLIGHT
            )
            self._i2c_device.write_byte(
                HubRegisters.DIS__BACKLIGHT,
                backlight_settings | BacklightRegister.DIS__BACKLIGHT__EN,
            )

        except Exception as e:
            logger.error("Error unblanking screen: " + str(e))

    def shutdown(self):

        # IMPORTANT: The default way in which the hub shuts down is as follows:
        # (1) The OS is shut down
        # (2) During shutdown a systemd service fires off shutdown command to hub
        # (3) Hub enters shutdown mode, waits for end of hdmi video signal from
        #     the pi
        # (4) Hub cuts power

        # However, we do need to stop polling the hub, otherwise we'll keep detecting
        # shutdown and triggering the shutdown process.

        logger.debug("Hub: shutdown")
        self._run_polling_thread = False

    def enable_hdmi_audio(self):

        try:
            logger.debug("Hub: enable_hdmi_audio")
            audio_settings = self._i2c_device.read_unsigned_byte(
                HubRegisters.AUD__CONFIG
            )
            self._i2c_device.write_byte(
                HubRegisters.AUD__CONFIG,
                audio_settings | AudioRegister.AUD__CONFIG__HDMI,
            )

        except Exception as e:
            logger.error("Error enabling hdmi audio (multiplexer): " + str(e))

    def disable_hdmi_audio(self):

        try:
            logger.debug("Hub: disable_hdmi_audio")
            audio_settings = self._i2c_device.read_unsigned_byte(
                HubRegisters.AUD__CONFIG
            )
            self._i2c_device.write_byte(
                HubRegisters.AUD__CONFIG,
                audio_settings & (~AudioRegister.AUD__CONFIG__HDMI & 0xFF),
            )

        except Exception as e:
            logger.error("Error disabling hdmi audio (multiplexer): " + str(e))

    ########################
    # Internal methods
    ########################

    def _main_thread_loop(self):

        while self._run_polling_thread is True:

            self._poll_hub()
            sleep(self._cycle_sleep_time)

    def _poll_hub(self):

        try:
            logger.debug("Polling for shutdown...")
            self._read_shutdown_control()

            logger.debug("Polling for battery...")
            self._read_battery_registers()

            logger.debug("Polling for backlight...")
            self._read_backlight_register()

        except TypeError:
            raise

        except Exception as e:
            logger.error("Error polling hub: " + str(e))

    def _read_shutdown_control(self):

        shutdown_control = self._i2c_device.read_unsigned_byte(
            HubRegisters.PWR__SHUTDOWN_CTRL
        )

        if shutdown_control & ShutdownRegister.PWR__SHUTDOWN_CTRL__BUTT != 0:

            # The power button been held for the time indicated in PWR__BUTT_SHORT_HOLD_TURNOFF
            self._state.emit_shutdown()

    def _read_battery_registers(self):

        # Get values from the hub

        current_ma = self._i2c_device.read_signed_word(HubRegisters.BAT__CURRENT)
        voltage_v = self._i2c_device.read_signed_word(HubRegisters.BAT__VOLTAGE)
        relative_state_of_charge = self._i2c_device.read_unsigned_byte(
            HubRegisters.BAT__RSOC
        )
        time_until_empty_mins = self._i2c_device.read_unsigned_word(
            HubRegisters.BAT__TIME_TO_EMPTY
        )
        time_until_full_mins = self._i2c_device.read_unsigned_word(
            HubRegisters.BAT__TIME_TO_FULL
        )

        # If the times are set to 0xFFFF, that means infinite (e.g. not charging or
        # discharging), so we set these to 0 to make them more sensible for clients

        if time_until_empty_mins == 0xFFFF:
            time_until_empty_mins = 0

        if time_until_full_mins == 0xFFFF:
            time_until_full_mins = 0

        # Set the charging state base on the current

        power_cable_connected = current_ma >= 0
        if power_cable_connected:
            if time_until_full_mins == 0:
                charging_state = 2  # full battery
            else:
                charging_state = 1  # charging
        else:
            charging_state = 0  # discharging

        self._state.set_battery_charging_state(charging_state)
        if charging_state == 2:
            self._state.set_battery_capacity(100)
        else:
            self._state.set_battery_capacity(relative_state_of_charge)

        # Choose between the time until full/empty based on the current also

        if current_ma > 0:
            self._state.set_battery_time(time_until_full_mins)
        else:
            self._state.set_battery_time(time_until_empty_mins)

        # Set the wattage in tenths of a watt

        self._state.set_battery_wattage(int(current_ma * voltage_v * 0.00001))

    def _read_backlight_register(self):

        backlight_settings = self._i2c_device.read_unsigned_byte(
            HubRegisters.DIS__BACKLIGHT
        )

        # Brightness
        current_brightness_value = (
            backlight_settings & BacklightRegister.DIS__BACKLIGHT__PERC_ALL
        )

        if current_brightness_value < 0:
            logger.warning(
                "Invalid brightness value returned from hub: "
                + str(current_brightness_value)
            )
            current_brightness_value = 0

        if current_brightness_value > 16:
            logger.warning(
                "Invalid brightness value returned from hub: "
                + str(current_brightness_value)
            )
            current_brightness_value = 16

        self._state.set_brightness(current_brightness_value)

        # Screen blanking
        screen_blanked = (
            backlight_settings & BacklightRegister.DIS__BACKLIGHT__EN
        ) == 0
        if screen_blanked is True:
            self._state.set_screen_blanked()
        else:
            self._state.set_screen_unblanked()

        # Lid state

        lid_closed = (backlight_settings & BacklightRegister.DIS__BACKLIGHT__LIDSW) == 0

        if lid_closed is True:
            self._state.set_lid_closed()
        else:
            self._state.set_lid_open()
