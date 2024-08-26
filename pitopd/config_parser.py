#!/usr/bin/python3
from dataclasses import dataclass, field
from itertools import count
from typing import Optional


@dataclass
class Section:
    name: str
    settings: list[str] = field(default_factory=list)
    id: int = field(default_factory=count().__next__, init=False)

    def cleanup(self):
        return [x for x in self.settings if len(x) > 0 and not x.startswith("#")]

    def find(self, setting_name: str):
        for setting in self.settings:
            if setting.startswith(setting_name):
                return setting
        return None

    def add(self, setting: str):
        self.settings.append(setting)

    def remove(self, setting_name: str):
        setting = self.find(setting_name)
        if setting is not None:
            self.settings.remove(setting)
        else:
            print(
                f"Section.remove(): '{setting_name}' not found in section '{self.name}'"
            )

    def comment(self, setting_name: str):
        setting = self.find(setting_name)
        if setting is not None:
            self.settings[self.settings.index(setting)] = f"#{setting}"
        else:
            print(
                f"Section.comment(): '{setting_name}' not found in section '{self.name}'"
            )

    def uncomment(self, setting_name: str):
        if not setting_name.startswith("#"):
            setting_name = f"#{setting_name}"
        setting = self.find(setting_name)
        if setting is not None:
            self.settings[self.settings.index(setting)] = setting[1:]
        else:
            print(
                f"Section.uncomment(): '{setting_name}' not found in section '{self.name}'"
            )


class RpiConfigParser:
    def __init__(self, config_file_path):
        self.sections = []
        self.path = config_file_path
        self.load()

    def load(self):
        self.sections = []
        section_name = "all"
        section = Section(name=section_name, settings=[])
        with open(self.path, "r") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            line = line.strip()
            if (
                not line.startswith("#")
                and len(line) >= 2
                and line[0] == "["
                and line[-1] == "]"
            ):
                # Found a section tag
                if line[1:-1] == "all" or section_name != line[1:-1]:
                    self.add(section)
                    section_name = line[1:-1]
                section = Section(name=section_name, settings=[])
                continue
            section.settings.append(line)
            if i == len(lines) - 1:
                self.add(section)

    def add(self, section: Section) -> None:
        if not isinstance(section, Section):
            raise TypeError(
                "RpiConfigParser.add_section(): section must be of type Section"
            )
        self.sections.append(section)

    def remove(self, section: Section) -> None:
        if not isinstance(section, Section):
            raise TypeError(
                "RpiConfigParser.add_section(): section must be of type Section"
            )
        self.sections.remove(section)

    def update(self, section: Section) -> None:
        if not isinstance(section, Section):
            raise TypeError(
                "RpiConfigParser.add_section(): section must be of type Section"
            )
        for i, s in enumerate(self.sections):
            if s.id == section.id:
                self.sections[i] = section
                return
        self.add(section)

    def find(self, section_name: str) -> Optional[Section]:
        # A config file can have multiple sections with the same name.
        # This function returns the last one since repeated settings are overwritten.
        for section in reversed(self.sections):
            if section.name == section_name:
                return section
        return None

    def find_all(self, section_name: str) -> list[Section]:
        # Return an array of sections with the same name
        response = []
        sections = reversed(self.sections)
        for section in sections:
            if section.name == section_name:
                response.append(section)
        return response

    def write(self, path: Optional[str] = None):
        if path is None:
            path = self.path
        with open(path, "w") as f:
            for i, section in enumerate(self.sections):
                # don't print the "all" section if it's the first one
                if not (i == 0 and section.name == "all"):
                    f.write(f"[{section.name}]\n")
                for setting in section.settings:
                    f.write(f"{setting}\n")
