import logging
from os import devnull
from subprocess import CalledProcessError, check_output
from threading import Thread
from time import sleep

from . import state

logger = logging.getLogger(__name__)


class IdleMonitor:

    DEFAULT_CYCLE_SLEEP_TIME = 5
    SENSITIVE_CYCLE_SLEEP_TIME = 0.2

    def __init__(self):
        self._callback_client = None
        self.previous_idletime = 0
        self._main_thread = None
        self._run_main_thread = False
        self._cycle_sleep_time = self.DEFAULT_CYCLE_SLEEP_TIME

    def initialise(self, callback_client):
        self._callback_client = callback_client

    def start(self):
        logger.debug("Starting idle time monitor...")
        if self._main_thread is None:
            self._main_thread = Thread(target=self._main_thread_loop)

        self._run_main_thread = True
        self._main_thread.start()

    def stop(self):
        logger.debug("Stopping idle time monitor...")
        self._run_main_thread = False
        if self._main_thread is not None:
            self._main_thread.join()
        logger.debug("Stopped idle time monitor.")

    def get_configured_timeout(self):
        return int(state.get("display", "timeout", fallback=str(300)))

    def set_configured_timeout(self, timeout: int):
        state.set("display", "timeout", str(timeout))

    # Internal methods
    def _emit_idletime_threshold_exceeded(self):
        if self._callback_client is not None:
            logger.info("Idletime threshold exceeded")
            self._callback_client.on_idletime_threshold_exceeded()

    def _emit_exceeded_idletime_reset(self):
        if self._callback_client is not None:
            logger.info("Idletime reset")
            self._callback_client.on_exceeded_idletime_reset()

    def _main_thread_loop(self):
        startup_wait_counter = 0
        startup_wait_time = 15

        logger.info(
            f"Waiting {str(startup_wait_time)} seconds before starting main idletime check thread..."
        )
        while self._run_main_thread and startup_wait_counter < startup_wait_time:
            startup_wait_counter += 1
            sleep(1)

        logger.info("Starting main idletime check thread...")
        while self._run_main_thread:
            FNULL = open(devnull, "w")

            try:
                xprintidle_resp = check_output(["xprintidle"], stderr=FNULL)
            except CalledProcessError:
                logger.warning(
                    "Unable to call xprintidle - have non-network local"
                    "connections been added to X server access control list?"
                )
                break

            xprintidle_resp_str = xprintidle_resp.decode("utf-8")

            try:
                idletime_ms = int(xprintidle_resp_str)
            except ValueError:
                logger.warning("Unable to convert xprintidle response to integer")
                break

            idle_timeout_s = self.get_configured_timeout()

            timeout_expired = idletime_ms > (idle_timeout_s * 1000)
            idletime_reset = idletime_ms < self.previous_idletime
            logger.debug(f"MS since idle: \t{str(idletime_ms)}")
            logger.debug(f"Timeout Expired?:\t{str(timeout_expired)}")
            logger.debug(f"Idletime Expired?:\t{str(idletime_reset)}")

            if idle_timeout_s > 0:
                timeout_already_expired = self.previous_idletime > idle_timeout_s * 1000

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
