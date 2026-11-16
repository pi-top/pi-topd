import importlib
import sys
from types import ModuleType

import pytest

SPI1_OVERLAY = "dtoverlay=spi1-1cs"


@pytest.fixture
def sys_config(monkeypatch, tmp_path):
    """Imports the real pitopd.sys_config with the pi-top SDK replaced by
    stubs, so the tests don't need the SDK.

    The boot partition is a temporary directory.
    """

    def stub(name, **attributes):
        module = ModuleType(name)
        for attribute, value in attributes.items():
            setattr(module, attribute, value)
        monkeypatch.setitem(sys.modules, name, module)

    stub("pitop")
    stub("pitop.common")
    stub("pitop.common.command_runner", run_command=lambda *args, **kwargs: "")
    stub("pitop.common.current_session_info", get_current_user=lambda: "pi")
    stub(
        "pitop.common.file_ops",
        create_temp_file=lambda *args, **kwargs: None,
        sed_inplace=lambda *args, **kwargs: None,
    )
    stub(
        "pitop.common.formatting",
        get_uncommented_line=lambda *args, **kwargs: "",
        is_line_commented=lambda *args, **kwargs: False,
    )
    stub("pitop.common.pt_os", get_boot_partition_path=lambda: str(tmp_path))
    sys.modules.pop("pitopd.sys_config", None)

    module = importlib.import_module("pitopd.sys_config")
    yield module

    sys.modules.pop("pitopd.sys_config", None)


@pytest.fixture
def write_config(tmp_path):
    def _write_config(*lines):
        config = tmp_path / "config.txt"
        config.write_text("\n".join(lines) + "\n")
        return config

    return _write_config


def test_overlay_in_config_true_if_overlay_is_enabled(sys_config, write_config):
    write_config("dtparam=i2c_arm=on", SPI1_OVERLAY, "gpu_mem=128")

    assert sys_config.overlay_in_config(SPI1_OVERLAY) is True


def test_overlay_in_config_false_if_overlay_is_absent(sys_config, write_config):
    write_config("dtparam=i2c_arm=on", "gpu_mem=128")

    assert sys_config.overlay_in_config(SPI1_OVERLAY) is False


def test_overlay_in_config_false_if_overlay_is_commented_out(sys_config, write_config):
    write_config("dtparam=i2c_arm=on", f"#{SPI1_OVERLAY}", "gpu_mem=128")

    assert sys_config.overlay_in_config(SPI1_OVERLAY) is False


def test_overlay_in_config_false_if_overlay_is_only_in_another_section(
    sys_config, write_config
):
    write_config("[pi4]", SPI1_OVERLAY, "[all]", "gpu_mem=128")

    assert sys_config.overlay_in_config(SPI1_OVERLAY) is False


def test_overlay_in_config_true_if_overlay_has_parameters(sys_config, write_config):
    write_config("[all]", f"{SPI1_OVERLAY},cs0_pin=18")

    assert sys_config.overlay_in_config(SPI1_OVERLAY) is True


def test_overlay_can_be_added_and_commented_out_again(sys_config, write_config):
    config = write_config("dtparam=i2c_arm=on", "[all]", "gpu_mem=128")

    sys_config.add_overlay_to_config(SPI1_OVERLAY)
    assert sys_config.overlay_in_config(SPI1_OVERLAY) is True
    assert SPI1_OVERLAY in config.read_text().splitlines()

    sys_config.comment_overlay_in_config_txt(SPI1_OVERLAY)
    assert sys_config.overlay_in_config(SPI1_OVERLAY) is False
    assert f"#{SPI1_OVERLAY}" in config.read_text().splitlines()


@pytest.fixture
def hdmi_card_name(sys_config, monkeypatch):
    def _hdmi_card_name(card_names, force_hotplug=()):
        monkeypatch.setattr(
            sys_config._SystemCalls,
            "_get_card_names",
            staticmethod(
                lambda user=None: [
                    {"name": name, "number": str(i)}
                    for i, name in enumerate(card_names)
                ]
            ),
        )
        monkeypatch.setattr(
            sys_config,
            "run_command",
            lambda cmd, **kwargs: (
                "1"
                if any(f"hdmi_force_hotplug:{p} " in cmd for p in force_hotplug)
                else ""
            ),
        )
        return sys_config._SystemCalls._get_config_specific_alsa_card_name(
            sys_config.AudioDevice.HDMI
        )

    return _hdmi_card_name


def test_hdmi_kms_pi4_uses_hdmi0_by_default(hdmi_card_name):
    names = ["bcm2835 Headphones", "vc4-hdmi-0", "vc4-hdmi-1"]
    assert hdmi_card_name(names) == "vc4-hdmi-0"


def test_hdmi_kms_pi4_uses_hdmi1_when_it_is_forced(hdmi_card_name):
    names = ["bcm2835 Headphones", "vc4-hdmi-0", "vc4-hdmi-1"]
    assert hdmi_card_name(names, force_hotplug=[1]) == "vc4-hdmi-1"


def test_hdmi_kms_pi4_falls_back_to_the_port_with_a_sink(hdmi_card_name):
    assert hdmi_card_name(["bcm2835 Headphones", "vc4-hdmi-1"]) == "vc4-hdmi-1"


def test_hdmi_single_port_kms(hdmi_card_name):
    assert hdmi_card_name(["bcm2835 Headphones", "vc4-hdmi"]) == "vc4-hdmi"


def test_hdmi_fkms_two_ports_unchanged(hdmi_card_name):
    names = ["bcm2835 HDMI 1", "bcm2835 HDMI 2"]
    assert hdmi_card_name(names) == "bcm2835 HDMI 1"
    assert hdmi_card_name(names, force_hotplug=[1]) == "bcm2835 HDMI 2"
