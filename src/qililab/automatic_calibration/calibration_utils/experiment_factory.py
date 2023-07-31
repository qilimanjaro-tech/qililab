from qililab.automatic_calibration.calibration_experiments.qubit_spectroscopy_experiment import (
    QubitSpectroscopyExperiment,
)
from qililab.automatic_calibration.calibration_experiments.rabi_experiment import RabiExperiment
from qililab.automatic_calibration.experiment import Experiment


class ExperimentFactory:
    """
    Factory class that generates a specific type of experiment
    """

    def __init__(self) -> None:
        pass

    def get_experiment(self, experiment_type: str) -> Experiment:
        if experiment_type == "rabi":
            return RabiExperiment()
        elif experiment_type == "qubit_spectroscopy":
            return QubitSpectroscopyExperiment()
        # ...
