from abc import ABC, abstractmethod

import calibration_utils.calibration_utils as cal_utils

from qililab.automatic_calibration.calibration_utils.experiment_factory import ExperimentFactory
from qililab.qprogram.qprogram import QProgram

"""
TODO: decide how fitting and plotting functions for each calibration node are determined. There are 2 options:
 1. Define custom plotting and fitting functions for each experiments and pass them as arguments to
    the constructor of the CalibrationNode.
 2. Define general fitting and plotting functions that receive model and labels respectively as arguments.
    Then the CalibrationNode constructor will receive model and labels as arguments and pass them as arguments to the
    fitting and plotting functions.
 """

"""
TODO: add docstrings for latest changes.
"""


class CalibrationNode(ABC):
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

    def __init__(
        self,
        node_id: str,
        qprogram: QProgram,
        fitting_model,
        plotting_labels: dict,
        qubit: int,
        parameters: dict,
        data_validation_threshold: float,
        number_of_random_datapoints: int = 10,
    ):
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

    def run_experiment(self, analyze: bool = True, manual_check: bool = False) -> None:
        """
        Run the experiment

        Args:
            analyze (bool): If set to true the analysis function is run, otherwise it's not. Default value is True.
            manual_check (bool): If set to true, the user will be shown and asked to approve or reject the result of the fitting done by the analysis function. Default value is False.
        """
        user_approves_plot = "n"
        while user_approves_plot == "n":
            # Compile and run the QProgram. TODO: add this once qprogram compiler is in main.

            if analyze:
                # Call the general analysis function with the appropriate model, or the custom one (no need to specify the model there, it will already be hardcoded).
                self.analyze()

            # Plot the results.
            # Show the plot.
            if manual_check:
                user_approves_plot = input("Do you want to repeat the experiment? (y/n): ").lower()
            else:
                user_approves_plot = "y"
