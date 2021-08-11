from pitop.common.logger import PTLogger

from subprocess import getoutput
from enum import IntEnum
from threading import Thread


class MessageID(IntEnum):
    title_low_battery = 0
    body_low_battery = 1
    title_critical_battery = 2
    body_critical_battery = 3
    title_reboot = 4
    body_reboot = 5
    title_unsupported = 6
    body_unsupported = 7
    title_spi_bus_active = 8
    body_spi_bus_active = 9


messages_en = {
    MessageID.title_low_battery: "Low Battery",
    MessageID.body_low_battery: "Your pi-top's battery level is low. Please plug in a charging cable to prevent your system from shutting down.",

    MessageID.title_critical_battery: "Low Battery",
    MessageID.body_critical_battery: "Your pi-top's battery level is critically low. "
    "System will shut down shortly unless a charging cable is plugged in.",

    MessageID.title_reboot: "Reboot Required",
    MessageID.body_reboot: "Recently detected hardware requires a system settings modification.\nPlease reboot to enable hardware support.",

    MessageID.title_unsupported: "Hardware Incompatible",
    MessageID.body_unsupported: "Recently detected hardware is not supported on your system",

    MessageID.title_spi_bus_active: "SPI bus changed",
    MessageID.body_spi_bus_active: "OLED is now set to use SPI0, but SPI1 is still active. "
    "To reset this, please reboot. For more information, please see the pi-top knowledge base.",
}

# TODO: Get system language, and swap if not english etc.
messages = messages_en


class NotificationManager:
    def __init__(self):
        self.__battery_warning_notification_id = -1

    def __is_battery_notification(self, message_title_id):
        low_battery = message_title_id == MessageID.title_low_battery
        critical_battery = message_title_id == MessageID.title_critical_battery
        return low_battery or critical_battery

    def __notify_send_command(self, message_title_id, message_text_id, icon_name, timeout=0, action_text=None, action=None):
        cmd = "/usr/bin/pt-notify-send "

        cmd += "--print-id "
        cmd += "--expire-time=" + str(timeout) + " "

        if self.__battery_warning_notification_id != -1:
            cmd += "--replace=" + \
                str(self.__battery_warning_notification_id) + " "

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

    def __show_message_in_thread(self, message_title_id, message_text_id, icon_name, action_text=None, action=None):
        Thread(
            target=self.__show_message,
            args=[message_title_id, message_text_id,
                  icon_name, action_text, action]
        ).start()

    def __show_message(self, message_title_id, message_text_id, icon_name, action_text=None, action=None):

        try:
            cmd = self.__notify_send_command(
                message_title_id, message_text_id, icon_name, action_text=action_text, action=action)
            notification_output = getoutput(cmd)

            PTLogger.info("Notification output:" + notification_output)
            if notification_output.isnumeric() and self.__is_battery_notification(message_title_id):
                self.__battery_warning_notification_id = int(
                    notification_output)
            else:
                PTLogger.warning("Notification output was not a valid id")

        except Exception as e:
            PTLogger.warning("Failed to show message: " + str(e))

    def clear_battery_warning_message(self):
        PTLogger.debug("Attempting to clear battery warning message if needed")
        if self.__battery_warning_notification_id != -1:
            PTLogger.debug("Clearing battery warning message")
            cmd = "/usr/bin/pt-notify-send --close=" + \
                str(self.__battery_warning_notification_id)
            getoutput(cmd)
            self.__battery_warning_notification_id = -1

    def display_critical_battery_warning_message(self):
        PTLogger.info("Displaying critical battery warning message")

        self.__show_message(
            message_title_id=MessageID.title_critical_battery,
            message_text_id=MessageID.body_critical_battery,
            icon_name="notification-battery-low",
        )

    def display_low_battery_warning_message(self):
        PTLogger.info("Displaying low battery warning message")

        self.__show_message(
            message_title_id=MessageID.title_low_battery,
            message_text_id=MessageID.body_low_battery,
            icon_name="notification-battery-low",
        )

    def display_reboot_message(self):
        PTLogger.info("Displaying reboot message")

        self.__show_message(
            message_title_id=MessageID.title_reboot,
            message_text_id=MessageID.body_reboot,
            icon_name="dialog-information",
        )

    def display_unsupported_hardware_message(self):
        PTLogger.info("Displaying unsupported hardware message")

        self.__show_message(
            message_title_id=MessageID.title_unsupported,
            message_text_id=MessageID.body_unsupported,
            icon_name="computer-fail",
        )

    def display_old_spi_bus_still_active_message(self):
        PTLogger.info("Displaying old SPI bus is still active message")
        open_knowledge_base_cmd = "chromium-browser --new-window https://knowledgebase.pi-top.com/"
        self.__show_message_in_thread(
            message_title_id=MessageID.title_spi_bus_active,
            message_text_id=MessageID.body_spi_bus_active,
            icon_name="messagebox_info",
            action_text="Learn More",
            action=open_knowledge_base_cmd,
        )
