
# Handles logging to the systemd log (journalctl)

import inspect
import logging
from systemd.journal import JournalHandler


class Logger:

    def __init__(self, logging_level):

        self._logging_level = logging_level
        self._journal_log = logging.getLogger("pt-device-manager")

        self._journal_log.addHandler(JournalHandler())
        self._journal_log.setLevel(self._logging_level)
        self._journal_log.info("Logging started.")

    def print_message(self, message):
        if (self._logging_level <= 10):
            print(inspect.stack()[1][3] + ": " + message)
        else:
            print(message)

    def debug(self, message):
        if (self._logging_level <= 10):
            self.print_message(message)

        self._journal_log.debug(message)

    def info(self, message):
        if (self._logging_level <= 20):
            self.print_message(message)

        self._journal_log.info(message)

    def warning(self, message):
        if (self._logging_level <= 30):
            self.print_message(message)

        self._journal_log.warning(message)

    def error(self, message):
        if (self._logging_level <= 40):
            self.print_message(message)

        self._journal_log.error(message)
