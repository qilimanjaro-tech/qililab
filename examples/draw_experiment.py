"""Draw experiment"""
import matplotlib.pyplot as plt
import qibo

from qililab import Experiment
from qililab.constants import DEFAULT_EXPERIMENT_NAME, DEFAULT_PLATFORM_NAME


def load_experiment():
    """Load the platform 'platform_0' from the DB."""
    # Using PLATFORM_MANAGER_DB
    experiment = Experiment(platform_name=DEFAULT_PLATFORM_NAME, experiment_name=DEFAULT_EXPERIMENT_NAME)
    figure = experiment.draw(resolution=0.1)
    figure.show()
    plt.show()


if __name__ == "__main__":
    load_experiment()
