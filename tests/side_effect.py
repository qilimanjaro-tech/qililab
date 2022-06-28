"""Side effect of the yaml.safe_load() function."""
import ntpath
from io import TextIOWrapper

from .data import MockedSettingsFactory


def yaml_safe_load_side_effect(stream: TextIOWrapper):
    """Side effect for the function safe_load of yaml module."""
    platform_name = ntpath.splitext(ntpath.basename(stream.name))[0]
    return MockedSettingsFactory.get(platform_name=platform_name)
