from abc import ABC, abstractmethod

import calibration_utils.calibration_utils as cal_utils

from qililab.automatic_calibration.calibration_utils.experiment_factory import ExperimentFactory


class Experiment(ABC):
    """
    This class represents a node in the calibration graph.
    Each node represent a step of a lager calibration procedure. Each of these steps consists of:
    - an experiment
    - an analysis procedure

    Attributes:
        parameters (dict): A dictionary where keys are parameter names (str) and values are:
                                - timeouts durations in seconds (float), representing an estimate of how long it takes for the parameters to drift.
                                - default sweep interval for the experiment (list(float))
        data_validation_threshold (float): The threshold used by the check_data() method to validate the data fittings.
        timestamps (dict): A dictionary where keys are timestamps and values are the operations that generated the timestamp.
                           This operation can be either a function call of check_data() or of calibrate()
        number_of_random_datapoints (int) : The number of points, chosen randomly within the sweep interval, where we check if the experiment
                                            gets the same outcome as during the last calibration that was run. Default value is 10.
    """

    def __init__(self, parameters: dict, data_validation_threshold: float, number_of_random_datapoints: int = 10):
        self._parameters = parameters
        self._data_validation_threshold = data_validation_threshold
        self._number_of_random_datapoints = number_of_random_datapoints
        self._timestamps = {}

    def check_state(self):
        """
        Check if the node's parameters drift timeouts have passed since the last calibration or data validation (a call of check_data).
        These timeouts represent how long it usually takes for the parameters to drift.

        Args:
            node (CalibrationNode): The node whose parameters need to be checked.

        Returns:
            bool: True if the parameters are in spec, False otherwise.
        """

        # Check if any of the parameters' timeouts have expired.
        for parameter, timeout in self._parameters.items():
            if cal_utils.is_timeout_expired(self.timestamps[-1], timeout):
                return False

    def check_data(self):
        """
        Check if the parameters found in the last calibration are still valid. This removes the need to redo the entire calibration procedure,
        which is much more time-expensive than just calling this method.
        """

        # Choose random datapoints within the sweep interval.
        try:
            random_values = cal_utils.get_random_values(self._parameters.sweepInterval)
        except ValueError as e:
            print(e)

        for value in random_values:
            self.run_experiment(analyze=True, sweep_interval=[value])

        # Check if data obtained now is similar to the one obtained in the last calibration.
        # return in_spec, out_of_spec or bad_data

        # Add timestamp to the timestamps dictionary.
        self.timestamps[cal_utils.get_timestamp()] = "check_data"

    def calibrate(self):
        """
        Run the calibration experiment on its default interval of sweep values.
        """

        self.run_experiment(analyze=True)

        # TODO: add user interaction condition

        # Add timestamp to the timestamps dictionary.
        self._timestamps[cal_utils.get_timestamp()] = "calibrate"

    def run_experiment(
        self, analyze: bool = True, sweep_interval: list(float) = None, manual_check: bool = False
    ) -> None:
        # sourcery skip: remove-empty-nested-block, remove-redundant-if
        """
        Run the experiment

        Args:
            analyze (bool): If set to true the analysis function is run, otherwise it's not. Default value is True.
            sweep_interval (list(float)): The sweep interval where the experiment is run. Default value is default_sweep_interval.
            manual_check (bool): If set to true, the user will be shown and asked to approve or reject the result of the fitting done by the analysis function. Default value is False.
        """

        if sweep_interval is None:
            sweep_interval = self._parameters.default_sweep_interval

        if analyze:
            self.analyze()

        if manual_check:
            # Show fitting done by analysis function and ask user to approve or reject it.
            pass

        # Run experiment

    @abstractmethod
    def analyze(self) -> None:
        # For each type of experiment this will have a specific implementation.
        # Note for forgetful developer: an abstract method cannot have a body.
        pass
