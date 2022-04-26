from pathlib import Path

import qibo

from qililab import PLATFORM_MANAGER_DB, PLATFORM_MANAGER_YAML
from qililab.constants import DEFAULT_PLATFORM_DUMP_FILENAME, DEFAULT_PLATFORM_NAME

# FIXME: Need to add backend in qibo's profiles.yml file
backend = {
    "name": "qililab",
    "driver": "qililab.backend.QililabBackend",
    "minimum_version": "0.0.1.dev0",
    "is_hardware": True,
}
qibo.K.profile["backends"].append(backend)
# ------------------------------------------------------


def load_platform_from_database():
    """Load the platform 'platform_0' from the DB."""
    # Using qibo (needed when using qibo circuits)
    qibo.set_backend(backend="qililab", platform=DEFAULT_PLATFORM_NAME)
    print(f"Platform name: {qibo.K.platform}")
    # Using PLATFORM_MANAGER_DB
    platform = PLATFORM_MANAGER_DB.build(platform_name=DEFAULT_PLATFORM_NAME)
    PLATFORM_MANAGER_DB.dump(platform=platform)  # save yaml file with all platform settings
    print(f"Platform INFO: {platform}")


def load_platform_from_yaml():
    """Load the platform configuration from the given yaml file."""
    filepath = Path(__file__).parent / DEFAULT_PLATFORM_DUMP_FILENAME
    platform = PLATFORM_MANAGER_YAML.build_from_yaml(filepath=filepath)
    print(f"Platform INFO: {platform}")


if __name__ == "__main__":
    load_platform_from_database()
    load_platform_from_yaml()
