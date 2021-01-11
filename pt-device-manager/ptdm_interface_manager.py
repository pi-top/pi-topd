from pitopcommon.logger import PTLogger
from pitopcommon.command_runner import run_command

from os import path


_TIMEOUT = 10


class InterfaceManager:
    @property
    def i2c(self):
        PTLogger.debug("Getting I2C state...")
        enabled = run_command("raspi-config nonint get_i2c",
                              timeout=_TIMEOUT).strip() == "0"
        PTLogger.debug(f"I2C state: {'enabled' if enabled else 'disabled'}")
        return enabled

    @i2c.setter
    def i2c(self, enabled):
        if enabled:
            if self.i2c:
                PTLogger.warning("I2C is already enabled")
            else:
                PTLogger.info("Enabling I2C...")
                run_command("raspi-config nonint do_i2c 0", timeout=_TIMEOUT)
        else:
            if self.i2c:
                PTLogger.info("Disabling I2C...")
                run_command("raspi-config nonint do_i2c 1", timeout=_TIMEOUT)
            else:
                PTLogger.warning("I2C is already disabled")

    @property
    def spi0(self):
        PTLogger.debug("Getting SPI0 state...")
        enabled = run_command("raspi-config nonint get_spi",
                              timeout=_TIMEOUT).strip() == "0"
        PTLogger.debug(f"SPI0 state: {'enabled' if enabled else 'disabled'}")
        return enabled

    @spi0.setter
    def spi0(self, enabled):
        if enabled:
            if self.spi0:
                PTLogger.warning("SPI0 is already enabled")
            else:
                PTLogger.info("Enabling SPI0...")
                run_command("raspi-config nonint do_spi 0", timeout=_TIMEOUT)
        else:
            if self.spi0:
                PTLogger.info("Disabling SPI0...")
                run_command("raspi-config nonint do_spi 1", timeout=_TIMEOUT)
            else:
                PTLogger.warning("SPI0 is already disabled")

    @property
    def spi1(self):
        PTLogger.debug("Getting SPI1 state...")
        enabled = path.exists("/dev/spidev1.0")
        PTLogger.debug(f"SPI1 state: {'enabled' if enabled else 'disabled'}")
        return

    @spi1.setter
    def spi1(self, enabled):
        if enabled:
            if self.spi1:
                PTLogger.warning("SPI1 is already enabled")
            else:
                PTLogger.info("Enabling SPI1...")
                run_command("dtoverlay spi1-1cs", timeout=_TIMEOUT)
        else:
            if self.spi1:
                PTLogger.error("Unable to deactivate SPI1")
            else:
                PTLogger.warning("SPI1 is already disabled")
