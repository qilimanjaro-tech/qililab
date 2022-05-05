"""Draw experiment"""
import qibo

from qililab import Experiment
from qililab.constants import DEFAULT_EXPERIMENT_NAME, DEFAULT_PLATFORM_NAME

# FIXME: Need to add backend in qibo's profiles.yml file
backend = {
    "name": "qililab",
    "driver": "qililab.backend.QililabBackend",
    "minimum_version": "0.0.1.dev0",
    "is_hardware": True,
}
qibo.K.profile["backends"].append(backend)
# ------------------------------------------------------


def load_experiment():
    """Load the platform 'platform_0' from the DB."""
    # Using qibo (needed when using qibo circuits)
    qibo.set_backend(backend="qililab", platform=DEFAULT_PLATFORM_NAME)
    # Using PLATFORM_MANAGER_DB
    experiment = Experiment(platform_name=DEFAULT_PLATFORM_NAME, experiment_name=DEFAULT_EXPERIMENT_NAME)
    experiment.draw(resolution=0.1)


if __name__ == "__main__":
    load_experiment()
