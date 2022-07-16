""" compare two runcards and print the differences """
import os
from pathlib import Path
from pprint import pprint

from deepdiff import DeepDiff

from qililab.platform.platform_manager_yaml import PlatformManagerYAML

os.environ["RUNCARDS"] = str(Path(__file__).parent)


def compare_runcards(first: dict, second: dict):
    """compare the runcards"""
    ddiff = DeepDiff(first, second, verbose_level=2)
    pprint(ddiff, indent=2)


if __name__ == "__main__":
    pm_yaml = PlatformManagerYAML()
    FIRST_RUNCARD_NAME = "galadriel_controller"
    SECOND_RUNCARD_NAME = "galadriel_mx"
    first_runcard = pm_yaml._load_platform_settings(  # pylint: disable=protected-access
        platform_name=FIRST_RUNCARD_NAME
    )
    second_runcard = pm_yaml._load_platform_settings(  # pylint: disable=protected-access
        platform_name=SECOND_RUNCARD_NAME
    )
    compare_runcards(first=first_runcard, second=second_runcard)
