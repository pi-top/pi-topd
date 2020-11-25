from ptdm_config_manager import ConfigManager
import sys
import unittest
from unittest.mock import patch, Mock, mock_open, MagicMock

mock_common_ids = MagicMock()
sys.modules["pitopcommon.common_ids"] = mock_common_ids
sys.modules["pitopcommon.logger"] = Mock()


class ConfigManagerTestCase(unittest.TestCase):
    def setUp(self):

        # Create the object to test

        self.mock_config_editor = Mock()
        self.config_editor = ConfigManager()
        self.config_editor._config_editor = self.mock_config_editor

    def test_get_last_identified_device_id_pi_top_4(self):

        # Setup

        self.mock_open = mock_open()
        self.mock_open_method = patch("builtins.open", self.mock_open)
        self.mock_open_method.start()

        mock_common_ids.DeviceID.__getitem__.side_effect = [
            mock_common_ids.DeviceID.pi_top_4]

        # Run

        device_id = self.config_editor.get_last_identified_device_id()

        # Test

        self.assertEqual(device_id, mock_common_ids.DeviceID.pi_top_4)

        # Cleanup

        self.mock_open_method.stop()

    def test_get_last_identified_device_id_unknown(self):

        # Setup

        self.mock_open = mock_open()
        self.mock_open_method = patch("builtins.open", self.mock_open)
        self.mock_open_method.start()

        mock_common_ids.DeviceID.__getitem__.side_effect = [
            mock_common_ids.DeviceID.unknown]

        # Run

        device_id = self.config_editor.get_last_identified_device_id()

        # Test

        self.assertEqual(device_id, mock_common_ids.DeviceID.unknown)

        # Cleanup

        self.mock_open_method.stop()

    def test_get_last_identified_device_id_returns_unknown_if_error_raised(self):

        # Setup

        self.mock_open = mock_open()
        self.mock_open_method = patch("builtins.open", self.mock_open)
        self.mock_open_method.start()

        self.mock_open.side_effect = IOError("File not there")

        # Run

        device_id = self.config_editor.get_last_identified_device_id()

        # Test

        self.assertEqual(device_id, mock_common_ids.DeviceID.unknown)

        # Cleanup

        self.mock_open_method.stop()


if __name__ == "__main__":
    unittest.main()
