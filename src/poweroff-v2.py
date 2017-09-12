#!/usr/bin/python3

# Script to send a poweroff command to the pi-top v2 hub. Typically this
# is launched by systemd responding to halt.target/poweroff.target, to
# ensure the hub shuts down after the raspberry pi

from pthub2 import pthub2_i2c_device

PWR__SHUTDOWN_CTRL = 0xA0
PWR__M3_TIMEOUT = 0xAE
PWR__SHUTDOWN_CTRL__MODE1 = 0x08
PWR__SHUTDOWN_CTRL__MODE2 = 0x16

try:

    i2c_device = pthub2_i2c_device.I2CDevice("/dev/i2c-1", 0x10, None)
    i2c_device.connect()

    # Set the timeout on the mode 3 shutdown
    i2c_device.write_word(PWR__M3_TIMEOUT, 15)

    # Get the current power control register
    shutdown_control = i2c_device.read_unsigned_byte(PWR__SHUTDOWN_CTRL)

    # Set the shutdown mode to 3
    shutdown_control = shutdown_control | PWR__SHUTDOWN_CTRL__MODE1
    shutdown_control = shutdown_control | PWR__SHUTDOWN_CTRL__MODE2

    # Write back to the device
    i2c_device.write_byte(PWR__SHUTDOWN_CTRL, shutdown_control)

except Exception as e:

    print("Error shutting down the hub: " + str(e))
