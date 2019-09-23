import configparser
from typing import Tuple, List
import io
from UM.VersionUpgrade import VersionUpgrade

_renamed_container_id_map = {
    "ultimaker2_0.25": "ultimaker2_olsson_0.25",
    "ultimaker2_0.4": "ultimaker2_olsson_0.4",
    "ultimaker2_0.6": "ultimaker2_olsson_0.6",
    "ultimaker2_0.8": "ultimaker2_olsson_0.8",
}


class VersionUpgrade43to44(VersionUpgrade):
    def getCfgVersion(self, serialised: str) -> int:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialised)
        format_version = int(parser.get("general", "version"))  # Explicitly give an exception when this fails. That means that the file format is not recognised.
        setting_version = int(parser.get("metadata", "setting_version", fallback = "0"))
        return format_version * 1000000 + setting_version

    ##  Upgrades Preferences to have the new version number.
    #
    #   This renames the renamed settings in the list of visible settings.
    def upgradePreferences(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation = None)
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "10"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    ##  Upgrades instance containers to have the new version
    #   number.
    #
    #   This renames the renamed settings in the containers.
    def upgradeInstanceContainer(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(serialized)

        # Update version number.
        parser["metadata"]["setting_version"] = "10"

        # Intent profiles were added, so the quality changes should match with no intent (so "default")
        if parser["metadata"].get("type", "") == "quality_changes":
            parser["metadata"]["intent_category"] = "default"

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]

    ##  Upgrades stacks to have the new version number.
    def upgradeStack(self, serialized: str, filename: str) -> Tuple[List[str], List[str]]:
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(serialized)

        # Update version number.
        if "metadata" in parser:
            parser["metadata"]["setting_version"] = "10"

        if "containers" in parser:
            # With the ContainerTree refactor, UM2 with Olsson block got moved to a separate definition.
            if "6" in parser["containers"]:
                if parser["containers"]["6"] == "ultimaker2":
                    if "metadata" in parser and "has_variants" in parser["metadata"] and parser["metadata"]["has_variants"] == "True":  # This is an Olsson block upgraded UM2!
                        parser["containers"]["6"] = "ultimaker2_olsson"
                        del parser["metadata"]["has_variants"]
                elif parser["containers"]["6"] == "ultimaker2_extended":
                    if "metadata" in parser and "has_variants" in parser["metadata"] and parser["metadata"]["has_variants"] == "True":  # This is an Olsson block upgraded UM2E!
                        parser["containers"]["6"] = "ultimaker2_extended_olsson"
                        del parser["metadata"]["has_variants"]

            # We should only have 6 levels when we start.
            if "7" in parser["containers"]:
                return ([], [])

            # We added the intent container in Cura 4.4. This means that all other containers move one step down.
            parser["containers"]["7"] = parser["containers"]["6"]
            parser["containers"]["6"] = parser["containers"]["5"]
            parser["containers"]["5"] = parser["containers"]["4"]
            parser["containers"]["4"] = parser["containers"]["3"]
            parser["containers"]["3"] = parser["containers"]["2"]
            parser["containers"]["2"] = "empty_intent"

            # Update renamed containers
            for key, value in parser["containers"].items():
                if value in _renamed_container_id_map:
                    parser["containers"][key] = _renamed_container_id_map[value]

        result = io.StringIO()
        parser.write(result)
        return [filename], [result.getvalue()]