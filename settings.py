import abc
import json
import pathlib

import pykson
from pykson import Pykson


class BaseSettings(pykson.JsonObject):
    """Base settings class that has version control and struct based serialization/deserialization"""

    VERSION = pykson.IntegerField(null=False, default_value=0)

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

        try:
            with open(file_path, encoding="utf-8") as settings_file:
                result = json.load(settings_file)

                if "VERSION" not in result.keys():
                    raise RuntimeError(
                        f"Settings file does not appears to contain a valid settings format: {result}"
                    )

                version = result["VERSION"]

                if version == 0:
                    raise RuntimeError("Settings file contains invalid version number")

                if version > self.VERSION:
                    raise RuntimeError(
                        f"Settings file comes from a future settings version ({version}), tomorrow does not exist"
                    )

                if version < self.VERSION:
                    self.migrate(result)
                    version = result["VERSION"]

                if version != self.VERSION:
                    raise RuntimeError(
                        "Migrate chain failed to update to the latest settings version available"
                    )

                # Copy new content to settings class
                new = Pykson().from_json(result, self.__class__)
                self.__dict__.update(new.__dict__)

        except Exception as exception:
            print(f"Exception: {exception}")

    def save(self, file_path: pathlib.Path):
        """Save settings to file

        Args:
            file_path (pathlib.Path): Path for the settings file
        """
        # Path for settings file does not exist, lets ensure that it does
        parent_path = file_path.parent.absolute()
        if not parent_path.exists():
            parent_path.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as settings_file:
            settings_file.write(Pykson().to_json(self))


class SettingsV1(BaseSettings):
    VERSION = 1
    new_variable = pykson.IntegerField(null=False, default_value=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.VERSION = SettingsV1.VERSION

    def migrate(self, data: dict):
        if data["VERSION"] == SettingsV1.VERSION:
            return

        if data["VERSION"] < SettingsV1.VERSION:
            super().migrate(data)

        data["VERSION"] = SettingsV1.VERSION
        data["new_variable"] = self.new_variable


class SettingsV2(SettingsV1):
    VERSION = 2
    new_variable_dosh = pykson.IntegerField(null=False, default_value=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.VERSION = SettingsV2.VERSION

    def migrate(self, data: dict):
        if data["VERSION"] < SettingsV2.VERSION:
            super().migrate(data)

        data["VERSION"] = SettingsV2.VERSION
        data["new_variable_dosh"] = self.new_variable_dosh


if __name__ == "__main__":
    file_path = pathlib.Path("/tmp/potato/elefante.json")

    a = SettingsV1()
    a.load(file_path)
    a.new_variable = 5
    a.save(file_path)
    print(Pykson().to_json(a))

    b = SettingsV2()
    b.load(file_path)
    b.save(file_path)
    print(Pykson().to_json(b))
