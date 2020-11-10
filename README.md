# pi-top Device Management

Python-based daemon for detecting, configuring and communicating with pi-top hardware/peripherals

## Table of Contents
* [What is in this repository?](#repo-contents)
* [Controlling the device manager](#control)
* [Logging](#logging)
* [Support](#support)
  * [Links](#support-links)
  * [Troubleshooting](#support-troubleshooting)

## <a name="repo-contents"></a> What is in this repository?

### How do I install pi-top hardware support?
The code in this repository forms the basis of the `pt-device-manager` software package, available for install on both pi-topOS and Raspbian. On the latest versions of pi-topOS, this package is pre-installed. On other platforms such as Raspbian, it is **NOT** recommended to install this package directly.

![Dependency tree for pi-top device software](
https://static.pi-top.com/images/pt-devices-debtree.png "Dependency tree for pi-top device software")

As demonstrated in the software tree above, `pt-devices` installs all of the relevant software for full pi-top device support, and is therefore the best solution for ensuring full pi-top hardware support:

<pre style="background-color: #002b36; color: #FFFFFF;">
sudo apt install pt-devices
</pre>

However, this design also allows for specific hardware requirements to only install what is needed. For example, to add pi-topHUB and pi-topSPEAKER support:

<pre style="background-color: #002b36; color: #FFFFFF;">
sudo apt install pt-hub pt-speaker
</pre>

As both the packages `pt-hub` and `pt-pulse` have dependencies on the pt-device-manager, the `pt-device-manager` package will also be installed and enabled. It is not recommended to install any of the Python 3 libraries directly if you require plug-and-play functionality.

### Summary
`pt-device-manager` is a Python 3 program that when installed and run on a pi-top device enables detection, configuration and management of pi-top hardware. This includes hubs (e.g. pi-top or pi-topCEED) as well as peripherals (pi-topPULSE, pi-topSPEAKER). The actual work of communicating with each hardware device is handled by software equivalent to 'device drivers' in separate repositories. However the pt-device-manager takes care of loading and initialising these drivers in a pattern akin to a _plugin_ architecture.

The responsibilities of the device manager include:

* Detecting whether the operating system is running on pi-top hardware, and if so initialising communication with the hub.
* Communicating with pi-top hubs to detect hardware changes and notifications, such as battery status, hardware-initiated shutdown, etc.
* Detecting connection/disconnection of pi-top peripherals, such as a pi-topSPEAKER, and initialising peripheral such that whenever possible it will work in a 'plug & play' manner.
* Opening a request-reponse messaging server and responding to requests from clients, e.g. responding to a request for the current screen brightness.
* Opening a publishing messaging server and broadcasting to connected client when hardware changes take place.
* Monitoring user input in order to dim the screen backlight when the user has been inactive for a configurable period.
* Shutting down the OS when required.

#### Extra required configuration
##### Dependencies - pt-device-manager
* python3-pt-common
  * Common class of Python operations (see this repo)
* python3-pip
  * Used to install `pyserial` (see [config](config) directory), which is not available to install using `apt-get`.
* python3-systemd
  * Used to write to the journal
* libzmq3-dev, python3-zmq
  * Used to broadcast messages to OS about device changes
* wiringpi
  * Used by poweroff-v1
* xprintidle, x11-xserver-utils, lightdm
  * Used for user idle time. Requires additional configuration (see below)

##### Recommends - pt-device-manager
* pt-notifications
  * Used, if available, for providing GUI-based instructions/information to the user, particularly to notify if a system reconfiguration is required

* python3-pt-pulse, python3-pt-speaker, python3-pt-hub-v1, python3-pt-hub-v2, python3-pt-proto-plus
  * Modules that the device manager will use if the device is detected to ensure that it is configured correctly

##### Dependencies - python3-pt-common
* raspi-config
  * Used to determine if I2C is enabled, so that devices and peripherals can be detected
* python3-systemd
  * Used to write to the syslog as a system process
* i2c-tools
  * Used to handle I2C interaction
* alsa-utils
  * Used to configure sound settings

##### User Input
User input for dimming the screen backlight when the user has been inactive for a configurable period is monitored using `xprintidle`.
`xprintidle` requires extra configuration to work with the root user with admin privileges. This is needed in this case because the device manager needs to run as the root user:

    /usr/bin/xhost local:root

To set this up yourself, run [xhost-setup](config/xhost-setup).

If you would like to do this manually, write the following to `/etc/lightdm/lightdm.conf.d/pt-xhost-local-root.conf`:

    [Seat:*]
    session-setup-script=xhost +SI:localuser:root

NOTE: `pt-device-manager` does this automatically for you during the installation process.

#### Supported device drivers and repositories

* **[pi-topHUB v1](https://github.com/pi-top/pi-topHUB-v1)** - For the original pi-top and pi-topCEED
* **[pi-topHUB v2](https://github.com/pi-top/pi-topHUB-v2)** - For the new pi-top
* **[pi-topPULSE](https://github.com/pi-top/pi-topPULSE)**
* **[pi-topSPEAKER](https://github.com/pi-top/pi-topSPEAKER)**
* **[pi-topPROTO+](https://github.com/pi-top/pi-topPROTO-plus)**

The following is a summary of relevant device details:

| Device                     | I2C Address | SPI Bus
| -------------------------- |:-----------:|:-----------:|
| pi-topHUB v1 (pi-top)      |     0x0b    |      1      |
| pi-topHUB v1 (pi-topCEED)  |      -      |      1      |
| pi-topHUB v2               |     0x10    |      -      |

| Peripheral               | I2C Address |
| ------------------------ |:-----------:|
| pi-topPROTO+             |     0x2a    |
| pi-topPULSE              |     0x24    |
| pi-topSPEAKER v1 (Left)  |     0x71    |
| pi-topSPEAKER v1 (Right) |     0x72    |
| pi-topSPEAKER v1 (Mono)  |     0x73    |
| pi-topSPEAKER v2         |     0x43    |


### Contents

#### Directory: `pt-device-manager`
##### pt-device-manager
This Python script is the brain of the pi-top device management on pi-topOS. See [How it works](#how-it-works) for more information.

##### ptdm_*
These Python modules are used by pt-device-manager.


#### Directory: `library/ptcommon`
##### All files
These files are shared by multiple components in pi-top device management. `python3-pt-common` installs these files to `/usr/lib/python3/dist-packages/`, where they can be imported and used by the components that require them.

##### ptdm_*
These Python modules are used by pt-device-manager.

#### Directory: `tools`
##### pt-brightness, pt-battery
These Python scripts are pt-device-manager messaging clients. They send messages to the device management service to adjust the screen settings or query the battery status on a pi-top device.

##### pt-i2s
Used by pt-device-manager to switch I2S on/off on the Raspberry Pi, specifically when targeting pi-topSPEAKER/pi-topPULSE. This is **only** used in conjunction with pi-topHUB v1, as I2S is handled automatically on pi-topHUB v2. To configure for I2S, a custom `asound.conf` file is used to enable mixing multiple audio sources. As well as this, some settings in `/boot/config.txt` are altered:

* `dtoverlay=hifiberry-dac` - enables I2S audio on subsequent boots
* `#dtparam=audio=on` - disables default sound driver
* `dtoverlay=i2s-mmap` - allows multiple audio sources to be mixed together

Disabling I2S reverses these changes.

#### Directory: `assets`
##### hifiberry-alsactl.restore
This file exposes a soundcard device configuration to the operating system, enabling volume control. It is used by `pt-device-manager` when it detects that I2S has been enabled via the daemon for the first time, whereby it reboots to enable. This operation is only required once, so a 'breadcrumb' file is created to indicate that this has been completed. This is **only** used in conjunction with pi-topHUB v1, as I2S is handled automatically on pi-topHUB v2.
**NOTE: this will only work if the default audio driver is disabled (this is handled automatically with 'pt-i2s'**

#### Directory: `poweroff`
##### poweroff-v1(.c), poweroff-v2
These programs (written in C and Python respectively) are used to send a message directly to the relevant pi-topHUB to trigger a full system hardware shutdown.
##### poweroff-v{1,2}.service
These are systemd services for the poweroff programs, which ensure that they are always run when the OS is shutting down.
These are typically put in `/lib/system/systemd/`, and enabled by running `sudo systemctl enable poweroff-v1.service` and `sudo systemctl enable poweroff-v1.service` in the terminal.
These services require the `poweroff-v1` and `poweroff-v2` files to be executable and put in `/usr/lib/pt-device-manager`, although this can be easily changed as desired.

#### Directory: `tests`
##### pt-device-manager-req-test
This Python script tests that the device manager is able to respond to requests for information such as the getting current device and brightness level as well as pinging, setting brightness and blanking/unblanking the screen.

##### pt-device-manager-resp-test
This Python script tests that the device manager is able to emit all of its publishing events, that reflect a system state change, such as battery level, brightness, lid opened/closed and peripheral connection state.

## <a name="control"></a> Controlling the device manager

pt-device-manager is intended to be a systemd service which starts with the OS and stops on shutdown. However for diagnostic or debugging purposes it can be useful to start and stop it, or to run it standalone.

Checking the current status of the device manager (with example output):

<pre style="background-color: #002b36; color: #FFFFFF;">
sudo systemctl status pt-device-manager

<span style="color:#E0E0E0"><span style="color:#859900">●</span> pt-device-manager.service - pi-top device auto-detection and configuration daemon
     Loaded: loaded (/lib/systemd/system/pt-device-manager.service; enabled)
     Active: <span style="color:#859900">active (running)</span> since Tue 2017-10-17 15:55:43 UTC; 1s ago
 Main PID: 15974 (pt-device-manag)
     CGroup: /system.slice/pt-device-manager.service
                     └─15974 /usr/bin/python3 /usr/lib/pt-device-manager/pt-device-manager</span>
</pre>

Starting/stopping the device manager:

<pre style="background-color: #002b36; color: #FFFFFF;">
sudo systemctl start pt-device-manager
sudo systemctl stop pt-device-manager
</pre>

Stopping and disabling the service, and then running standalone:

<pre style="background-color: #002b36; color: #FFFFFF;">
sudo systemctl stop pt-device-manager
sudo systemctl disable pt-device-manager
cd /usr/lib/pt-device-manager
sudo ./pt-device-manager --no-journal --log-level 20
</pre>

**Note** when running the device manager standalone, the above two command line parameters are useful:

* `--no-journal` forces the device manager to log to stdout rather than the systemd journal
* `--log-level X` sets the logging levels where 10 is the lowest (debug) and 40 is the highest (serious errors only)


## <a name="logging"></a> Logging

As the pt-device-manager runs as a systemd service, it logs to the system journal. This can be viewed using commands such as:

<pre style="background-color: #002b36; color: #FFFFFF;">
sudo journalctl -u pt-device-manager
sudo journalctl -u pt-device-manager --no-pager
sudo journalctl -u pt-device-manager -b
</pre>

## <a name="support"></a> Support
### <a name="support-links"></a> Links
* [pi-topHUB v1](https://github.com/pi-top/pi-topHUB-v1)
* [pi-topHUB v2](https://github.com/pi-top/pi-topHUB-v2)
* [pi-topPULSE](https://github.com/pi-top/pi-topPULSE)
* [pi-topSPEAKER](https://github.com/pi-top/pi-topSPEAKER)
* [pi-topPROTO+](https://github.com/pi-top/pi-topPROTO-plus)
* <a name="support-pinout"></a>[pi-top Peripherals' GPIO Pinouts](https://pinout.xyz/boards#manufacturer=pi-top)
* [Support](https://support.pi-top.com/)

### <a name="support-troubleshooting"></a> Troubleshooting
#### Why is my pi-top device/peripheral not working?

* Please see the corresponding repository for your device. Repositories are listed at the top of this README.

#### Why is my pi-top v1 reporting itself to be a pi-topCEED?

* See the [pi-topHUB v1 troubleshooting section](https://github.com/pi-top/pi-topHUB-v1#support-troubleshooting) for information relating to this issue.
