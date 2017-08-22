
# Messages sent to/from pt-device-manager clients


class Message:

    _message_names = {}

    # Requests
    REQ_TEST_PUB_EMITS                  = 100

    REQ_PING                            = 110
    REQ_GET_DEVICE_ID                   = 111
    REQ_GET_BRIGHTNESS                  = 112
    REQ_SET_BRIGHTNESS                  = 113
    REQ_INCREMENT_BRIGHTNESS            = 114
    REQ_DECREMENT_BRIGHTNESS            = 115
    REQ_BLANK_SCREEN                    = 116
    REQ_UNBLANK_SCREEN                  = 117

    _message_names[REQ_TEST_PUB_EMITS] = "REQ_TEST_PUB_EMITS"
    _message_names[REQ_PING] = "REQ_PING"
    _message_names[REQ_GET_DEVICE_ID] = "REQ_GET_DEVICE_ID"
    _message_names[REQ_GET_BRIGHTNESS] = "REQ_GET_BRIGHTNESS"
    _message_names[REQ_SET_BRIGHTNESS] = "REQ_SET_BRIGHTNESS"
    _message_names[REQ_INCREMENT_BRIGHTNESS] = "REQ_INCREMENT_BRIGHTNESS"
    _message_names[REQ_DECREMENT_BRIGHTNESS] = "REQ_DECREMENT_BRIGHTNESS"
    _message_names[REQ_BLANK_SCREEN] = "REQ_BLANK_SCREEN"
    _message_names[REQ_UNBLANK_SCREEN] = "REQ_UNBLANK_SCREEN"

    # Responses
    RSP_DONE_TEST_PUB_EMITS             = 200

    RSP_ERR_SERVER                      = 201
    RSP_ERR_MALFORMED                   = 202
    RSP_ERR_UNSUPPORTED                 = 203
    RSP_PING                            = 210
    RSP_GET_DEVICE_ID                   = 211
    RSP_GET_BRIGHTNESS                  = 212
    RSP_SET_BRIGHTNESS                  = 213
    RSP_INCREMENT_BRIGHTNESS            = 214
    RSP_DECREMENT_BRIGHTNESS            = 215
    RSP_BLANK_SCREEN                    = 216
    RSP_UNBLANK_SCREEN                  = 217

    _message_names[RSP_DONE_TEST_PUB_EMITS] = "RSP_DONE_TEST_PUB_EMITS"
    _message_names[RSP_ERR_SERVER] = "RSP_ERR_SERVER"
    _message_names[RSP_ERR_MALFORMED] = "RSP_ERR_MALFORMED"
    _message_names[RSP_ERR_UNSUPPORTED] = "RSP_ERR_UNSUPPORTED"
    _message_names[RSP_PING] = "RSP_PING"
    _message_names[RSP_GET_DEVICE_ID] = "RSP_GET_DEVICE_ID"
    _message_names[RSP_GET_BRIGHTNESS] = "RSP_GET_BRIGHTNESS"
    _message_names[RSP_SET_BRIGHTNESS] = "RSP_SET_BRIGHTNESS"
    _message_names[RSP_INCREMENT_BRIGHTNESS] = "RSP_INCREMENT_BRIGHTNESS"
    _message_names[RSP_DECREMENT_BRIGHTNESS] = "RSP_DECREMENT_BRIGHTNESS"
    _message_names[RSP_BLANK_SCREEN] = "RSP_BLANK_SCREEN"
    _message_names[RSP_UNBLANK_SCREEN] = "RSP_UNBLANK_SCREEN"

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

    _message_names[PUB_BRIGHTNESS_CHANGED] = "PUB_BRIGHTNESS_CHANGED"
    _message_names[PUB_PERIPHERAL_CONNECTED] = "PUB_PERIPHERAL_CONNECTED"
    _message_names[PUB_PERIPHERAL_DISCONNECTED] = "PUB_PERIPHERAL_DISCONNECTED"
    _message_names[PUB_SHUTDOWN_REQUESTED] = "PUB_SHUTDOWN_REQUESTED"
    _message_names[PUB_REBOOT_REQUIRED] = "PUB_REBOOT_REQUIRED"
    _message_names[PUB_BATTERY_CHARGING_STATE_CHANGED] = "PUB_BATTERY_CHARGING_STATE_CHANGED"
    _message_names[PUB_BATTERY_CAPACITY_CHANGED] = "PUB_BATTERY_CAPACITY_CHANGED"
    _message_names[PUB_BATTERY_TIME_REMAINING_CHANGED] = "PUB_BATTERY_TIME_REMAINING_CHANGED"
    _message_names[PUB_SCREEN_BLANKED] = "PUB_SCREEN_BLANKED"
    _message_names[PUB_SCREEN_UNBLANKED] = "PUB_SCREEN_UNBLANKED"
    _message_names[PUB_DEVICE_ID_CHANGED] = "PUB_DEVICE_ID_CHANGED"

    @classmethod
    def from_string(cls, message_string):

        new_object = cls()
        new_object._message_string = message_string
        new_object._parse()

        return new_object

    @classmethod
    def from_parts(cls, message_id, parameters):

        new_object = cls()
        new_object._message_id = message_id
        new_object._parameters = parameters

        return new_object

    def to_string(self):

        message_to_send = str(self._message_id)

        for message_param in self._parameters:
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

    def message_id_name(self):

        return self._message_names[self._message_id]

    def message_friendly_string(self):

        result = self.message_id_name()

        for param in self._parameters:
            result += " "
            result += str(param)

        return result

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
