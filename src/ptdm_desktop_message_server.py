# Zenity stuff - port from pt-periph

#     Build zenity message service
#         MEDIUM
#         Migrate components from pt-peripheral-daemon
#         pt-device-manager-x?
#             Separate python zmq receiver process starting with systemd
#             Needs to subscribe to the pt-device-manager publish server, and respond to the reboot required message
#                 Example python code for subscribing in pt-device-manager-test