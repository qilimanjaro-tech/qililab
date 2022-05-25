"""Side effect of the yaml.safe_load() function."""
import ntpath
from io import TextIOWrapper

from ..data import MockedSettingsHashTable


def yaml_safe_load_side_effect(stream: TextIOWrapper):
    """Side effect for the function safe_load of yaml module."""
    filename = ntpath.splitext(ntpath.basename(stream.name))[0]
    return MockedSettingsHashTable.get(name=filename)
