import numpy as np

from qililab import QProgram


class CalibrationNode:
    """
    This class represents a node in the calibration graph.
    Each node represent a step of a lager calibration procedure. Each of these steps consists of:
        *an experiment
        *an analysis procedure (fitting and plotting of experimental data)

    Attributes:
        _node_id (str): A unique identifier for the node. It should describe what the node does in the calibration graph.
        _qprogram (function): The function that generates the QProgram describing the experiment done in the node.
        _sweep_interval (dict): Dictionary with 3 keys describing the sweep values of the experiment. The keys are:
                                *start
                                *step
                                *stop
                                The sweep values are all the numbers between 'start' and 'stop', separated from each other
                                by the distance 'step'
        _is_refinement (bool): True if this experiment refines data obtained from a previous experiment. False otherwise.
                                If True, the sweep values depend on the data obtained from the previous experiment. See run_experiment
                                for more details.
        _analysis_function (function): analysis function for the experimental data. If set to None, we use a standard analysis function defined for all experiments.
        _fitting_model: The fitting model for the experimental data. If None, it means we're using a custom fitting function that already has a built-in fitting model.
        _plotting_labels (dict): Labels used in the plot of the fitted experimental data. The keys of the dictionary indicate the axis,
                                    the values indicate the corresponding label.
        _qubit (int): The qubit that is being calibrated by the calibration graph to which the node belongs.
        _parameter (str): The parameter that this node will tune.
        _alias (str): The alias of the bus where the parameters is set #TODO: I think this is part of the old buses implementation: if possible, remove asap.
        _drift_timeout (float): A durations in seconds, representing an estimate of how long it takes for the parameter to drift.
        _data_validation_threshold (float): The threshold used by the check_data() method to validate the data fittings.
        _timestamps (dict): A dictionary where keys are timestamps and values are the operations that generated the timestamp.
                           This operation can be either a function call of check_data() or of calibrate()
        _number_of_random_datapoints (int) : The number of points, chosen randomly within the sweep interval, where we check if the experiment
                                            gets the same outcome as during the last calibration that was run. Default value is 10.
        _experiment_results: The results of the calibration experiment represented as a dictionary. For now this only supports experiment run on QBlox hardware. 
                             The dictionary is a standard structure in which the data is stored by the QBlox hardware. For more details see this documentation: 
                             https://qblox-qblox-instruments.readthedocs-hosted.com/en/master/api_reference/pulsar.html#qblox_instruments.native.Pulsar.get_acquisitions
        _manual_check (bool): If True, the user is shown the plot for the experiment assigned to this node. The user must approve or reject the plot. If the user rejects
                              the plot, the experiment is run again.
        _needs_recalibration (bool): Flag to indicate if the last calibration run on this node has been unsuccessful and thus shuold be done again.
    """

    def __init__(
        self,
        node_id: str,
        qprogram,
        sweep_interval: dict = None,
        is_refinement: bool = False,
        analysis_function = None,
        fitting_model = None,
        plotting_labels: dict = None,
        qubit: int = None,
        parameter: str = None,
        alias: str = None,
        drift_timeout: float = 0,
        data_validation_threshold: float = 1,
        number_of_random_datapoints: int = 10,
        manual_check: bool = False
    ):
        self._node_id = node_id
        self._qprogram = qprogram
        self._sweep_interval = sweep_interval
        self._is_refinement = is_refinement
        self._analysis_function = self.analysis if analysis_function is None else analysis_function
        self._fitting_model = fitting_model
        self._plotting_labels = plotting_labels
        self._qubit = qubit
        self._parameter = parameter
        self._alias = alias
        self._drift_timeout = drift_timeout
        self._data_validation_threshold = data_validation_threshold
        self._number_of_random_datapoints = number_of_random_datapoints
        self._manual_check = manual_check
        self._timestamps = {}
        self._experiment_results = None
    
    def _hash_(self) -> int:
        """
        Make the CalibrationNode object hashable by hashing its unique identifier _node_id.
        This is necessary because to be a node in a NetworkX graph, an object must be hashable.

        Returns:
            int: The hash value of the object.
        """        
        return hash(self.node_id)
    
    def analysis(self) -> int|float:
        """
        The default analysis function used to analyze experimental data to obtain the optimal parameter values.
        To be implemented by a future intern.

        Returns:
            int|float: The optimal parameter value.
        """        
        pass

    @property
    def node_id(self):
        return self._node_id
    
    @property
    def qprogram(self):
        return self._qprogram
    
    @property
    def sweep_interval(self):
        return self._sweep_interval
    
    @sweep_interval.setter
    def sweep_interval(self, value):
        self._sweep_interval = value
    
    @property
    def is_refinement(self):
        return self._is_refinement
    
    @property
    def analysis_function(self):
        return self._analysis_function
    
    @property
    def parameter(self):
        return self._parameter
    
    @property
    def alias(self):
        return self._alias
    
    @property
    def drift_timeout(self):
        return self._drift_timeout
    
    @property
    def timestamps(self):
        return self._timestamps
    
    def add_timestamp(self, timestamp: int, type_of_timestamp: str):
        self._timestamps[timestamp] = type_of_timestamp
        
    @property
    def experiment_results(self):
        return self._experiment_results
    
    @experiment_results.setter
    def experiment_results(self, experiment_results):
        self._experiment_results = experiment_results
    
    @property
    def manual_check(self):
        return self._manual_check
    
    @manual_check.setter
    def manual_check(self, manual_check: bool):
        self._manual_check = manual_check
        
    @property
    def needs_recalibration(self): 
        return self._needs_recalibration
    
    @needs_recalibration.setter
    def needs_recalibration(self, value):
        self._needs_recalibration = value
        