
# Handles logging to the systemd log (journalctl)

import inspect
import logging
from systemd.journal import JournalHandler
import datetime


class Logger:

    log_level_indicators = {10: 'D', 20: 'I', 30: 'W', 40: 'E', 50: '!'}

    def __init__(self, logging_level, log_to_journal):

        self._logging_level = logging_level
        self._log_to_journal = log_to_journal
        self._journal_log = logging.getLogger("pt-device-manager")
        self._journal_log.addHandler(JournalHandler())
        self._journal_log.setLevel(self._logging_level)

        self._journal_log.info("Logging started.")

    def _print_message(self, message, level):
        if (self._log_to_journal is False and self._logging_level <= level):
            print("[" + datetime.datetime.now().strftime("%H:%M:%S.%f") + " " + self.log_level_indicators[level] + "] " + message)

    def debug(self, message):
        self._print_message(message, logging.DEBUG)
        self._journal_log.debug(message)

    def info(self, message):
        self._print_message(message, logging.INFO)
        self._journal_log.info(message)

    def warning(self, message):
        self._print_message(message, logging.WARNING)
        self._journal_log.warning(message)

    def error(self, message):
        self._print_message(message, logging.ERROR)
        self._journal_log.error(message)
