import idletime
import time
import threading


class IdleMonitor(self):
    def initialise(self, logger, callback_client, timeout_ms=300000):
        self.previous_idletime = 0
        self._logger = logger
        self._callback_client = callback_client
        self._main_thread = None
        self._run_main_thread = False
        set_idle_timeout_ms(timeout_ms)

    def set_idle_timeout_ms(self, timeout_ms):
        self.idle_timeout_ms = timeout_ms
        timeout_s = float(self.idle_timeout_ms / 1000)
        self._cycle_sleep_time = min(5, float(timeout_s / 10))

    def start(self):
        if self._main_thread is None:
            self._main_thread = threading.Thread(target=self._main_thread_loop)

        self._run_main_thread = True
        self._main_thread.start()

    def stop(self):
        self._run_main_thread = False
        self._main_thread.join()

    def emit_idletime_threshold_exceeded(self):
        if (self._callback_client is not None):
            self._callback_client._on_idletime_threshold_exceeded()

    def emit_exceeded_idletime_reset(self):
        if (self._callback_client is not None):
            self._callback_client._on_exceeded_idletime_reset()

    def _main_thread_loop(self):
        while self._run_main_thread:
            time_since_idle = idletime.get_idle_time()

            timeout_expired = (time_since_idle > self.idle_timeout_ms)
            idletime_reset = (time_since_idle < self.previous_idletime)

            timeout_already_expired = (self.previous_idletime > self.idle_timeout_ms)

            if timeout_expired and not timeout_already_expired:
                emit_idletime_threshold_exceeded()
            elif idletime_reset and timeout_already_expired:
                emit_exceeded_idletime_reset()

            self.previous_idletime = time_since_idle
            sleep(_cycle_sleep_time)
