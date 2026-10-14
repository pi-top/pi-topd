import logging
from os import path
from time import sleep

from pitop.common.command_runner import run_command

from .sys_config import (
    add_overlay_to_config,
    comment_overlay_in_config_txt,
    overlay_in_config,
)

logger = logging.getLogger(__name__)
_TIMEOUT = 10

_SPI1_OVERLAY = "dtoverlay=spi1-1cs"
_SPI1_DEVICE = "/dev/spidev1.0"
_SPI1_WAIT_TIMEOUT = 5
_SPI1_WAIT_INTERVAL = 0.5


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
        enabled = path.exists(_SPI1_DEVICE)
        logger.debug(f"SPI1 state: {'enabled' if enabled else 'disabled'}")
        return enabled

    @spi1.setter
    def spi1(self, enabled):
        if enabled:
            # Also load the overlay from config.txt, so that the firmware applies it
            # before the kernel starts. On some kernels (seen on 6.12.109) loading it
            # at runtime leaves the SPI1 controller in deferred probe, so
            # /dev/spidev1.0 never appears and the OLED stays blank.
            loaded_at_boot = self._ensure_spi1_overlay_in_config()

            if self.spi1:
                logger.warning("SPI1 is already enabled")
                return

            # The device node can still be appearing if the firmware loaded the overlay
            if loaded_at_boot and self._wait_for_spi1():
                return

            logger.info("Enabling SPI1...")
            run_command("dtoverlay spi1-1cs", timeout=_TIMEOUT)
            if not self._wait_for_spi1():
                logger.error(
                    f"SPI1 device {_SPI1_DEVICE} did not appear after loading the "
                    "overlay; a reboot may be required"
                )
        else:
            # Don't leave SPI1 claiming its pins at every boot once the OLED has
            # moved to SPI0
            self._remove_spi1_overlay_from_config()

            if self.spi1:
                logger.error(
                    "Unable to deactivate SPI1 at runtime; it will be disabled "
                    "after the next reboot"
                )
            else:
                logger.warning("SPI1 is already disabled")

    def _wait_for_spi1(self):
        for _ in range(int(_SPI1_WAIT_TIMEOUT / _SPI1_WAIT_INTERVAL)):
            if path.exists(_SPI1_DEVICE):
                return True
            sleep(_SPI1_WAIT_INTERVAL)
        return path.exists(_SPI1_DEVICE)

    def _ensure_spi1_overlay_in_config(self):
        """Returns True if the overlay was already in config.txt (i.e. it was
        loaded at boot), False if it was missing or config.txt couldn't be
        read/updated."""
        try:
            if overlay_in_config(_SPI1_OVERLAY):
                return True
            logger.info("Adding SPI1 overlay to config.txt so it is loaded at boot")
            add_overlay_to_config(_SPI1_OVERLAY)
        except Exception as e:
            logger.error(f"Failed to add SPI1 overlay to config.txt: {e}")
        return False

    def _remove_spi1_overlay_from_config(self):
        try:
            # Only rewrite config.txt if there is something to change
            if overlay_in_config(_SPI1_OVERLAY):
                logger.info("Removing SPI1 overlay from config.txt")
                comment_overlay_in_config_txt(_SPI1_OVERLAY)
        except Exception as e:
            logger.error(f"Failed to remove SPI1 overlay from config.txt: {e}")
