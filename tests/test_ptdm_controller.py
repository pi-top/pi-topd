from ptdm_controller import Controller
from pitop.core.common_ids import DeviceID
import sys
import unittest
from unittest.mock import patch, call, Mock

mock_systemd_daemon = Mock()
mock_common_ids = Mock()
sys.modules["systemd.daemon"] = mock_systemd_daemon
sys.modules["pitop.core.common_ids"] = mock_common_ids
sys.modules["time"].sleep = Mock()
sys.modules["pitop.core.logger"] = Mock()


class ControllerTestCase(unittest.TestCase):
    def setUp(self):

        # Mock objects and methods

        self.mock_publish_server = Mock()
        self.mock_power_manager = Mock()
        self.mock_hub_manager = Mock()
        self.mock_idle_monitor = Mock()
        self.mock_notification_manager = Mock()
        self.mock_peripheral_manager = Mock()
        self.mock_request_server = Mock()
        self.mock_config_manager = Mock()

        # Create the object under test

        self.controller = Controller(
            self.mock_publish_server,
            self.mock_power_manager,
            self.mock_hub_manager,
            self.mock_idle_monitor,
            self.mock_notification_manager,
            self.mock_peripheral_manager,
            self.mock_request_server,
            self.mock_config_manager,
        )

        self.controller._continue_running = False

    def tearDown(self):

        pass

    def test_controller_starts_publish_server(self):

        # Setup

        self.mock_publish_server.start_listening.return_value = True

        # Run

        self.assertTrue(self.controller.start())

        # Test

        self.mock_publish_server.start_listening.assert_called()

    def test_controller_dies_if_fails_to_start_publish_server(self):

        # Setup

        self.mock_publish_server.start_listening.return_value = False

        # Run

        self.assertFalse(self.controller.start())

    def test_controller_connects_to_hub_and_starts_hub_manager(self):

        # Setup

        self.mock_publish_server.start_listening.return_value = True
        self.mock_hub_manager.connect_to_hub.return_value = True

        # Run

        self.assertTrue(self.controller.start())

        # Test

        self.mock_hub_manager.connect_to_hub.assert_called()
        self.mock_hub_manager.start.assert_called()

    def test_controller_connects_to_hub_and_writes_host_device_to_file(self):

        # Setup
        self.mock_publish_server.start_listening.return_value = True
        self.mock_hub_manager.connect_to_hub.return_value = True
        self.mock_hub_manager.get_device_id.return_value = DeviceID.pi_top_4

        # Run

        self.assertTrue(self.controller.start())

        # Test

        self.mock_config_manager.write_device_id_to_file.assert_called_with(
            DeviceID.pi_top_4
        )

    def test_controller_does_not_connect_to_a_hub_and_writes_host_device_to_file(self):

        # Setup
        self.mock_publish_server.start_listening.return_value = True
        self.mock_hub_manager.connect_to_hub.return_value = True
        self.mock_hub_manager.get_device_id.return_value = DeviceID.unknown

        # Run

        assert self.controller.start() == False

        # Test

        self.mock_config_manager.write_device_id_to_file.assert_called_with(
            DeviceID.unknown
        )

    def test_controller_dies_if_fails_to_connect_to_hub(self):

        # Setup

        self.mock_publish_server.start_listening.return_value = True
        self.mock_hub_manager.connect_to_hub.return_value = False

        # Run

        self.assertFalse(self.controller.start())

        # Test

        self.mock_hub_manager.connect_to_hub.assert_called()
        self.mock_hub_manager.start.assert_not_called()

    def test_controller_waits_for_and_gets_device_id(self):

        # Setup

        self.mock_publish_server.start_listening.return_value = True
        self.mock_hub_manager.connect_to_hub.return_value = True

        # Run

        self.assertTrue(self.controller.start())

        # Test

        self.mock_hub_manager.wait_for_device_identification.assert_called()
        self.mock_hub_manager.get_device_id.assert_called()

    def test_controller_exits_if_device_unknown(self):

        # Setup

        self.mock_publish_server.start_listening.return_value = True
        self.mock_hub_manager.connect_to_hub.return_value = True
        self.mock_hub_manager.get_device_id.return_value = DeviceID.unknown

        # Run

        assert self.controller.start() == False

    def test_controller_device_id_passed_to_sub_systems(self):

        # Setup

        self.mock_publish_server.start_listening.return_value = True
        self.mock_hub_manager.connect_to_hub.return_value = True
        self.mock_hub_manager.get_device_id.return_value = DeviceID.pi_top_3

        # Run

        self.assertTrue(self.controller.start())

        # Test

        self.mock_peripheral_manager.initialise_device_id.assert_called_with(
            DeviceID.pi_top_3
        )
        self.mock_power_manager.set_device_id.assert_called_with(
            DeviceID.pi_top_3)

    def test_controller_starts_peripheral_manager(self):

        # Setup

        self.mock_publish_server.start_listening.return_value = True
        self.mock_hub_manager.connect_to_hub.return_value = True
        self.mock_peripheral_manager.start.return_value = True

        # Run

        self.assertTrue(self.controller.start())

        # Test

        self.mock_peripheral_manager.start.assert_called()

    def test_controller_dies_if_fails_to_start_peripheral_manager(self):

        # Setup

        self.mock_publish_server.start_listening.return_value = True
        self.mock_hub_manager.connect_to_hub.return_value = True
        self.mock_peripheral_manager.start.return_value = False

        # Run

        self.assertFalse(self.controller.start())

    def test_controller_starts_idle_monitor(self):

        # Setup

        self.mock_publish_server.start_listening.return_value = True
        self.mock_hub_manager.connect_to_hub.return_value = True
        self.mock_peripheral_manager.start.return_value = True

        # Run

        self.assertTrue(self.controller.start())

        # Test

        self.mock_idle_monitor.start.assert_called()

    def test_controller_starts_request_server_listening(self):

        # Setup

        self.mock_publish_server.start_listening.return_value = True
        self.mock_hub_manager.connect_to_hub.return_value = True
        self.mock_peripheral_manager.start.return_value = True
        self.mock_request_server.start.return_value = True

        # Run

        self.assertTrue(self.controller.start())

        # Test

        self.mock_request_server.start_listening.assert_called()

    def test_controller_dies_if_fails_to_start_request_server(self):

        # Setup

        self.mock_publish_server.start_listening.return_value = True
        self.mock_hub_manager.connect_to_hub.return_value = True
        self.mock_peripheral_manager.start.return_value = True
        self.mock_request_server.start_listening.return_value = False

        # Run

        self.assertFalse(self.controller.start())

    def test_controller_notifies_systemd_when_ready(self):

        # Setup

        self.mock_publish_server.start_listening.return_value = True
        self.mock_hub_manager.connect_to_hub.return_value = True
        self.mock_peripheral_manager.start.return_value = True
        self.mock_request_server.start_listening.return_value = True

        # Run

        self.assertTrue(self.controller.start())

        # Test

        mock_systemd_daemon.notify.assert_called_with("READY=1")


if __name__ == "__main__":
    unittest.main()
