import abc
import json
import pathlib

import pykson
from pykson import Pykson


class BadSettingsFile(ValueError):
    """Settings file is not valid."""


class SettingsFromTheFuture(ValueError):
    """Settings file version is from a newer version of the service."""


class MigrationFail(RuntimeError):
    """Could not apply migration."""


class BadAttributes(BadSettingsFile):
    """Attributes on settings file are not valid."""


class BaseSettings(pykson.JsonObject):
    """Base settings class that has version control and struct based serialization/deserialization"""

    VERSION = pykson.IntegerField(default_value=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abc.abstractmethod
    def migrate(self, data: dict):
        """Function used to migrate from previous settings verion

        Args:
            data (dict): Data from the previous version settings
        """
        raise RuntimeError(
            "Migrate function from base class was called, settings file appears to be not possible to be migrated"
        )

    def load(self, file_path: pathlib.Path):
        """Load settings from file

        Args:
            file_path (pathlib.Path): Path for settings file
        """
        if not file_path.exists():
            raise RuntimeError(f"Settings file does not exist: {file_path}")

        with open(file_path, encoding="utf-8") as settings_file:
            result = json.load(settings_file)

            if "VERSION" not in result.keys():
                raise BadSettingsFile(f"Settings file does not appears to contain a valid settings format: {result}")

            version = result["VERSION"]

            if version == 0:
                raise BadAttributes("Settings file contains invalid version number")

            if version > self.VERSION:
                raise SettingsFromTheFuture(
                    f"Settings file comes from a future settings version: {version}, "
                    f"latest supported: {self.VERSION}, tomorrow does not exist"
                )

            if version < self.VERSION:
                self.migrate(result)
                version = result["VERSION"]

            if version != self.VERSION:
                raise MigrationFail("Migrate chain failed to update to the latest settings version available")

            # Copy new content to settings class
            new = Pykson().from_json(result, self.__class__)
            self.__dict__.update(new.__dict__)

    def save(self, file_path: pathlib.Path):
        """Save settings to file

        Args:
            file_path (pathlib.Path): Path for the settings file
        """
        # Path for settings file does not exist, lets ensure that it does
        parent_path = file_path.parent.absolute()
        if not parent_path.exists():
            parent_path.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as settings_file:
            settings_file.write(Pykson().to_json(self))

    def reset(self):
        """Reset internal data to default values"""
        new = self.__class__()
        self.__dict__.update(new.__dict__)
