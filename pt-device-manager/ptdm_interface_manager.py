from pitopcommon.command_runner import run_command

from os import path


_TIMEOUT = 10


class InterfaceManager:
    @property
    def i2c(self):
        return run_command("raspi-config nonint get_i2c", timeout=_TIMEOUT).strip() == 0

    @i2c.setter
    def i2c(self, enabled):
        if enabled:
            if self.i2c:
                print("I2C is already enabled")
            else:
                run_command("raspi-config nonint do_i2c 0", timeout=_TIMEOUT)
        else:
            if self.i2c:
                run_command("raspi-config nonint do_i2c 1", timeout=_TIMEOUT)
            else:
                print("I2C is already disabled")

    @property
    def spi0(self):
        return run_command("raspi-config nonint get_spi", timeout=_TIMEOUT).strip() == 0

    @spi0.setter
    def spi0(self, enabled):
        if enabled:
            if self.spi0:
                print("SPI0 is already enabled")
            else:
                run_command("dtparam spi=on", timeout=_TIMEOUT)
        else:
            if self.spi0:
                run_command("dtparam spi=off", timeout=_TIMEOUT)
            else:
                print("SPI0 is already disabled")

    @property
    def spi1(self):
        return path.exists("/dev/spidev1.0")

    @spi1.setter
    def spi1(self, enabled):
        if enabled:
            if self.spi1:
                print("SPI1 is already enabled")
            else:
                run_command("dtoverlay spi1-1cs", timeout=_TIMEOUT)
        else:
            if self.spi1:
                print("Unable to deactivate SPI1")
            else:
                print("SPI1 is already disabled")
