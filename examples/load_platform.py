from pathlib import Path

import qibo
from mdformat import file

from qililab import PLATFORM_BUILDER_DB, PLATFORM_BUILDER_YAML

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
    qibo.set_backend(backend="qililab", platform="platform_0")
    print(f"Platform name: {qibo.K.platform}")
    # Using PLATFORM_BUILDER
    platform = PLATFORM_BUILDER_DB.build(platform_name="platform_0")
    platform.dump()  # save yaml file with all platform settings
    print(f"Platform name: {platform}")


def load_platform_from_yaml():
    """Load the platform configuration from the given yaml file."""
    filepath = Path(__file__).parent / "all_platform.yml"
    platform = PLATFORM_BUILDER_YAML.build_from_yaml(filepath=filepath)
    print(f"Platform name: {platform}")


if __name__ == "__main__":
    load_platform_from_database()
    load_platform_from_yaml()
