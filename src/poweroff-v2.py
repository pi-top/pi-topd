#!/usr/bin/python3

# Script to send a poweroff command to the pi-top v2 hub. Typically this
# is launched by systemd responding to halt.target/poweroff.target, to
# ensure the hub shuts down after the raspberry pi

from ptcommon import i2c_device

PWR__SHUTDOWN_CTRL = 0xA0
PWR__SHUTDOWN_CTRL__MODE1 = 0x08

try:

    hub = i2c_device.I2CDevice("/dev/i2c-1", 0x10, None)
    hub.connect()

    # Get the current power control register
    shutdown_control = hub.read_unsigned_byte(PWR__SHUTDOWN_CTRL)

    # Set the shutdown mode to 1
    shutdown_control = shutdown_control | PWR__SHUTDOWN_CTRL__MODE1

    # Write back to the device
    hub.write_byte(PWR__SHUTDOWN_CTRL, shutdown_control)

except Exception as e:

    print("Error shutting down the hub: " + str(e))
