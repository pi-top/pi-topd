import logging
from os import path

from pitop.common.command_runner import run_command

logger = logging.getLogger(__name__)
_TIMEOUT = 10


class InterfaceManager:
    @property
    def i2c(self):
        logger.debug("Getting I2C state...")
        enabled = (
            run_command("raspi-config nonint get_i2c", timeout=_TIMEOUT).strip() == "0"
        )
        logger.debug(f"I2C state: {'enabled' if enabled else 'disabled'}")
        return enabled

    @i2c.setter
    def i2c(self, enabled):
        if enabled:
            if self.i2c:
                logger.warning("I2C is already enabled")
            else:
                logger.info("Enabling I2C...")
                run_command("raspi-config nonint do_i2c 0", timeout=_TIMEOUT)
        else:
            if self.i2c:
                logger.info("Disabling I2C...")
                run_command("raspi-config nonint do_i2c 1", timeout=_TIMEOUT)
            else:
                logger.warning("I2C is already disabled")

    @property
    def spi0(self):
        logger.debug("Getting SPI0 state...")
        enabled = (
            run_command("raspi-config nonint get_spi", timeout=_TIMEOUT).strip() == "0"
        )
        logger.debug(f"SPI0 state: {'enabled' if enabled else 'disabled'}")
        return enabled

    @spi0.setter
    def spi0(self, enabled):
        if enabled:
            if self.spi0:
                logger.warning("SPI0 is already enabled")
            else:
                logger.info("Enabling SPI0...")
                run_command("raspi-config nonint do_spi 0", timeout=_TIMEOUT)
        else:
            if self.spi0:
                logger.info("Disabling SPI0...")
                run_command("raspi-config nonint do_spi 1", timeout=_TIMEOUT)
            else:
                logger.warning("SPI0 is already disabled")

    @property
    def spi1(self):
        logger.debug("Getting SPI1 state...")
        enabled = path.exists("/dev/spidev1.0")
        logger.debug(f"SPI1 state: {'enabled' if enabled else 'disabled'}")
        return enabled

    @spi1.setter
    def spi1(self, enabled):
        if enabled:
            if self.spi1:
                logger.warning("SPI1 is already enabled")
            else:
                logger.info("Enabling SPI1...")
                run_command("dtoverlay spi1-1cs", timeout=_TIMEOUT)
        else:
            if self.spi1:
                logger.error("Unable to deactivate SPI1")
            else:
                logger.warning("SPI1 is already disabled")
