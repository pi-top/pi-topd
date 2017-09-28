from ptcommon.logger import PTLogger
import idletime
import time
import threading
from os import makedirs
from os import path
from os import remove


class IdleMonitor():

    DEFAULT_CYCLE_SLEEP_TIME = 5
    SENSITIVE_CYCLE_SLEEP_TIME = 0.2
    CONFIG_FILE_DIR = "/etc/pi-top/pt-device-manager/"
    CONFIG_FILE = CONFIG_FILE_DIR + "screen-timeout"

    def __init__(self):
        pass

    def initialise(self, callback_client):
        self.previous_idletime = 0
        self._callback_client = callback_client
        self._main_thread = None
        self._run_main_thread = False
        self._idle_timeout_s = 300
        self._cycle_sleep_time = self.DEFAULT_CYCLE_SLEEP_TIME

        if not path.exists(self.CONFIG_FILE_DIR):
            makedirs(self.CONFIG_FILE_DIR)

        self._get_timeout_from_file()

    def start(self):
        PTLogger.info("Starting idle time monitor...")
        if self._main_thread is None:
            self._main_thread = threading.Thread(target=self._main_thread_loop)

        self._run_main_thread = True
        self._main_thread.start()

    def stop(self):
        PTLogger.info("Stopping idle time monitor...")
        self._run_main_thread = False
        self._main_thread.join()
        PTLogger.debug("Stopped idle time monitor.")

    def get_configured_timeout(self):
        return self._idle_timeout_s

    def set_configured_timeout(self, timeout):
        self._idle_timeout_s = timeout
        self._set_timeout_in_file()

    # Internal methods

    def _emit_idletime_threshold_exceeded(self):
        if (self._callback_client is not None):
            PTLogger.info("Idletime threshold exceeded")
            self._callback_client._on_idletime_threshold_exceeded()

    def _emit_exceeded_idletime_reset(self):
        if (self._callback_client is not None):
            PTLogger.info("Idletime reset")
            self._callback_client._on_exceeded_idletime_reset()

    def _get_timeout_from_file(self):
        if path.exists(self.CONFIG_FILE):
            file = open(self.CONFIG_FILE, 'r+')
            self._idle_timeout_s = int(file.read().strip())
            file.close()

        PTLogger.info("Idletime retrieved from config: " + str(self._idle_timeout_s))

    def _set_timeout_in_file(self):
        if path.exists(self.CONFIG_FILE):
            remove(self.CONFIG_FILE)

        file = open(self.CONFIG_FILE, 'w')
        file.write(str(self._idle_timeout_s) + "\n")
        file.close()

        PTLogger.info("Idletime set in config: " + str(self._idle_timeout_s))

    def _main_thread_loop(self):
        while self._run_main_thread:
            time_since_idle = idletime.get_idle_time()

            if (time_since_idle != -1):

                if (self._idle_timeout_s > 0):

                    timeout_expired = (time_since_idle > (self._idle_timeout_s * 1000))
                    idletime_reset = (time_since_idle < self.previous_idletime)

                    timeout_already_expired = (self.previous_idletime > (self._idle_timeout_s * 1000))

                    if timeout_expired and not timeout_already_expired:
                        self._emit_idletime_threshold_exceeded()
                        self._cycle_sleep_time = self.SENSITIVE_CYCLE_SLEEP_TIME
                    elif idletime_reset and timeout_already_expired:
                        self._emit_exceeded_idletime_reset()
                        self._cycle_sleep_time = self.DEFAULT_CYCLE_SLEEP_TIME

                    self.previous_idletime = time_since_idle

            else:
                PTLogger.warning("pt-idletime.get_idle_time() returned -1. Check the configuration of xhost.")

            for i in range(5):
                time.sleep(self._cycle_sleep_time / 5)

                if (self._run_main_thread is False):
                    break
