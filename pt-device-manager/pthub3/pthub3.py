from ptcommon.logger import PTLogger
from ptcommon.common_ids import DeviceID
from pthub3.pthub3_state import State
from pthub3.pthub3_connection import HubConnection


def initialise():
    global _state
    global _hub_connection

    _state = State()
    _hub_connection = HubConnection()

    PTLogger.info("Initialising I2C connection...")

    if _hub_connection.initialise(_state) is False:
        PTLogger.warning("Unable to detect pi-topHUB v3 connection")
        return False

    PTLogger.info("Initialised")
    return True


def register_client(
        on_brightness_changed_func=None,
        on_screen_blank_state_changed_func=None,
        on_native_display_connect_state_changed_func=None,
        on_external_display_connect_state_changed_func=None,
        on_lid_open_state_changed_func=None,
        on_shutdown_requested_func=None,
        on_battery_state_changed_func=None,
        on_button_press_state_changed_func=None,
        on_oled_pi_controlled_state_change_func=None,
        # on_oled_spi_state_change_func=None,  # Not implemented in device manager - not yet required
        on_direct_button_gpio_state_change_func=None
):
    _state.register_client(
        on_brightness_changed_func,
        on_screen_blank_state_changed_func,
        on_native_display_connect_state_changed_func,
        on_external_display_connect_state_changed_func,
        on_lid_open_state_changed_func,
        on_shutdown_requested_func,
        on_battery_state_changed_func,
        on_button_press_state_changed_func,
        on_oled_pi_controlled_state_change_func,
        # on_oled_spi_state_change_func,
        on_direct_button_gpio_state_change_func
    )


def start():
    PTLogger.debug("Hub connection loop starting...")
    _hub_connection.start()
    PTLogger.info("Hub connection loop started")


def stop():
    PTLogger.debug("Hub connection loop stopping...")
    _hub_connection.stop()
    PTLogger.info("Hub connection loop stopped")


def increment_brightness():
    _hub_connection.increment_brightness()


def decrement_brightness():
    _hub_connection.decrement_brightness()


def set_brightness(val):
    _hub_connection.set_brightness(val)


def set_oled_pi_control_state(controlled_by_pi):
    _hub_connection.set_oled_control(controlled_by_pi)


def reset_oled():
    _hub_connection.reset_oled()


def set_oled_use_spi0(use_spi0):
    _hub_connection.set_oled_use_spi0(use_spi0)


def blank_screen():
    _hub_connection.blank_screen()


def unblank_screen():
    _hub_connection.unblank_screen()


def shutdown():
    _hub_connection.shutdown()


def get_brightness():
    return _state.brightness


def get_oled_pi_control_state():
    return _state.oled_is_pi_controlled


def get_oled_use_spi0():
    return _state.oled_is_using_spi0


def get_lid_open_state():
    return _state.lid_open


def get_screen_blanked_state():
    return _state.screen_blanked


def get_shutdown_button_held():
    return _hub_connection.read_shutdown_button_held()


def get_shutdown_mode():
    return _hub_connection.read_shutdown_mode()


def set_shutdown_mode(mode):
    _hub_connection.set_shutdown_mode(mode)


def get_ac_power_connected():
    return _hub_connection.read_ac_power_connected()


def set_shutdown_cancel(cancel):
    _hub_connection.set_shutdown_cancel(cancel)


def get_shutdown_short_button_hold_turn_on():
    return _hub_connection.read_shutdown_short_button_hold_turn_on()


def get_shutdown_short_button_hold_turn_off():
    return _hub_connection.read_shutdown_short_button_hold_turn_off()


def get_shutdown_long_button_hold_turn_off():
    return _hub_connection.read_shutdown_long_button_hold_turn_off()


def set_shutdown_short_button_hold_turn_on(time):
    _hub_connection.set_shutdown_short_button_hold_turn_on(time)


def set_shutdown_short_button_hold_turn_off(time):
    _hub_connection.set_shutdown_short_button_hold_turn_off(time)


def set_shutdown_long_button_hold_turn_off(time):
    _hub_connection.set_shutdown_long_button_hold_turn_off(time)


def get_shutdown_mode1_timeout_min():
    _hub_connection.read_shutdown_mode1_timeout_min()


def set_shutdown_mode1_timeout_min(time):
    _hub_connection.set_shutdown_mode1_timeout_min(time)


def get_shutdown_mode2_timeout_min():
    return _hub_connection.read_shutdown_mode2_timeout_min()


def set_shutdown_mode2_timeout_min(time):
    _hub_connection.set_shutdown_mode2_timeout_min(time)


def get_shutdown_mode1_timeout_max():
    return _hub_connection.read_shutdown_mode1_timeout_max()


def set_shutdown_mode1_timeout_max(time):
    _hub_connection.set_shutdown_mode1_timeout_max(time)


def get_shutdown_mode2_timeout_max():
    return _hub_connection.read_shutdown_mode2_timeout_max()


def set_shutdown_mode2_timeout_max(time):
    _hub_connection.set_shutdown_mode2_timeout_max(time)


def get_shutdown_mode3_timeout():
    return _hub_connection.read_shutdown_mode3_timeout()


def set_shutdown_mode3_timeout(time):
    _hub_connection.set_shutdown_mode3_timeout(time)


def get_battery_cell3_voltage():
    return _hub_connection.read_battery_cell3_voltage()


def get_battery_cell4_voltage():
    return _hub_connection.read_battery_cell4_voltage()


def get_battery_error_flag():
    return _hub_connection.read_battery_error_flag()


def get_battery_manufacture_date():
    return _hub_connection.read_battery_manufacture_date()


def get_battery_charging_error_detect():
    return _hub_connection.read_battery_charging_error_detect()


def get_audio_hdmi_control():
    return _hub_connection.read_audio_hdmi_control()


def get_audio_headphone_detect_flag():
    return _hub_connection.read_audio_headphone_detect_flag()


def get_realtime_counter():
    return _hub_connection.read_realtime_counter()


def set_realtime_counter(time):
    _hub_connection.set_realtime_counter(time)


def get_mcu_software_version_major():
    return _hub_connection.read_mcu_software_version_major()


def get_mcu_software_version_minor():
    return _hub_connection.read_mcu_software_version_minor()


def get_sch_hardware_version_major():
    return _hub_connection.read_sch_hardware_version_major()


def get_sch_hardware_version_minor():
    return _hub_connection.read_sch_hardware_version_minor()


def get_brd_version():
    return _hub_connection.read_brd_version()


def get_part_name():
    return _hub_connection.read_part_name()


def get_part_number():
    return _hub_connection.read_part_number()


def get_serial_id():
    return _hub_connection.read_serial_id()


def get_display_mcu_software_version_major():
    return _hub_connection.read_display_mcu_software_version_major()


def get_display_mcu_software_version_minor():
    return _hub_connection.read_display_mcu_software_version_minor()


def get_display_sch_hardware_version_major():
    return _hub_connection.read_display_sch_hardware_version_major()


def get_display_sch_hardware_version_minor():
    return _hub_connection.read_display_sch_hardware_version_minor()


def get_display_brd_version():
    return _hub_connection.read_display_brd_version()


def get_display_part_name():
    return _hub_connection.read_display_part_name()


def get_display_part_nunber():
    return _hub_connection.read_display_part_number()


def get_display_serial_id():
    return _hub_connection.read_display_serial_id()


def get_uptime_standby_time():
    return _hub_connection.read_uptime_standby_time()


def get_uptime_rails_on_time():
    return _hub_connection.read_uptime_rails_on_time()


def get_lifetime_standby_time():
    return _hub_connection.read_lifetime_standby_time()


def get_lifetime_rails_on_time():
    return _hub_connection.read_lifetime_rails_on_time()


def get_lifetime_number_of_power_cycles():
    return _hub_connection.read_lifetime_number_of_power_cycles()


def get_screen_test_mode():
    return _hub_connection.read_screen_test_mode()


def set_screen_test_mode(test_mode):
    _hub_connection.set_screen_test_mode(test_mode)


def get_battery_temperature():
    return _hub_connection.read_battery_temperature()


def get_battery_cell1_voltage():
    return _hub_connection.read_battery_cell1_voltage()


def get_battery_cell2_voltage():
    return _hub_connection.read_battery_cell2_voltage()


def get_battery_serial_number():
    return _hub_connection.read_battery_serial_number()


def get_battery_manufacture_date():
    return _hub_connection.read_battery_manufacture_date()


def get_battery_storage_mode():
    return _hub_connection.read_battery_storage_mode()


def set_battery_storage_mode(set_storage_mode):
    _hub_connection.set_battery_storage_mode(set_storage_mode)


def get_modular_connector_detected_device():
    return _hub_connection.read_modular_connector_device_detection()


def get_battery_display_i2c_control():
    _hub_connection.read_battery_display_i2c_control()


def set_battery_display_i2c_control(controlled_by_pi):
    _hub_connection.set_battery_display_i2c_control(controlled_by_pi)


def get_raspi_board_detect_flag():
    return _hub_connection.read_raspi_board_detect_flag()


def get_raspi_board_prevent_boot():
    return _hub_connection.read_raspi_board_prevent_boot()


def set_raspi_board_prevent_boot(prevent_boot):
    _hub_connection.set_raspi_board_prevent_boot(prevent_boot)


def get_apcad_battery_pack_in():
    return _hub_connection.read_apcad_battery_pack_in()


def get_apcad_dc_jack_in():
    return _hub_connection.read_apcad_dc_jack_in()


def get_apcad_modular_power_in():
    return _hub_connection.read_apcad_modular_power_in()


def get_apcad_system_voltage_persist():
    return _hub_connection.read_apcad_system_voltage_persist()


def get_apcad_5v_persist():
    return _hub_connection.read_apcad_5v_persist()


def get_apcad_5v():
    return _hub_connection.read_apcad_5v()


def get_apcad_5v_usb():
    return _hub_connection.read_apcad_5v_usb()


def get_apcad_3v3():
    return _hub_connection.read_apcad_3v3()


def get_apcad_control_dc_mpwr_input_auto_overcurrent_protection():
    return _hub_connection.read_apcad_control_dc_mpwr_input_auto_overcurrent_protection()


def set_fan_manual_speed(fan_speed):
    _hub_connection.set_fan_manual_speed(fan_speed)


def set_fan_mode_auto(auto):
    _hub_connection.set_fan_mode_auto(auto)


def read_mcu_rpi_cpu_temp():
    return _hub_connection.read_mcu_rpi_cpu_temp()


def read_fan_mode_auto():
    return _hub_connection.read_fan_mode_auto()


def read_fan_speed():
    return _hub_connection.read_fan_speed()


# Deprecated


def get_screen_off_state():
    return _state.screen_blanked


def get_device_id():
    return DeviceID.pi_top_4


def get_battery_state():
    return _state.battery_charging_state, _state.battery_capacity, _state.battery_remaining_time, _state.battery_wattage


def get_battery_time_state():
    return _state.battery_remaining_time


def get_battery_capacity_state():
    return _state.battery_capacity


def enable_hdmi_to_i2s_audio():
    _hub_connection.enable_hdmi_audio()


def disable_hdmi_to_i2s_audio():
    _hub_connection.disable_hdmi_audio()


def set_speed(no_of_polls_per_second=4):
    _hub_connection.set_speed(no_of_polls_per_second)
