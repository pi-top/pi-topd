from pitop.common.logger import PTLogger
from subprocess import check_output
from subprocess import CalledProcessError
from os import devnull
from os import makedirs
from os import path
from os import remove
from threading import Thread
from time import sleep


class IdleMonitor:

    DEFAULT_CYCLE_SLEEP_TIME = 5
    SENSITIVE_CYCLE_SLEEP_TIME = 0.2
    CONFIG_FILE_DIR = "/etc/pi-top/pt-device-manager/"
    CONFIG_FILE = CONFIG_FILE_DIR + "screen-timeout"

    def __init__(self):
        self._callback_client = None
        self.previous_idletime = 0
        self._main_thread = None
        self._run_main_thread = False
        self._idle_timeout_s = 300
        self._cycle_sleep_time = self.DEFAULT_CYCLE_SLEEP_TIME

        if not path.exists(self.CONFIG_FILE_DIR):
            makedirs(self.CONFIG_FILE_DIR)

        if not path.exists(self.CONFIG_FILE):
            self._set_timeout_in_file()

        self._get_timeout_from_file()

    def initialise(self, callback_client):
        self._callback_client = callback_client

    def start(self):
        PTLogger.info("Starting idle time monitor...")
        if self._main_thread is None:
            self._main_thread = Thread(target=self._main_thread_loop)

        self._run_main_thread = True
        self._main_thread.start()

    def stop(self):
        PTLogger.info("Stopping idle time monitor...")
        self._run_main_thread = False
        if self._main_thread is not None:
            self._main_thread.join()
        PTLogger.debug("Stopped idle time monitor.")

    def get_configured_timeout(self):
        return self._idle_timeout_s

    def set_configured_timeout(self, timeout):
        self._idle_timeout_s = timeout
        self._set_timeout_in_file()

    # Internal methods
    def _emit_idletime_threshold_exceeded(self):
        if self._callback_client is not None:
            PTLogger.info("Idletime threshold exceeded")
            self._callback_client.on_idletime_threshold_exceeded()

    def _emit_exceeded_idletime_reset(self):
        if self._callback_client is not None:
            PTLogger.info("Idletime reset")
            self._callback_client.on_exceeded_idletime_reset()

    def _get_timeout_from_file(self):
        if path.exists(self.CONFIG_FILE):
            try:
                file = open(self.CONFIG_FILE, "r+")
                file_contents = file.read().strip()
                file.close()

                self._idle_timeout_s = int(file_contents)
                PTLogger.info(
                    f"Idletime retrieved from config: {str(self._idle_timeout_s)}"
                )
            except Exception as e:
                PTLogger.warning(
                    f"Idletime could not be retrieved from config. Using default: {str(self._idle_timeout_s)}"
                )
                PTLogger.warning(e)

    def _set_timeout_in_file(self):
        if path.exists(self.CONFIG_FILE):
            remove(self.CONFIG_FILE)

        file = open(self.CONFIG_FILE, "w")
        file.write(str(self._idle_timeout_s) + "\n")
        file.close()

        PTLogger.info(f"Idletime set in config: {str(self._idle_timeout_s)}")

    def _main_thread_loop(self):
        startup_wait_counter = 0
        startup_wait_time = 15

        PTLogger.info(
            f"Waiting {str(startup_wait_time)} seconds before starting main idletime check thread..."
        )
        while self._run_main_thread and startup_wait_counter < startup_wait_time:
            startup_wait_counter += 1
            sleep(1)

        PTLogger.info("Starting main idletime check thread...")
        while self._run_main_thread:
            FNULL = open(devnull, "w")

            try:
                xprintidle_resp = check_output(["xprintidle"], stderr=FNULL)
            except CalledProcessError:
                PTLogger.warning(
                    "Unable to call xprintidle - have non-network local"
                    "connections been added to X server access control list?"
                )
                break

            xprintidle_resp_str = xprintidle_resp.decode("utf-8")

            try:
                idletime_ms = int(xprintidle_resp_str)
            except ValueError:
                PTLogger.warning(
                    "Unable to convert xprintidle response to integer")
                break

            timeout_expired = idletime_ms > (self._idle_timeout_s * 1000)
            idletime_reset = idletime_ms < self.previous_idletime
            PTLogger.debug(f"MS since idle: \t{str(idletime_ms)}")
            PTLogger.debug(f"Timeout Expired?:\t{str(timeout_expired)}")
            PTLogger.debug(f"Idletime Expired?:\t{str(idletime_reset)}")

            if self._idle_timeout_s > 0:
                timeout_already_expired = (
                    self.previous_idletime > self._idle_timeout_s * 1000
                )

                if timeout_expired and not timeout_already_expired:
                    self._emit_idletime_threshold_exceeded()
                    self._cycle_sleep_time = self.SENSITIVE_CYCLE_SLEEP_TIME
                elif idletime_reset and timeout_already_expired:
                    self._emit_exceeded_idletime_reset()
                    self._cycle_sleep_time = self.DEFAULT_CYCLE_SLEEP_TIME

                self.previous_idletime = idletime_ms

            for i in range(5):
                sleep(self._cycle_sleep_time / 5)

                if self._run_main_thread is False:
                    break
