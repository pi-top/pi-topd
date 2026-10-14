import importlib
import logging
import sys
from types import ModuleType, SimpleNamespace

import pytest

SPI1_OVERLAY = "dtoverlay=spi1-1cs"
SPI1_RUNTIME_COMMAND = "dtoverlay spi1-1cs"


class FakeSystem:
    """In-memory stand-in for the Pi: config.txt overlays, /dev/spidev1.0 and
    the commands that were run."""

    def __init__(self):
        self.config = set()
        self.config_writes = []
        self.config_error = None
        self.spi1_device = False
        self.runtime_load_creates_device = True
        self.device_appears_after_sleeps = None
        self.sleeps = 0
        self.commands = []

    def overlay_in_config(self, overlay):
        if self.config_error:
            raise self.config_error
        return overlay in self.config

    def add_overlay_to_config(self, overlay):
        self.config_writes.append(("add", overlay))
        self.config.add(overlay)

    def comment_overlay_in_config_txt(self, overlay):
        self.config_writes.append(("comment", overlay))
        self.config.discard(overlay)

    def run_command(self, command, timeout=None):
        self.commands.append(command)
        if command == SPI1_RUNTIME_COMMAND and self.runtime_load_creates_device:
            self.spi1_device = True
        return ""

    def sleep(self, _seconds):
        self.sleeps += 1
        if (
            self.device_appears_after_sleeps is not None
            and self.sleeps >= self.device_appears_after_sleeps
        ):
            self.spi1_device = True

    def exists(self, device):
        return self.spi1_device and device == "/dev/spidev1.0"


@pytest.fixture
def system(monkeypatch):
    """Imports InterfaceManager with pitop and sys_config replaced by fakes, so
    the tests don't need the pi-top SDK or a Raspberry Pi."""
    fake = FakeSystem()

    command_runner = ModuleType("pitop.common.command_runner")
    command_runner.run_command = fake.run_command
    sys_config = ModuleType("pitopd.sys_config")
    sys_config.overlay_in_config = fake.overlay_in_config
    sys_config.add_overlay_to_config = fake.add_overlay_to_config
    sys_config.comment_overlay_in_config_txt = fake.comment_overlay_in_config_txt

    monkeypatch.setitem(sys.modules, "pitop", ModuleType("pitop"))
    monkeypatch.setitem(sys.modules, "pitop.common", ModuleType("pitop.common"))
    monkeypatch.setitem(sys.modules, "pitop.common.command_runner", command_runner)
    monkeypatch.setitem(sys.modules, "pitopd.sys_config", sys_config)
    sys.modules.pop("pitopd.interface_manager", None)

    module = importlib.import_module("pitopd.interface_manager")
    monkeypatch.setattr(module, "path", SimpleNamespace(exists=fake.exists))
    monkeypatch.setattr(module, "sleep", fake.sleep)

    fake.interface_manager = module.InterfaceManager()
    yield fake

    sys.modules.pop("pitopd.interface_manager", None)


def test_enable_spi1_adds_overlay_to_config_and_loads_it_at_runtime(system):
    system.interface_manager.spi1 = True

    assert system.config_writes == [("add", SPI1_OVERLAY)]
    assert system.commands == [SPI1_RUNTIME_COMMAND]


def test_enable_spi1_does_not_reload_overlay_that_was_loaded_at_boot(system):
    system.config.add(SPI1_OVERLAY)
    system.device_appears_after_sleeps = 2

    system.interface_manager.spi1 = True

    assert system.commands == []
    assert system.config_writes == []


def test_enable_spi1_falls_back_to_runtime_load_if_boot_overlay_gives_no_device(
    system, caplog
):
    system.config.add(SPI1_OVERLAY)

    with caplog.at_level(logging.ERROR):
        system.interface_manager.spi1 = True

    assert system.commands == [SPI1_RUNTIME_COMMAND]
    assert caplog.records == []


def test_enable_spi1_when_already_enabled_still_persists_overlay(system):
    # e.g. pi-topd upgraded on a running system whose config.txt lacks the overlay
    system.spi1_device = True

    system.interface_manager.spi1 = True

    assert system.config_writes == [("add", SPI1_OVERLAY)]
    assert system.commands == []


def test_enable_spi1_logs_error_if_device_never_appears(system, caplog):
    system.runtime_load_creates_device = False

    with caplog.at_level(logging.ERROR):
        system.interface_manager.spi1 = True

    assert system.commands == [SPI1_RUNTIME_COMMAND]
    assert "did not appear" in caplog.text


def test_enable_spi1_still_loads_at_runtime_if_config_txt_cannot_be_read(
    system, caplog
):
    system.config_error = OSError("boot partition read-only")

    with caplog.at_level(logging.ERROR):
        system.interface_manager.spi1 = True

    assert system.commands == [SPI1_RUNTIME_COMMAND]
    assert "Failed to add SPI1 overlay to config.txt" in caplog.text


def test_disable_spi1_removes_overlay_from_config(system):
    system.config.add(SPI1_OVERLAY)

    system.interface_manager.spi1 = False

    assert system.config_writes == [("comment", SPI1_OVERLAY)]


def test_disable_spi1_does_not_touch_config_if_overlay_absent(system):
    system.interface_manager.spi1 = False

    assert system.config_writes == []
    assert system.commands == []


def test_disable_spi1_logs_error_if_config_txt_cannot_be_read(system, caplog):
    system.config_error = OSError("boot partition read-only")

    with caplog.at_level(logging.ERROR):
        system.interface_manager.spi1 = False

    assert "Failed to remove SPI1 overlay from config.txt" in caplog.text
