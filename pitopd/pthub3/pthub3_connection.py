import logging
from threading import Thread
from time import sleep

from pitop.common import bitwise_ops
from pitop.common.i2c_device import I2CDevice
from pitopd.event import AppEvents, subscribe


from .internal.apcad import APCAD
from .internal.battery import BatteryControl
from .internal.device_info import DeviceInfo
from .internal.diagnostics import Diagnostics
from .internal.display import BacklightRegister, Display
from .internal.hardware import (
    BatteryDisplayI2CBusControl,
    FanSpeedControl,
    HardwareControl,
    OLEDControlRegister,
    RasPiBoardDetect,
    UIButtonsRegister,
)
from .internal.misc import AudioConfig, AudioRegister, UnixTime
from .internal.power import PowerControl, ShutdownRegister

logger = logging.getLogger(__name__)


class HubConnection:
    POWER_OFF_TIMEOUT_SECONDS = 10

    def __init__(self):
        self._run_polling_thread = False
        self._cycle_sleep_time = 0.1
        self._accelerated_cycle_sleep_time = 0.02
        self._accelerated_cycle_sleep_time_counter = 0
        self._accelerated_cycle_sleep_time_counter_limit = 150
        self.button_pressed_recently = False
        self._main_thread = Thread(target=self._main_thread_loop)
        self._state = None
        self._i2c_device = None
        self._battery_sleep_counter = 0
        self._battery_min_read_sleep_s = 2
        self._display_sleep_counter = 0
        self._display_min_read_sleep_s = 2
        self._cpu_temp_sleep_counter = 0
        self._cpu_temp_min_read_sleep_s = 5

    def initialise(self, state):
        self._state = state

        try:
            self._i2c_device = I2CDevice("/dev/i2c-1", 0x11)
            self._i2c_device.set_delays(0.001, 0.001)
            self._i2c_device.connect()
            if not self.check_for_part_name_id():
                return False
        except Exception as e:
            logger.warning("Unable to read from hub (v3) over i2c: " + str(e))
            return False

        subscribe(AppEvents.SPI_BUS_CHANGED, self.set_oled_use_spi0)
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

    def set_speed(self, no_of_polls_per_second=10):
        self._cycle_sleep_time = float(1 / no_of_polls_per_second)

    def read_raspi_board_detect_flag(self):
        logger.debug("Hub: Reading raspi board detect flag")
        return self._i2c_device.read_bits_from_byte_at_address(
            bits_to_read=RasPiBoardDetect.CTRL__BRD_DETECT__DETECT,
            addr_to_read=HardwareControl.CTRL__BRD_DETECT,
        )

    def read_raspi_board_prevent_boot(self):
        logger.debug("Hub: Reading raspi board prevent boot")
        return self._i2c_device.read_bits_from_byte_at_address(
            bits_to_read=RasPiBoardDetect.CTRL__BRD_DETECT__PREVENT,
            addr_to_read=HardwareControl.CTRL__BRD_DETECT,
        )

    def set_raspi_board_prevent_boot(self, prevent_boot):
        logger.debug("Hub: setting raspi board prevent boot")
        full_byte = self._i2c_device.read_unsigned_byte(
            HardwareControl.CTRL__BRD_DETECT
        )

        if prevent_boot:
            full_byte = bitwise_ops.set_bits_high(
                RasPiBoardDetect.CTRL__BRD_DETECT__PREVENT, full_byte
            )
        else:
            full_byte = bitwise_ops.set_bits_low(
                RasPiBoardDetect.CTRL__BRD_DETECT__PREVENT, full_byte
            )

        self._i2c_device.write_byte(HardwareControl.CTRL__BRD_DETECT, full_byte)

    def read_modular_connector_device_detection(self):
        logger.debug("Hub: Reading Modular Connector Device Detection")
        return self._i2c_device.read_unsigned_byte(HardwareControl.CTRL__MODULE_DETECT)

    def read_battery_display_i2c_control(self):
        logger.debug("Hub: Reading battery_display_i2c_control")
        return self._i2c_device.read_bits_from_byte_at_address(
            bits_to_read=BatteryDisplayI2CBusControl.CTRL__BATT_AND_DISP_I2C_MUX__CONTROL,
            addr_to_read=HardwareControl.CTRL__BATT_AND_DISP_I2C_MUX,
        )

    def set_battery_display_i2c_control(self, controlled_by_pi):
        logger.debug("Hub: Writing battery_display_i2c_control")
        state_bit = 0x1 if controlled_by_pi else 0x00
        self._i2c_device.write_byte(
            HardwareControl.CTRL__BATT_AND_DISP_I2C_MUX, state_bit
        )

    def read_oled_control(self):
        logger.debug("Hub: Reading oled_control")
        return self._i2c_device.read_bits_from_byte_at_address(
            bits_to_read=OLEDControlRegister.CTRL__UI_OLED_CTRL__RPI_CONTROL,
            addr_to_read=HardwareControl.CTRL__UI_OLED_CTRL,
        )

    def set_oled_control(self, controlled_by_pi):
        logger.debug("Hub: Writing oled_control")
        full_byte = self._i2c_device.read_unsigned_byte(
            HardwareControl.CTRL__UI_OLED_CTRL
        )

        if controlled_by_pi:
            full_byte = bitwise_ops.set_bits_high(
                OLEDControlRegister.CTRL__UI_OLED_CTRL__RPI_CONTROL, full_byte
            )
        else:
            full_byte = bitwise_ops.set_bits_low(
                OLEDControlRegister.CTRL__UI_OLED_CTRL__RPI_CONTROL, full_byte
            )

        self._i2c_device.write_byte(HardwareControl.CTRL__UI_OLED_CTRL, full_byte)
        self.reset_oled()

    def reset_oled(self):
        full_byte = self._i2c_device.read_unsigned_byte(
            HardwareControl.CTRL__UI_OLED_CTRL
        )
        full_byte = bitwise_ops.set_bits_high(
            OLEDControlRegister.CTRL__UI_OLED_CTRL__RST, full_byte
        )
        self._i2c_device.write_byte(HardwareControl.CTRL__UI_OLED_CTRL, full_byte)
        for count in range(5):
            logger.debug("Hub: reading for OLED reset count: " + str(count))
            sleep(0.002)
            reset_bit_value = (
                self._i2c_device.read_unsigned_byte(HardwareControl.CTRL__UI_OLED_CTRL)
                & OLEDControlRegister.CTRL__UI_OLED_CTRL__RST
            )
            if reset_bit_value == 0:
                logger.debug("Hub: OLED has reset (count: %s)" % str(count))
                return
        logger.warning("Hub: Failed to read OLED reset completed in time.")

    def read_oled_use_spi0(self):
        logger.debug("Hub: Reading oled_use_spi0")
        return self._i2c_device.read_bits_from_byte_at_address(
            bits_to_read=OLEDControlRegister.CTRL__UI_OLED_CTRL__SPI_ALT,
            addr_to_read=HardwareControl.CTRL__UI_OLED_CTRL,
        )

    def set_oled_use_spi0(self, use_spi0):
        logger.debug("Hub: Writing oled_use_spi0")
        full_byte = self._i2c_device.read_unsigned_byte(
            HardwareControl.CTRL__UI_OLED_CTRL
        )

        if use_spi0:
            full_byte = bitwise_ops.set_bits_high(
                OLEDControlRegister.CTRL__UI_OLED_CTRL__SPI_ALT, full_byte
            )
        else:
            full_byte = bitwise_ops.set_bits_low(
                OLEDControlRegister.CTRL__UI_OLED_CTRL__SPI_ALT, full_byte
            )

        self._i2c_device.write_byte(HardwareControl.CTRL__UI_OLED_CTRL, full_byte)
        self.reset_oled()

    def set_fan_manual_speed(self, fan_speed):
        logger.debug("Hub: Writing fan speed")
        if not 0 <= fan_speed <= 9:
            logger.warning(
                "Invalid fan speed " + str(fan_speed) + ". Fan speed range is [0-9]"
            )
            return
        fan_speed_control_byte = self._i2c_device.read_unsigned_byte(
            HardwareControl.CTRL__FAN_SPEED
        )
        fan_speed_set_byte = bitwise_ops.set_bits_high(
            fan_speed,
            bitwise_ops.get_bits(
                ~FanSpeedControl.CTRL__FAN_SPEED__SPEED, fan_speed_control_byte
            ),
        )

        self._i2c_device.write_byte(HardwareControl.CTRL__FAN_SPEED, fan_speed_set_byte)

    def read_fan_speed(self):
        logger.debug("Hub: Reading fan speed")
        return (
            self._i2c_device.read_unsigned_byte(HardwareControl.CTRL__FAN_SPEED)
            & FanSpeedControl.CTRL__FAN_SPEED__SPEED
        )

    def set_fan_mode_auto(self, auto):
        logger.debug("Hub: Writing fan control mode")
        fan_mode = 0 if auto else 1
        fan_speed_control_byte = self._i2c_device.read_unsigned_byte(
            HardwareControl.CTRL__FAN_SPEED
        )
        fan_mode_set_byte = bitwise_ops.set_bits_high(
            (fan_mode << 7),
            bitwise_ops.get_bits(
                FanSpeedControl.CTRL__FAN_SPEED__SPEED, fan_speed_control_byte
            ),
        )

        self._i2c_device.write_byte(HardwareControl.CTRL__FAN_SPEED, fan_mode_set_byte)

    def read_fan_mode_auto(self):
        logger.debug("Hub: Reading fan mode")
        return self._i2c_device.read_unsigned_byte(HardwareControl.CTRL__FAN_SPEED) >> 7

    def read_mcu_rpi_cpu_temp(self):
        logger.debug("Hub: Reading RPi CPU temperature")
        return self._i2c_device.read_unsigned_byte(HardwareControl.CTRL__RASPI_CPU_TEMP)

    def set_rpi_cpu_temp(self, cpu_temp):
        logger.debug("Hub: Writing RPi CPU temperature")
        self._i2c_device.write_byte(HardwareControl.CTRL__RASPI_CPU_TEMP, cpu_temp)

    def read_uptime_standby_time(self):
        logger.debug("Hub: Reading standby time of uptime")
        return self._i2c_device.read_n_unsigned_bytes(Diagnostics.DIAG__UPTIME_STDBY, 4)

    def read_uptime_rails_on_time(self):
        logger.debug("Hub: Reading rails on time of uptime")
        return self._i2c_device.read_n_unsigned_bytes(
            Diagnostics.DIAG__UPTIME_RAILSON, 4
        )

    def read_lifetime_standby_time(self):
        logger.debug("Hub: Reading standby time of lifetime")
        return self._i2c_device.read_n_unsigned_bytes(Diagnostics.DIAG__UPTIME_STDBY, 4)

    def read_lifetime_rails_on_time(self):
        logger.debug("Hub: Reading rails on time of lifetime")
        return self._i2c_device.read_n_unsigned_bytes(
            Diagnostics.DIAG__LIFETIME_RAILSON, 4
        )

    def read_lifetime_number_of_power_cycles(self):
        logger.debug("Hub: Reading number of power cycles of lifetime")
        return self._i2c_device.read_unsigned_word(Diagnostics.DIAG__UPTIME_STDBY)

    def read_shutdown_button_held(self):
        logger.debug("Hub: Reading shutdown button held")
        return self._i2c_device.read_bits_from_byte_at_address(
            bits_to_read=ShutdownRegister.PWR__SHUTDOWN_CTRL__HELD,
            addr_to_read=PowerControl.PWR__SHUTDOWN_CTRL,
        )

    def _read_shutdown_control(self):
        logger.debug("Polling for shutdown...")
        shutdown_control = bitwise_ops.get_bits(
            ShutdownRegister.PWR__SHUTDOWN_CTRL__BUTT,
            self._i2c_device.read_unsigned_byte(PowerControl.PWR__SHUTDOWN_CTRL),
        )
        if shutdown_control != 0:
            # The power button been held for the time indicated in PWR__BUTT_SHORT_HOLD_TURNOFF
            self._state.emit_shutdown()

    def read_shutdown_mode(self):
        logger.debug("Hub: Reading shutdown mode")
        full_byte = self._i2c_device.read_unsigned_byte(PowerControl.PWR__SHUTDOWN_CTRL)
        # TODO: REVIEW BITSHIFT HERE - WHY IS THIS NEEDED?
        return (
            bitwise_ops.get_bits(ShutdownRegister.PWR__SHUTDOWN_CTRL__MODE, full_byte)
            >> 3
        )

    def set_shutdown_mode(self, mode: int):
        logger.debug("Hub: Writing shutdown mode")
        full_byte = bitwise_ops.set_bits_low(
            ShutdownRegister.PWR__SHUTDOWN_CTRL__MODE,
            self._i2c_device.read_unsigned_byte(PowerControl.PWR__SHUTDOWN_CTRL),
        )
        set_value = bitwise_ops.set_bits_high((mode << 3), full_byte)
        self._i2c_device.write_byte(PowerControl.PWR__SHUTDOWN_CTRL, set_value)

    def read_ac_power_connected(self):
        logger.debug("Hub: Reading detect ac power")
        return self._i2c_device.read_bits_from_byte_at_address(
            bits_to_read=ShutdownRegister.PWR__SHUTDOWN_CTRL__AC,
            addr_to_read=PowerControl.PWR__SHUTDOWN_CTRL,
        )

    def set_shutdown_cancel(self, cancel):
        logger.debug("Hub: Writing cancel shutdown")
        if cancel is True:
            shutdown_state = self._i2c_device.read_unsigned_byte(
                PowerControl.PWR__SHUTDOWN_CTRL
            )
            cancel_shutdown = bitwise_ops.set_bits_high(
                ShutdownRegister.PWR__SHUTDOWN_CTRL__CANCEL, shutdown_state
            )
            self._i2c_device.write_byte(
                PowerControl.PWR__SHUTDOWN_CTRL, cancel_shutdown
            )

    def read_shutdown_short_button_hold_turn_on(self):
        logger.debug("Hub: Reading shutdown short hold button turn on duration")
        return self._i2c_device.read_unsigned_byte(
            PowerControl.PWR__BUTT_SHORT_HOLD_TURNON
        )

    def set_shutdown_short_button_hold_turn_on(self, time):
        logger.debug("Hub: Writing shutdown short hold button turn on duration")
        self._i2c_device.write_byte(PowerControl.PWR__BUTT_SHORT_HOLD_TURNON, time)

    def read_shutdown_short_button_hold_turn_off(self):
        logger.debug("Hub: Reading shutdown short hold button turn off duration")
        return self._i2c_device.read_unsigned_byte(
            PowerControl.PWR__BUTT_SHORT_HOLD_TURNOFF
        )

    def set_shutdown_short_button_hold_turn_off(self, time):
        logger.debug("Hub: Writing shutdown short hold button turn off duration")
        self._i2c_device.write_byte(PowerControl.PWR__BUTT_SHORT_HOLD_TURNOFF, time)

    def read_shutdown_long_button_hold_turn_off(self):
        logger.debug("Hub: Reading shutdown long hold button turn off duration")
        return self._i2c_device.read_unsigned_byte(PowerControl.PWR__BUTT_LONG_HOLD)

    def set_shutdown_long_button_hold_turn_off(self, time):
        logger.debug("Hub: Writing shutdown long hold button turn off duration")
        self._i2c_device.write_byte(PowerControl.PWR__BUTT_LONG_HOLD, time)

    def read_shutdown_mode1_timeout_min(self):
        logger.debug("Hub: Reading shutdown mode 1 timeout min")
        return self._i2c_device.read_unsigned_word(PowerControl.PWR__M1_TIMEOUT_MIN)

    def set_shutdown_mode1_timeout_min(self, time):
        logger.debug("Hub: Writing shutdown mode 1 timeout min")
        self._i2c_device.write_word(PowerControl.PWR__M1_TIMEOUT_MIN, time)

    def read_shutdown_mode2_timeout_min(self):
        logger.debug("Hub: Reading shutdown mode 2 timeout min")
        return self._i2c_device.read_unsigned_word(PowerControl.PWR__M2_TIMEOUT_MIN)

    def set_shutdown_mode2_timeout_min(self, time):
        logger.debug("Hub: Writing shutdown mode 2 timeout min")
        self._i2c_device.write_word(PowerControl.PWR__M2_TIMEOUT_MIN, time)

    def read_shutdown_mode1_timeout_max(self):
        logger.debug("Hub: Reading shutdown mode 1 timeout max")
        return self._i2c_device.read_unsigned_word(PowerControl.PWR__M1_TIMEOUT_MAX)

    def set_shutdown_mode1_timeout_max(self, time):
        logger.debug("Hub: Writing shutdown mode 1 timeout max")
        self._i2c_device.write_word(PowerControl.PWR__M1_TIMEOUT_Max, time)

    def read_shutdown_mode2_timeout_max(self):
        logger.debug("Hub: Reading shutdown mode 2 timeout max")
        return self._i2c_device.read_unsigned_word(PowerControl.PWR__M2_TIMEOUT_MAX)

    def set_shutdown_mode2_timeout_max(self, time):
        logger.debug("Hub: Writing shutdown mode 2 timeout max")
        self._i2c_device.write_word(PowerControl.PWR__M2_TIMEOUT_MAX, time)

    def read_shutdown_mode3_timeout(self):
        logger.debug("Hub: Reading shutdown mode 3 timeout")
        return self._i2c_device.read_unsigned_word(PowerControl.PWR__M3_TIMEOUT)

    def set_shutdown_mode3_timeout(self, time):
        logger.debug("Hub: Writing shutdown mode 3 timeout")
        self._i2c_device.write_word(PowerControl.PWR__M3_TIMEOUT, time)

    def read_screen_test_mode(self):
        return self._i2c_device.read_unsigned_byte(Display.DIS__TEST_MODE)

    def set_screen_test_mode(self, test_mode):
        self._i2c_device.write_byte(Display.DIS__TEST_MODE, test_mode)

    def read_battery_storage_mode(self):
        logger.debug("Hub: Reading battery storage mode")
        return self._i2c_device.read_unsigned_byte(BatteryControl.BAT__STORAGE_MODE)

    def set_battery_storage_mode(self, set_storage_mode):
        logger.debug("Hub: Writing battery storage mode")
        state_bit = int(set_storage_mode)
        self._i2c_device.write_byte(BatteryControl.BAT__STORAGE_MODE, state_bit)

    def read_battery_temperature(self):
        logger.debug("Hub: Reading battery temperature")
        return self._i2c_device.read_unsigned_word(BatteryControl.BAT__TEMPERATURE)

    def read_battery_cell1_voltage(self):
        logger.debug("Hub: Reading battery cell 1 voltage")
        return self._i2c_device.read_unsigned_word(BatteryControl.BAT__VOLT_CELL1)

    def read_battery_cell2_voltage(self):
        logger.debug("Hub: Reading battery cell 2 voltage")
        return self._i2c_device.read_unsigned_word(BatteryControl.BAT__VOLT_CELL2)

    def read_battery_cell3_voltage(self):
        logger.debug("Hub: Reading battery cell 3 voltage")
        return self._i2c_device.read_unsigned_word(BatteryControl.BAT__VOLT_CELL3)

    def read_battery_cell4_voltage(self):
        logger.debug("Hub: Reading battery cell 4 voltage")
        return self._i2c_device.read_unsigned_word(BatteryControl.BAT__VOLT_CELL4)

    def read_battery_error_flag(self):
        logger.debug("Hub: Reading battery error flag")
        return self._i2c_device.read_bits_from_byte_at_address(
            bits_to_read=0x1, addr_to_read=BatteryControl.BAT__PF_ERROR
        )

    def read_battery_serial_number(self):
        logger.debug("Hub: Reading battery serial number")
        return self._i2c_device.read_unsigned_word(BatteryControl.BAT__SERIAL_NUM)

    def read_battery_manufacture_date(self):
        logger.debug("Hub: Reading battery manufacture date")
        return self._i2c_device.read_unsigned_word(BatteryControl.BAT__MANUF_DATE)

    def read_battery_charging_error_detect(self):
        logger.debug("Hub: Reading battery charging error")
        return self._i2c_device.read_unsigned_byte(BatteryControl.BAT__CHARGING_ERROR)

    def read_mcu_software_version_major(self):
        logger.debug("Hub: Reading mcu software version major")
        return self._i2c_device.read_unsigned_byte(DeviceInfo.ID__MCU_SOFT_VERS_MAJOR)

    def read_mcu_software_version_minor(self):
        logger.debug("Hub: Reading mcu software version minor")
        return self._i2c_device.read_unsigned_byte(DeviceInfo.ID__MCU_SOFT_VERS_MINOR)

    def read_sch_hardware_version_major(self):
        logger.debug("Hub: Reading sch hardware version major")
        return self._i2c_device.read_unsigned_byte(DeviceInfo.ID__SCH_REV_MAJOR)

    def read_sch_hardware_version_minor(self):
        logger.debug("Hub: Reading sch hardware version minor")
        return self._i2c_device.read_unsigned_byte(DeviceInfo.ID__SCH_REV_MINOR)

    def read_brd_version(self):
        logger.debug("Hub: Reading brd version")
        return self._i2c_device.read_unsigned_byte(DeviceInfo.ID__BRD_REV)

    def check_for_part_name_id(self):
        return self.read_part_name() != 0

    def read_part_name(self):
        logger.debug("Hub: Reading part name")
        return self._i2c_device.read_unsigned_word(DeviceInfo.ID__PART_NAME)

    def read_part_number(self):
        logger.debug("Hub: Reading part number")
        return self._i2c_device.read_unsigned_word(DeviceInfo.ID__PART_NUMBER)

    def read_serial_id(self):
        logger.debug("Hub: Reading serial id")
        return self._i2c_device.read_n_unsigned_bytes(DeviceInfo.ID__SERIAL_ID, 4)

    def read_display_mcu_software_version_major(self):
        logger.debug("Hub: Reading display mcu software version major")
        return self._i2c_device.read_unsigned_byte(
            DeviceInfo.ID__DISPLAY_MCU_SOFT_VERS_MAJOR
        )

    def read_display_mcu_software_version_minor(self):
        logger.debug("Hub: Reading display mcu software version minor")
        return self._i2c_device.read_unsigned_byte(
            DeviceInfo.ID__DISPLAY_MCU_SOFT_VERS_MINOR
        )

    def read_display_sch_hardware_version_major(self):
        logger.debug("Hub: Reading display sch hardware version major")
        return self._i2c_device.read_unsigned_byte(DeviceInfo.ID__DISPLAY_SCH_REV_MAJOR)

    def read_display_sch_hardware_version_minor(self):
        logger.debug("Hub: Reading display sch hardware version minor")
        return self._i2c_device.read_unsigned_byte(DeviceInfo.ID__DISPLAY_SCH_REV_MINOR)

    def read_display_brd_version(self):
        logger.debug("Hub: Reading display brd version")
        return self._i2c_device.read_unsigned_byte(DeviceInfo.ID__DISPLAY_BRD_REV)

    def read_display_part_name(self):
        logger.debug("Hub: Reading display part name")
        return self._i2c_device.read_unsigned_word(DeviceInfo.ID__DISPLAY_PART_NAME)

    def read_display_part_nmuber(self):
        logger.debug("Hub: Reading display part number")
        return self._i2c_device.read_unsigned_word(DeviceInfo.ID__DISPLAY_PART_NUMBER)

    def read_display_serial_id(self):
        logger.debug("Hub: Reading display serial id")
        return self._i2c_device.read_n_unsigned_bytes(
            DeviceInfo.ID__DISPLAY_SERIAL_ID, 4
        )

    def increment_brightness(self):
        try:
            logger.debug("Hub: increment_brightness")
            current_brightness_value = self._i2c_device.read_bits_from_byte_at_address(
                bits_to_read=BacklightRegister.DIS__BACKLIGHT__PERC_ALL,
                addr_to_read=Display.DIS__BACKLIGHT,
            )

            if current_brightness_value < 16:
                self.set_brightness(current_brightness_value + 1)
        except Exception as e:
            logger.error("Error incrementing brightness: " + str(e))

    def decrement_brightness(self):
        try:
            logger.debug("Hub: decrement_brightness")
            current_brightness_value = self._i2c_device.read_bits_from_byte_at_address(
                bits_to_read=BacklightRegister.DIS__BACKLIGHT__PERC_ALL,
                addr_to_read=Display.DIS__BACKLIGHT,
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

            updated_backlight_settings = bitwise_ops.set_bits_high(
                value,
                bitwise_ops.set_bits_low(
                    BacklightRegister.DIS__BACKLIGHT__PERC_ALL,
                    self._i2c_device.read_unsigned_byte(Display.DIS__BACKLIGHT),
                ),
            )

            self._i2c_device.write_byte(
                Display.DIS__BACKLIGHT, updated_backlight_settings
            )
        except Exception as e:
            logger.error("Error setting brightness: " + str(e))

    def blank_screen(self):
        try:
            logger.debug("Hub: blank_screen")
            updated_backlight_settings = bitwise_ops.set_bits_low(
                BacklightRegister.DIS__BACKLIGHT__EN,
                self._i2c_device.read_unsigned_byte(Display.DIS__BACKLIGHT),
            )
            self._i2c_device.write_byte(
                Display.DIS__BACKLIGHT, updated_backlight_settings
            )
        except Exception as e:
            logger.error("Error blanking screen: " + str(e))

    def unblank_screen(self):
        try:
            logger.debug("Hub: unblank_screen")
            updated_backlight_settings = bitwise_ops.set_bits_high(
                BacklightRegister.DIS__BACKLIGHT__EN,
                self._i2c_device.read_unsigned_byte(Display.DIS__BACKLIGHT),
            )
            self._i2c_device.write_byte(
                Display.DIS__BACKLIGHT, updated_backlight_settings
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
            updated_audio_settings = bitwise_ops.set_bits_high(
                AudioRegister.AUD__CONFIG__HDMI,
                self._i2c_device.read_unsigned_byte(AudioConfig.AUD__CONFIG),
            )
            self._i2c_device.write_byte(AudioConfig.AUD__CONFIG, updated_audio_settings)
        except Exception as e:
            logger.error("Error enabling hdmi audio (multiplexer): " + str(e))

    def disable_hdmi_audio(self):
        try:
            logger.debug("Hub: disable_hdmi_audio")
            updated_audio_settings = bitwise_ops.set_bits_low(
                AudioRegister.AUD__CONFIG__HDMI,
                self._i2c_device.read_unsigned_byte(AudioConfig.AUD__CONFIG),
            )
            self._i2c_device.write_byte(AudioConfig.AUD__CONFIG, updated_audio_settings)
        except Exception as e:
            logger.error("Error disabling hdmi audio (multiplexer): " + str(e))

    def read_audio_hdmi_control(self):
        logger.debug("Hub: reading hdmi audio control")
        return self._i2c_device.read_bits_from_byte_at_address(
            bits_to_read=AudioRegister.AUD__CONFIG__HDMI,
            addr_to_read=AudioConfig.AUD__CONFIG,
        )

    def read_audio_headphone_detect_flag(self):
        logger.debug("Hub: reading hdmi audio control")
        return self._i2c_device.read_bits_from_byte_at_address(
            bits_to_read=AudioRegister.AUD__CONFIG__HPDET,
            addr_to_read=AudioConfig.AUD__CONFIG,
        )

    def read_realtime_counter(self):
        logger.debug("Hub: reading real time counter unix time")
        return self._i2c_device.read_n_unsigned_bytes(
            UnixTime.MISC__realtime_COUNTER, 4
        )

    def set_realtime_counter(self, time):
        logger.debug("Hub: Wrting real time counter unix time")
        self._i2c_device.write_n_bytes(UnixTime.MISC__realtime_COUNTER, time)

    def read_apcad_battery_pack_in(self):
        logger.debug("Reading APCAD__VOLT_BATT_IN")
        return self._i2c_device.read_unsigned_word(APCAD.APCAD__VOLT_BATT_IN)

    def read_apcad_dc_jack_in(self):
        logger.debug("Reading APCAD__VOLT_DC_IN")
        return self._i2c_device.read_unsigned_word(APCAD.APCAD__VOLT_DC_IN)

    def read_apcad_modular_power_in(self):
        logger.debug("Reading APCAD__VOLT_MPWR_IN")
        return self._i2c_device.read_unsigned_word(APCAD.APCAD__VOLT_MPWR_IN)

    def read_apcad_system_voltage_persist(self):
        logger.debug("Reading APCAD__VOLT_VSYS_PRST")
        return self._i2c_device.read_unsigned_word(APCAD.APCAD__VOLT_VSYS_PRST)

    def read_apcad_5v_persist(self):
        logger.debug("Reading APCAD__VOLT_5V_PRST")
        return self._i2c_device.read_unsigned_word(APCAD.APCAD__VOLT_5V_PRST)

    def read_apcad_5v(self):
        logger.debug("Reading APCAD__VOLT_5V")
        return self._i2c_device.read_unsigned_word(APCAD.APCAD__VOLT_5V)

    def read_apcad_5v_usb(self):
        logger.debug("Reading APCAD__VOLT_5V_USB")
        return self._i2c_device.read_unsigned_word(APCAD.APCAD__VOLT_5V_USB)

    def read_apcad_3v3(self):
        logger.debug("Reading APCAD__VOLT_3V3")
        return self._i2c_device.read_unsigned_word(APCAD.APCAD__VOLT_3V3)

    ########################
    # Internal methods
    ########################
    def _read_battery_registers_if_min_time_passed(self):
        # Reset battery sleep counter if time has passed
        if self._battery_sleep_counter >= self._battery_min_read_sleep_s:
            self._battery_sleep_counter = 0

        # Read battery state if counter reset
        if self._battery_sleep_counter == 0:
            self._read_battery_registers()

        # Update battery counter with sleep time
        self._battery_sleep_counter += self._cycle_sleep_time

    def _read_battery_registers(self):
        logger.debug("Hub: Reading battery registers")

        # Get values from the hub
        current_ma = self._i2c_device.read_signed_word(BatteryControl.BAT__CURRENT)
        voltage_v = self._i2c_device.read_unsigned_word(BatteryControl.BAT__VOLTAGE)
        relative_state_of_charge = self._i2c_device.read_unsigned_byte(
            BatteryControl.BAT__RSOC
        )
        time_until_empty_mins = self._i2c_device.read_unsigned_word(
            BatteryControl.BAT__TIME_TO_EMPTY
        )
        time_until_full_mins = self._i2c_device.read_unsigned_word(
            BatteryControl.BAT__TIME_TO_FULL
        )
        # Set the charging state base on the current
        power_cable_connected = self.read_ac_power_connected()

        # If the times are set to 0xFFFF, that means infinite (e.g. not charging or
        # discharging), so we set these to 0 to make more readable
        if time_until_empty_mins == 0xFFFF:
            time_until_empty_mins = 0

        if time_until_full_mins == 0xFFFF:
            time_until_full_mins = 0

        if power_cable_connected:
            if relative_state_of_charge >= 97:
                charging_state = 2  # full battery
            else:
                charging_state = 1  # charging
        else:
            charging_state = 0  # discharging

        # Set the wattage in tenths of a watt
        wattage = int(current_ma * voltage_v * 0.00001)

        # Show time until full/empty based on charging state
        remaining_time = (
            time_until_full_mins if power_cable_connected else time_until_empty_mins
        )

        capacity = 100 if charging_state == 2 else relative_state_of_charge
        self._state.set_battery_state(charging_state, capacity, remaining_time, wattage)

    def _read_oled_register(self):
        logger.debug("Hub: Reading OLED register")

        oled_controlled_state = self._i2c_device.read_unsigned_byte(
            HardwareControl.CTRL__UI_OLED_CTRL
        )
        self._state.set_oled_controller(
            bitwise_ops.get_bits(
                OLEDControlRegister.CTRL__UI_OLED_CTRL__RPI_CONTROL,
                oled_controlled_state,
            )
        )
        self._state.set_oled_using_spi0_state(
            bitwise_ops.get_bits(
                OLEDControlRegister.CTRL__UI_OLED_CTRL__SPI_ALT, oled_controlled_state
            )
        )

    def _read_ui_buttons_register(self):
        logger.debug("Hub: Reading UI button register")

        ui_button_state = self._i2c_device.read_unsigned_byte(
            HardwareControl.CTRL__UI_BUTTON_CTRL
        )

        self._state.set_buttons_route_to_gpio_state(
            bitwise_ops.get_bits(
                UIButtonsRegister.CTRL__UI_BUTTON_CTRL__DIRECT_GPIO, ui_button_state
            )
        )

        self._state.set_up_button_press_state(
            bitwise_ops.get_bits(
                UIButtonsRegister.CTRL__UI_BUTTON_CTRL__UP, ui_button_state
            )
        )

        self._state.set_down_button_press_state(
            bitwise_ops.get_bits(
                UIButtonsRegister.CTRL__UI_BUTTON_CTRL__DOWN, ui_button_state
            )
        )

        self._state.set_select_button_press_state(
            bitwise_ops.get_bits(
                UIButtonsRegister.CTRL__UI_BUTTON_CTRL__SELECT, ui_button_state
            )
        )

        self._state.set_cancel_button_press_state(
            bitwise_ops.get_bits(
                UIButtonsRegister.CTRL__UI_BUTTON_CTRL__CANCEL, ui_button_state
            )
        )

    def _get_cpu_temp(self):
        logger.debug("Getting CPU temperature")
        cpu_temp_file = "/sys/class/thermal/thermal_zone0/temp"
        try:
            file = open(cpu_temp_file, "r")
        except FileNotFoundError as ferr:
            logger.warning("CPU temperature file not found")
            logger.warning(ferr)
            return None
        except Exception as ex:
            logger.warning(
                "Unhandled exception when trying to open CPU temperature file"
            )
            logger.warning(ex)
            return None
        else:
            str_val = file.readline().strip()

        logger.debug("Parsing CPU temperature")

        try:
            cpu_temp = int(str_val)
        except ValueError as verr:
            logger.warning("CPU temp from file not valid integer")
            logger.warning(verr)
            return None
        except Exception as ex:
            logger.warning("Unhandled exception when parsing CPU temp")
            logger.warning(ex)
            return None

        temp_celsius = int(cpu_temp / 1000)

        logger.debug("CPU temperature: " + str(temp_celsius))

        return temp_celsius

    def _write_cpu_temp_register(self):
        cpu_temp = self._get_cpu_temp()

        if cpu_temp is None:
            logger.warning("CPU temperature is not valid - skipping write to register")
            return

        self.set_rpi_cpu_temp(cpu_temp)

    def _write_cpu_temp_register_if_min_time_passed(self):
        # Reset counter if time has passed
        if self._cpu_temp_sleep_counter >= self._cpu_temp_min_read_sleep_s:
            self._cpu_temp_sleep_counter = 0

        # Read CPU state and write to register if counter reset
        if self._cpu_temp_sleep_counter == 0:
            self._write_cpu_temp_register()

        # Update CPU temp counter with sleep time
        self._cpu_temp_sleep_counter += self._cycle_sleep_time

    def _poll_hub(self):
        try:
            logger.debug("Starting poll hub registers")
            self._read_battery_registers_if_min_time_passed()
            self._read_shutdown_control()
            self._read_oled_register()
            self._read_ui_buttons_register()
            self._write_cpu_temp_register_if_min_time_passed()
            logger.debug("Finished poll hub registers")

        except TypeError as e:
            raise e

        except Exception as e:
            logger.error("Error polling hub: " + str(e))

    def check_button_pressed_recently(self):
        button_pressed_now = (
            self._state.up_button_press_state != 0
            or self._state.down_button_press_state != 0
            or self._state.select_button_press_state != 0
            or self._state.cancel_button_press_state != 0
        )
        if button_pressed_now:
            self.button_pressed_recently = True
            self._accelerated_cycle_sleep_time_counter = 0

        if self.button_pressed_recently:
            self._accelerated_cycle_sleep_time_counter += 1
        else:
            self._accelerated_cycle_sleep_time_counter = 0

        if (
            self._accelerated_cycle_sleep_time_counter
            >= self._accelerated_cycle_sleep_time_counter_limit
        ):
            self.button_pressed_recently = False

    def _main_thread_loop(self):
        while self._run_polling_thread:
            try:
                self._poll_hub()

                self.check_button_pressed_recently()

                time_to_sleep = (
                    self._accelerated_cycle_sleep_time
                    if self.button_pressed_recently
                    else self._cycle_sleep_time
                )

                sleep(time_to_sleep)

            except Exception as e:
                logger.warning("Exception during hub polling")
                logger.warning(e)
