# Instantiates and coordinates between the other classes
from pitopcommon.logger import PTLogger
from pitopcommon.common_ids import DeviceID
from pitopcommon.command_runner import run_command_background

from os import path
from systemd.daemon import notify
from time import sleep


class Controller:
    def __init__(
        self,
        publish_server,
        power_manager,
        hub_manager,
        idle_monitor,
        notification_manager,
        peripheral_manager,
        request_server,
        config_manager,
    ):
        self._continue_running = True

        self._publish_server = publish_server
        self._power_manager = power_manager
        self._hub_manager = hub_manager
        self._idle_monitor = idle_monitor
        self._notification_manager = notification_manager
        self._peripheral_manager = peripheral_manager
        self._request_server = request_server
        self._config_manager = config_manager

        # Initialise
        self._power_manager.initialise(self)
        self._hub_manager.initialise(self)
        self._idle_monitor.initialise(self)
        self._peripheral_manager.initialise(self)
        self._request_server.initialise(self)

        self.device_id = None

    def _set_host_device_id(self, device_id):
        self.device_id = device_id

        PTLogger.info(f"Setting device ID as {self.device_id}")

        self._config_manager.write_device_id_to_file(self.device_id)

        self._peripheral_manager.initialise_device_id(self.device_id)
        self._power_manager.set_device_id(self.device_id)

    def _set_host_device_id_from_hub(self):
        self._set_host_device_id(self._hub_manager.get_device_id())

    def start(self):
        PTLogger.info("Starting device manager...")

        last_identified_device_id = self._config_manager.get_last_identified_device_id()

        if self._publish_server.start_listening() is False:
            PTLogger.error("Unable to start listening on publish server")
            return False

        if self._hub_manager.connect_to_hub():
            self._hub_manager.start()
        else:
            PTLogger.error("No pi-top hub detected")
            self._set_host_device_id(DeviceID.unknown)
            return False

        # Wait until we have established what device we're running on.
        # This is due to the hub being detected, but the device it itself is yet to be determined.
        # This is only relevant for pi-topCEED.
        self._hub_manager.wait_for_device_identification()

        self._set_host_device_id_from_hub()

        # Stop device manager if no pi-top host detected
        if self.device_id == DeviceID.unknown:
            PTLogger.warning(
                "Unknown host device, despite successfully initialising a hub")
            return False

        # Check if any peripherals need to be set up
        self._peripheral_manager.auto_initialise_peripherals()

        PTLogger.info("Configured for dependencies - unblocking systemd")
        notify("READY=1")

        if self.device_id != last_identified_device_id:
            PTLogger.info(
                f"Host device has changed! Previous pi-top host: {str(last_identified_device_id)}")

        if self._peripheral_manager.start() is False:
            PTLogger.error("Unable to start peripheral manager")
            return False

        self._idle_monitor.start()

        if self._request_server.start_listening() is False:
            PTLogger.error("Unable to start listening on request server")
            return False

        sleep(0.5)

        PTLogger.info("Fully configured - running")

        while self._continue_running is True:
            sleep(0.5)

        return True

    def stop(self):
        PTLogger.info("Stopping device manager...")
        self._continue_running = False

        # Stop the other classes

        self._request_server.stop_listening()
        self._idle_monitor.stop()
        self._peripheral_manager.stop()
        self._hub_manager.stop()
        self._publish_server.stop_listening()

    ###########################################
    # Request server callback methods
    ###########################################

    def on_request_get_device_id(self):
        return self._hub_manager.get_device_id()

    def on_request_get_brightness(self):
        return self._hub_manager.get_brightness()

    def on_request_set_brightness(self, brightness):
        self._hub_manager.set_brightness(brightness)

    def on_request_increment_brightness(self):
        self._hub_manager.increment_brightness()

    def on_request_decrement_brightness(self):
        self._hub_manager.decrement_brightness()

    def on_request_blank_screen(self):
        self._hub_manager.blank_screen()

    def on_request_unblank_screen(self):
        self._hub_manager.unblank_screen()

    def on_request_battery_state(self):
        return self._hub_manager.get_battery_state()

    def on_request_get_peripheral_enabled(self, peripheral_id):
        return self._peripheral_manager.get_peripheral_id_enabled(peripheral_id)

    def on_request_get_screen_blanking_timeout(self):
        return self._idle_monitor.get_configured_timeout()

    def on_request_set_screen_blanking_timeout(self, timeout):
        return self._idle_monitor.set_configured_timeout(timeout)

    def on_request_get_lid_open_state(self):
        if self._hub_manager.get_lid_open_state():
            return 1
        else:
            return 0

    def on_request_get_screen_backlight_state(self):
        if self._hub_manager.get_screen_blanked_state():
            return 0
        else:
            return 1

    def on_request_set_screen_backlight_state(self, backlight_on):
        if backlight_on:
            self._hub_manager.unblank_screen()
        else:
            self._hub_manager.blank_screen()

    def on_request_get_oled_control(self):
        if self._hub_manager.get_oled_pi_control_state():
            return 1
        else:
            return 0

    def on_request_set_oled_pi_control(self, is_pi_controlled):
        self._hub_manager.set_oled_pi_control_state(is_pi_controlled)

    def on_request_get_oled_spi_bus(self):
        if self._hub_manager.get_oled_use_spi0():
            return 0
        else:
            return 1

    def on_request_set_oled_spi_bus(self, spi_port_number):
        def enable_spi_dtoverlay_if_required_in_background(spi_port_number):
            PTLogger.info(f"Will use SPI port {spi_port_number}")
            if spi_port_number == 0:
                run_command_background("dtparam spi=on")
                self._notification_manager.display_old_spi_bus_still_active_message()
            else:
                run_command_background("dtparam spi=off")
                if not path.exists("/dev/spidev1.0"):
                    run_command_background(
                        f"dtoverlay spi{spi_port_number}-1cs")

        enable_spi_dtoverlay_if_required_in_background(spi_port_number)
        self._hub_manager.set_oled_use_spi0(spi_port_number == 0)

    ###########################################
    # Idle Monitor callback methods
    ###########################################

    def on_idletime_threshold_exceeded(self):
        self._hub_manager.blank_screen()

    def on_exceeded_idletime_reset(self):
        self._hub_manager.unblank_screen()

    ###########################################
    # Hub Manager callback methods
    ###########################################

    def on_hub_shutdown_requested(self):
        self._publish_server.publish_shutdown_requested()

        # Let the hub modules handle any logic required to shutdown
        self._hub_manager.shutdown()

        # Now trigger the OS shutdown
        self._power_manager.shutdown()

    def on_hub_brightness_changed(self, new_value):
        self._publish_server.publish_brightness_changed(new_value)

    def _battery_state_is_fully_defined(self):
        battery_charging_state, battery_capacity, battery_time, battery_wattage = (
            self._hub_manager.get_battery_state()
        )
        charging_defined = battery_charging_state != -1
        capacity_defined = battery_capacity != -1
        time_defined = battery_time != -1
        wattage_defined = battery_wattage != -1
        return (
            charging_defined and capacity_defined and time_defined and wattage_defined
        )

    def on_hub_battery_state_changed(
        self, charging_state, capacity, time_remaining, wattage
    ):
        if self._battery_state_is_fully_defined():
            self._publish_server.publish_battery_state_changed(
                charging_state, capacity, time_remaining, wattage
            )

            # Let the power manager know about the state of the battery
            # so it can trigger warnings or safe-shutdown as necessary
            self._power_manager.set_battery_capacity(capacity)
            self._power_manager.set_battery_charging(charging_state)
            self._power_manager.process_battery_state()

    def on_screen_blank_state_changed(self, blanked_state):
        if blanked_state:
            self.on_screen_blanked()
        else:
            self.on_screen_unblanked()

    def on_screen_blanked(self):
        self._publish_server.publish_screen_blanked()

    def on_screen_unblanked(self):
        self._publish_server.publish_screen_unblanked()

    def on_lid_open_state_changed(self, lid_open_state):
        if lid_open_state:
            self.on_lid_opened()
        else:
            self.on_lid_closed()

    def on_lid_opened(self):
        self._publish_server.publish_lid_opened()
        self._hub_manager.unblank_screen()

    def on_lid_closed(self):
        self._publish_server.publish_lid_closed()
        self._hub_manager.blank_screen()

    def on_button_press_state_changed(self, button_pressed, is_pressed):
        if button_pressed == "Up":
            self._publish_server.publish_up_button_press_state_changed(
                is_pressed)
        elif button_pressed == "Down":
            self._publish_server.publish_down_button_press_state_changed(
                is_pressed)
        elif button_pressed == "Select":
            self._publish_server.publish_select_button_press_state_changed(
                is_pressed)
        elif button_pressed == "Cancel":
            self._publish_server.publish_cancel_button_press_state_changed(
                is_pressed)

    def on_device_id_changed(self, device_id_int):
        # Inform the power manager that the device id has changed, so
        # it can handle battery notifications correctly
        self._power_manager.set_device_id(device_id_int)

    def on_oled_pi_controlled_state_changed(self, oled_controlled_by_pi):
        self._publish_server.publish_oled_pi_controlled_state_changed(
            oled_controlled_by_pi)

    def on_oled_spi_bus_changed(self, oled_uses_spi0):
        self._publish_server.publish_oled_spi_state_changed(oled_uses_spi0)

    ###########################################
    # Peripheral Manager callback methods
    ###########################################

    def on_peripheral_connected(self, peripheral_id_int):
        self._publish_server.publish_peripheral_connected(peripheral_id_int)
        self._hub_manager.unblank_screen()

    def on_peripheral_disconnected(self, peripheral_id_int):
        self._publish_server.publish_peripheral_disconnected(peripheral_id_int)

    def on_enable_hdmi_to_i2s_audio(self):
        self._hub_manager.enable_hdmi_to_i2s_audio()

    def on_disable_hdmi_to_i2s_audio(self):
        self._hub_manager.disable_hdmi_to_i2s_audio()

    def on_unsupported_hardware(self):
        self._publish_server.publish_unsupported_hardware()
        self._notification_manager.display_unsupported_hardware_message()
        self._hub_manager.unblank_screen()

    def on_reboot_required(self):
        self._publish_server.publish_reboot_required()
        self._notification_manager.display_reboot_message()
        self._hub_manager.unblank_screen()

    ###########################################
    # Power manager callback methods
    ###########################################

    def on_clear_battery_warning(self):
        self._notification_manager.clear_battery_warning_message()

    def on_low_battery_warning(self):
        self._publish_server.publish_low_battery_warning()
        self._notification_manager.display_low_battery_warning_message()
        self._hub_manager.unblank_screen()

    def on_critical_battery_warning(self):
        self._publish_server.publish_critical_battery_warning()
        self._notification_manager.display_critical_battery_warning_message()
        self._hub_manager.unblank_screen()
