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
