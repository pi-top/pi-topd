
# Messages sent to/from pt-device-manager clients


class Message:

    # Requests

    REQ_PING                            = 110
    REQ_GET_HUB_INFO                    = 111
    REQ_GET_BRIGHTNESS                  = 112
    REQ_SET_BRIGHTNESS                  = 113

    # Responses

    RSP_ERR_SERVER                      = 201
    RSP_ERR_MALFORMED                   = 202
    RSP_ERR_UNSUPPORTED                 = 203
    RSP_PING                            = 210
    RSP_GET_HUB_INFO                    = 211
    RSP_GET_BRIGHTNESS                  = 212
    RSP_SET_BRIGHTNESS                  = 213

    # Broadcast/published messages

    PUB_BRIGHTNESS_CHANGED              = 300
    PUB_PERIPHERAL_CONNECTED            = 301
    PUB_PERIPHERAL_DISCONNECTED         = 302
    PUB_SHUTDOWN_REQUESTED              = 303
    PUB_REBOOT_REQUIRED                 = 304
    PUB_BATTERY_CHARGING_STATE_CHANGED  = 305
    PUB_BATTERY_CAPACITY_CHANGED        = 306
    PUB_BATTERY_TIME_REMAINING_CHANGED  = 307
    PUB_SCREEN_BLANKED                  = 308
    PUB_SCREEN_UNBLANKED                = 309
    PUB_DEVICE_ID_CHANGED               = 310

    def __init__(self, message_string):

        self._message_string = message_string
        self._parse()

    @classmethod
    def build_message_string(self, message_id, parameters=[]):

        message_to_send = str(message_id)

        for message_param in parameters:
            message_to_send += "|"
            message_to_send += str(message_param)

        return message_to_send

    def validate_parameters(self, expected_param_types):

        if (len(self._parameters) != len(expected_param_types)):
            msg = "Message did not have the correct number of parameters"
            msg += " (" + str(required_count) + ")"
            raise ValueError(msg)

        for i in range(len(self._parameters)):

            if (expected_param_types[i] == int):

                if (self._is_integer(self._parameters[i]) is False):
                    msg = "Expected integer parameter could not be parsed"
                    raise ValueError(msg)

            elif (expected_param_types[i] == float):

                if (_is_float(self._parameters[i]) is False):
                    msg = "Expected float parameter could not be parsed"
                    raise ValueError(msg)

    def message_id(self):
        return self._message_id

    def parameters(self):
        return self._parameters

    def _parse(self):
        message_parts = self._message_string.split("|")

        if (len(message_parts) < 1):

            raise ValueError("Message did not have an id")

        if (self._is_integer(message_parts[0]) is False):

            raise ValueError("Message id was not an integer")

        self._message_id = int(message_parts[0])
        self._parameters = message_parts[1:]

    def _is_integer(self, string):
        try:
            int(string)
            return True

        except:
            return False

    def _is_float(self, string):
        try:
            float(string)
            return True

        except:
            return False
