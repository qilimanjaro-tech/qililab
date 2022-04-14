import qibo

from qililab import PLATFORM_BUILDER

# FIXME: Need to add backend in qibo's profiles.yml file
backend = {
    "name": "qililab",
    "driver": "qililab.backend.QililabBackend",
    "minimum_version": "0.0.1.dev0",
    "is_hardware": True,
}
qibo.K.profile["backends"].append(backend)
# ------------------------------------------------------


def load_platform():
    """Load the platform 'platform_0' from the settings folder."""
    # Using qibo (needed when using qibo circuits)
    qibo.set_backend(backend="qililab", platform="platform_0")
    print(f"Platform name: {qibo.K.platform}")
    # Using PLATFORM_BUILDER
    platform = PLATFORM_BUILDER.build(platform_name="platform_0")
    print(f"Platform name: {platform}")


if __name__ == "__main__":
    load_platform()
