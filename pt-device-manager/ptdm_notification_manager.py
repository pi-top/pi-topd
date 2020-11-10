from pitop.core.logger import PTLogger
from subprocess import getoutput
from enum import IntEnum


class MessageID(IntEnum):
    title_low_battery = 0
    body_low_battery = 1
    title_critical_battery = 2
    body_critical_battery = 3
    title_reboot = 4
    body_reboot = 5
    title_unsupported = 6
    body_unsupported = 7


messages_en = {
    MessageID.title_low_battery: "Low Battery",
    MessageID.body_low_battery: "Your pi-top's battery level is low. Please plug in a charging cable to prevent your system from shutting down.",

    MessageID.title_critical_battery: "Low Battery",
    MessageID.body_critical_battery: "Your pi-top's battery level is critically low. System will shut down shortly unless a charging cable is plugged in.",

    MessageID.title_reboot: "Reboot Required",
    MessageID.body_reboot: "Recently detected hardware requires a system settings modification.\nPlease reboot to enable hardware support.",

    MessageID.title_unsupported: "Hardware Incompatible",
    MessageID.body_unsupported: "Recently detected hardware is not supported on your system"
}

# TODO: Get system language, and swap if not english etc.
messages = messages_en


class NotificationManager:
    def __init__(self):
        self._battery_warning_notification_id = -1

    def _is_battery_notification(self, message_title_id):
        low_battery = message_title_id == MessageID.title_low_battery
        critical_battery = message_title_id == MessageID.title_critical_battery
        return low_battery or critical_battery

    def _notify_send_command(self, message_title_id, message_text_id, icon_name, timeout=0, action_text=None, action=None):
        cmd = "/usr/bin/pt-notify-send "

        cmd += "--print-id "
        cmd += "--expire-time=" + str(timeout) + " "

        if self._battery_warning_notification_id != -1:
            cmd += "--replace=" + \
                str(self._battery_warning_notification_id) + " "

        cmd += "--icon=" + icon_name + " "

        if action is not None:
            if action_text is None:
                action_text = ""
            cmd += "--action=\"" + action_text + ":" + action + "\" "

        cmd += "\"" + \
            messages[message_title_id] + "\" "
        cmd += "\"" + \
            messages[message_text_id] + "\""

        PTLogger.info("pt-notify-send command: " + str(cmd))
        return cmd

    def _show_message(self, message_title_id, message_text_id, icon_name):

        try:
            cmd = self._notify_send_command(
                message_title_id, message_text_id, icon_name)
            notification_output = getoutput(cmd)

            PTLogger.info("Notification output:" + notification_output)
            if notification_output.isnumeric() and self._is_battery_notification(message_title_id):
                self._battery_warning_notification_id = int(
                    notification_output)
            else:
                PTLogger.warning("Notification output was not a valid id")

        except Exception as e:
            PTLogger.warning("Failed to show message: " + str(e))

    def clear_battery_warning_message(self):
        PTLogger.debug("Attempting to clear battery warning message if needed")
        if self._battery_warning_notification_id != -1:
            PTLogger.debug("Clearing battery warning message")
            cmd = "/usr/bin/pt-notify-send --close=" + \
                str(self._battery_warning_notification_id)
            getoutput(cmd)
            self._battery_warning_notification_id = -1

    def display_critical_battery_warning_message(self):
        PTLogger.info("Displaying critical battery warning message")
        message_title_id = MessageID.title_critical_battery
        message_text_id = MessageID.body_critical_battery
        icon_name = "notification-battery-low"
        self._show_message(message_title_id, message_text_id, icon_name)

    def display_low_battery_warning_message(self):
        PTLogger.info("Displaying low battery warning message")
        message_title_id = MessageID.title_low_battery
        message_text_id = MessageID.body_low_battery
        icon_name = "notification-battery-low"
        self._show_message(message_title_id, message_text_id, icon_name)

    def display_reboot_message(self):
        PTLogger.info("Displaying reboot message")
        message_title_id = MessageID.title_reboot
        message_text_id = MessageID.body_reboot
        icon_name = "dialog-information"
        self._show_message(message_title_id, message_text_id, icon_name)

    def display_unsupported_hardware_message(self):
        PTLogger.info("Displaying unsupported hardware message")
        message_title_id = MessageID.title_unsupported
        message_text_id = MessageID.body_unsupported
        icon_name = "computer-fail"
        self._show_message(message_title_id, message_text_id, icon_name)
