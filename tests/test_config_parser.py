import pytest

from pitopd.config_parser import RpiConfigParser, Section


def files_contents_match(file1, file2):
    with open(file1, "r") as f1:
        with open(file2, "r") as f2:
            f1_read = f1.read()
            f2_read = f2.read()
            if f1_read != f2_read:
                print(f"File contents do not match:\n{f1_read}\n!=\n{f2_read}")
                return False
    return True


# RpiConfigParser class tests
def test_config_parser_constructor_fails_if_file_does_not_exist():
    with pytest.raises(FileNotFoundError):
        RpiConfigParser("non_existent_file")


def test_config_parser_loads_file():
    config = RpiConfigParser("tests/rpi_config_txt/test_config.txt")
    assert config is not None


def test_config_parser_get_section():
    config = RpiConfigParser("tests/rpi_config_txt/test_config.txt")
    assert len(config.sections) == 3
    # Find existing sections
    assert config.find("all") is not None
    assert config.find("all").name == "all"
    assert config.find("pi4") is not None
    assert config.find("pi4").name == "pi4"
    # Find non existing section
    assert config.find("non_existent") is None


def test_config_parser_get_all_sections():
    config = RpiConfigParser("tests/rpi_config_txt/test_config.txt")
    # get_all_sections for an existent section
    existent_section_arr = config.find_all("all")
    assert isinstance(existent_section_arr, list)
    assert len(existent_section_arr) == 2
    assert isinstance(existent_section_arr[0], Section)
    assert existent_section_arr[0].name == "all"
    assert isinstance(existent_section_arr[1], Section)
    assert existent_section_arr[1].name == "all"

    # get_all_sections for a non existent section
    non_existent_section_arr = config.find_all("non_existent")
    assert isinstance(non_existent_section_arr, list)
    assert len(non_existent_section_arr) == 0


def test_config_parser_add_remove_section():
    config = RpiConfigParser("tests/rpi_config_txt/test_config.txt")
    assert len(config.sections) == 3

    # Adding a section of invalid type should raise an exception
    with pytest.raises(TypeError):
        config.add("not_a_section")
    assert len(config.sections) == 3

    # Adding a valid section
    section = Section("new_section", [])
    config.add(section)
    assert len(config.sections) == 4
    assert config.find("new_section") == section

    # Removing a section of invalid type should raise an exception
    with pytest.raises(TypeError):
        config.remove("not_a_section")
    assert len(config.sections) == 4

    # Removing a valid section
    config.remove(section)
    assert len(config.sections) == 3
    assert config.find("new_section") is None


def test_config_parser_write():
    # Reading a file and writing it back should result in the same file
    config = RpiConfigParser("tests/rpi_config_txt/test_config.txt")
    config.write("/tmp/test_config_output.txt")
    assert files_contents_match(
        "tests/rpi_config_txt/test_config.txt", "/tmp/test_config_output.txt"
    )

    # Overwritting the file should result in the same file
    config = RpiConfigParser("/tmp/test_config_output.txt")
    config.write()
    assert files_contents_match(
        "tests/rpi_config_txt/test_config.txt", "/tmp/test_config_output.txt"
    )

    # Modifying the file should result in a different file
    config = RpiConfigParser("/tmp/test_config_output.txt")
    config.find("all").add("this-is-a-new-setting")
    config.write()

    assert files_contents_match(
        "tests/rpi_config_txt/test_config.txt", "/tmp/test_config_output.txt"
    )


def test_config_parser_load():
    # When no tags are present, the file should be loaded as a single section under 'all'
    config = RpiConfigParser("tests/rpi_config_txt/no_tags_config.txt")
    assert len(config.sections) == 1
    assert config.sections[0].name == "all"

    # Multiple tags are stored as separate sections
    config = RpiConfigParser("tests/rpi_config_txt/multiple_tags_config.txt")
    assert len(config.sections) == 5
    assert config.sections[0].name == "all"
    assert config.sections[1].name == "pi4"
    assert config.sections[2].name == "all"
    assert config.sections[3].name == "pi3"
    assert config.sections[4].name == "all"

    # Handle case where first tag isn't 'all'
    config = RpiConfigParser("tests/rpi_config_txt/first_tag_is_different.txt")
    assert len(config.sections) == 5
    assert config.sections[0].name == "all"
    assert len(config.sections[0].settings) == 0
    assert config.sections[1].name == "pi4"
    assert config.sections[2].name == "all"
    assert config.sections[3].name == "pi3"
    assert config.sections[4].name == "all"


# Section class tests
def test_section_find_setting():
    section = Section("whatever", ["setting1", "setting2", "setting3"])

    # Looking for a setting returns the setting
    assert section.find("setting1") == "setting1"

    # Looking for a non existant setting returns None
    assert section.find("what?") is None

    # Add a setting and look it up
    section.add("what?")
    assert section.find("what?") == "what?"

    # Comment out setting
    section.comment("what?")
    assert section.find("what?") is None

    # Can find commented settings
    assert section.find("#what?") == "#what?"


def test_section_add_remove_settings():
    section = Section("whatever", [])

    # Add settings
    assert len(section.settings) == 0
    section.add("setting1")
    assert len(section.settings) == 1
    assert section.settings[0] == "setting1"
    section.add("setting2")
    assert len(section.settings) == 2
    assert section.settings[1] == "setting2"

    # Remove settings
    section.remove("setting1")
    assert len(section.settings) == 1
    assert section.settings[0] == "setting2"
    section.remove("setting2")
    assert len(section.settings) == 0


def test_section_comment_uncomment():
    section = Section("whatever", ["setting1", "setting2"])

    # Comment out existing setting
    section.comment("setting1")
    assert section.find("setting1") is None
    assert section.find("#setting1") == "#setting1"
    assert len(section.settings) == 2

    # Uncomment existing setting by name
    section.uncomment("setting1")
    assert section.find("setting1") == "setting1"
    assert section.find("#setting1") is None
    assert len(section.settings) == 2

    # Uncomment existing setting by commented name
    section.comment("setting1")
    assert section.find("setting1") is None

    section.uncomment("#setting1")
    assert section.find("setting1") == "setting1"
    assert section.find("#setting1") is None
    assert len(section.settings) == 2

    # Comment out non existing setting
    section.comment("setting3")
    assert section.find("setting3") is None
    assert section.find("#setting3") is None
    assert len(section.settings) == 2

    # Uncomment non existing setting
    section.uncomment("setting3")
    assert section.find("setting3") is None
    assert section.find("#setting3") is None
    assert len(section.settings) == 2
