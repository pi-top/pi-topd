# More Information

### Responsibilities

* Detecting whether the operating system is running on pi-top hardware, and if so initialising communication with the hub
* Communicating with pi-top hubs to detect hardware changes and notifications, such as battery status, hardware-initiated shutdown, etc.
* Detecting connection/disconnection of pi-top peripherals, such as a pi-topSPEAKER, and initialising peripheral such that whenever possible it will work in a 'plug & play' manner
* Opening a request-reponse messaging server and responding to requests from clients, e.g. responding to a request for the current screen brightness
* Opening a publishing messaging server and broadcasting to connected client when hardware changes take place
* Monitoring user input in order to dim the screen backlight when the user has been inactive for a configurable period (see next section)
* Shutting down the OS when required

#### Screen Blanking
In order to be able to dim the display after a period of inactivity, user input time is required - this is handled by `xprintidle`.

Currently, this implementation requires providing desktop information to the root user (which this application runs as). If this application is installed as a Debian package, this is taken care of for you.

To do this manually, write the following to `/etc/lightdm/lightdm.conf.d/pt-xhost-local-root.conf`:

    [Seat:*]
    session-setup-script=xhost +SI:localuser:root
