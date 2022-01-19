import os
import pathlib
import re
from typing import Optional, Type

import appdirs
import settings


class Manager:
    SETTINGS_NAME_PREFIX = "settings-"

    def __init__(self, project_name: str, settings_type, config_path: Optional[pathlib.Path] = None):
        assert project_name, "project_name should be not empty"
        assert issubclass(settings_type, settings.BaseSettings), "settings_type should use BaseSettings as subclass"

        self.project_name = project_name
        self.config_path = (
            config_path.joinpath(project_name)
            if config_path
            else pathlib.Path(appdirs.user_config_dir(self.project_name))
        )
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.settings_type = settings_type
        self._settings = None

    @property
    def settings(self) -> Type["self.settings_type"]:
        """Getter point for settings

        Returns:
            [self.settings_type]: The settings defined in the constructor
        """
        if not self._settings:
            self.load()

        return self._settings

    @settings.setter
    def settings(self, value: Type["self.settings_type"]):
        """Setter point for settings, save settings in any change

        Args:
            value ([self.settings_type]): The settings defined in the constructor
        """
        if not self._settings:
            self.load()

        self._settings = value
        self.save()

    def settings_file_path(self) -> pathlib.Path:
        """Return the settings file for the version specified in the constructor settings

        Returns:
            pathlib.Path: Path for the settings file
        """
        return self.config_path.joinpath(f"{Manager.SETTINGS_NAME_PREFIX}{self.settings_type.VERSION}.json")

    @staticmethod
    def load_from_file(settings_type: Type["T"], file_path: pathlib.Path) -> Type["T"]:
        """Load settings from a generic location and settings type

        Args:
            settings_type (BaseSettings): Settings type that inherits from BaseSettings.
            file_path (pathlib.Path): Path for a valid settings file

        Returns:
            [type]: [description]
        """
        assert issubclass(settings_type, settings.BaseSettings), "settings_type should use BaseSettings as subclass"

        settings_data = settings_type()

        if file_path.exists():
            settings_data.load(file_path)
        else:
            settings_data.save(file_path)

        return settings_data

    def save(self):
        """Save settings"""
        self.settings.save(self.settings_file_path())

    def load(self):
        """Load settings"""

        # Get all possible settings candidates and sort it by version
        valid_files = [
            possible_file
            for possible_file in os.listdir(self.config_path)
            if possible_file.startswith(Manager.SETTINGS_NAME_PREFIX)
        ]
        valid_files.sort(key=lambda x: int(re.search(f"{Manager.SETTINGS_NAME_PREFIX}(\\d+)", x).group(1)))
        valid_files.reverse()

        for valid_file in valid_files:
            file_path = self.config_path.joinpath(valid_file)
            try:
                self._settings = Manager.load_from_file(self.settings_type, file_path)
                break
            except settings.SettingsFromTheFuture as exception:
                print("Invalid settings, going to try another file:", exception)
        else:
            self._settings = Manager.load_from_file(self.settings_type, self.settings_file_path())
