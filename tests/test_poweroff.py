import importlib
import sys
from enum import Enum
from types import ModuleType

import pytest

PWR__SHUTDOWN_CTRL = 0xA0
AC = 0x40
BUTT = 0x02


class DeviceID(Enum):
    pi_top = 0
    pi_top_ceed = 1
    pi_top_3 = 2
    pi_top_4 = 3


class FakeHub:
    def __init__(self, register):
        self.register = register
        self.writes = []

    def connect(self):
        pass

    def read_unsigned_byte(self, address):
        assert address == PWR__SHUTDOWN_CTRL
        return self.register

    def write_byte(self, address, value):
        assert address == PWR__SHUTDOWN_CTRL
        self.writes.append(value)


@pytest.fixture
def poweroff(monkeypatch):
    """Imports the real pitopd.poweroff with the SDK and spidev stubbed."""

    def stub(name, **attributes):
        module = ModuleType(name)
        for attribute, value in attributes.items():
            setattr(module, attribute, value)
        monkeypatch.setitem(sys.modules, name, module)

    stub("pitop")
    stub("pitop.common")
    stub("pitop.common.common_ids", DeviceID=DeviceID)
    stub("pitop.common.i2c_device", I2CDevice=None)
    stub("spidev", SpiDev=None)
    stub("pitopd.state")
    monkeypatch.delitem(sys.modules, "pitopd.poweroff", raising=False)
    return importlib.import_module("pitopd.poweroff")


def written(poweroff, monkeypatch, run, register, reboot_flag=False):
    hub = FakeHub(register)
    monkeypatch.setattr(poweroff, "I2CDevice", lambda *args: hub)
    monkeypatch.setattr(poweroff, "isfile", lambda path: reboot_flag)
    run()
    assert len(hub.writes) == 1
    return hub.writes[0]


@pytest.mark.parametrize(
    "register, reboot_flag, expected",
    [
        (0x00, False, 0x08),  # mode 1
        (0x00, True, 0x20),  # mode 4
        (AC | BUTT, False, AC | BUTT | 0x08),  # other bits kept
        (0x28, False, 0x08),  # stale mode 5 replaced, not OR'd into mode 5
        (0x10, True, 0x20),  # stale mode 2 replaced, not OR'd into mode 6
    ],
)
def test_pi_top_4_poweroff_sets_mode(
    poweroff, monkeypatch, register, reboot_flag, expected
):
    value = written(
        poweroff,
        monkeypatch,
        lambda: poweroff._do_poweroff(DeviceID.pi_top_4),
        register,
        reboot_flag,
    )
    assert value == expected


@pytest.mark.parametrize(
    "register, expected",
    [
        (0x00, 0x28),
        (AC, AC | 0x28),
        (0x10, 0x28),  # stale mode 2 replaced, not OR'd into mode 7
    ],
)
def test_pi_top_4_reboot_sets_mode_5(poweroff, monkeypatch, register, expected):
    assert written(poweroff, monkeypatch, poweroff._do_reboot, register) == expected


def test_pi_top_3_poweroff_unchanged(poweroff, monkeypatch):
    value = written(
        poweroff,
        monkeypatch,
        lambda: poweroff._do_poweroff(DeviceID.pi_top_3),
        0x10,
    )
    assert value == 0x18
