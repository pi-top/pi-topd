
# Discovers which peripheral libraries are installed, and uses those to
# detect, initialise, and communicate with the corresponding device


class PeripheralManager():

    def initialise(self, logger, callback_client):

        self._logger = logger
        self._callback_client = callback_client
