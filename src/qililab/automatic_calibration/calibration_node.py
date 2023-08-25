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
        _experiment (function): The function that generates and executes the experiment to be done in the node. This experiment 
                                can be anything (a Qprogram, a circuit with a pulse schedule, ...), as long as it returns its
                                results in the following format: an array with dimensions (2, N), where N is the number of elements
                                of the loop that is run by the experiment. This array contains the results of the experiment for the
                                'I' and the 'Q' quadrature. If the results array is called 'results_array', then the 'I' results will
                                be in array_results[0] and the 'Q' results will be in array_results[1].
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
        _fit_quadrature (str): The quadrature that has to be fitted by the analysis function. It can be either 'i' or 'q'.
        _plotting_labels (dict): Labels used in the plot of the fitted experimental data. The keys of the dictionary indicate the axis,
                                    the values indicate the corresponding label.
        _qubit (int): The qubit whose parameter (one of them) is calibrated by this node. This attribute is used to name the drive bus, which is qubit-specific, 
                      so it can be passed to the function contained in the _experiment attribute. NOTE: this is useless for now, because bus aliases are not yet standardized
                      and it's therefore not possible to have a standard mapping between qubit number and bus alias. That's why the _drive_bus and _readout_bus attributes are
                      here.
        _drive_bus (str): The alias of the drive bus. The correct alias of the bus can be found in the runcard.
        _readout_bus (str): The alias of the readout bus. The correct alias of the bus can be found in the runcard.
        _parameter (str): The parameter that this node will tune.
        _drift_timeout (float): A durations in seconds, representing an estimate of how long it takes for the parameter to drift.
        _data_validation_threshold (float): The threshold used by the check_data() method to validate the data fittings. #TODO: this is now used for the rsquared value in check_data, change docs
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
        experiment,
        sweep_interval: dict = None,
        is_refinement: bool = False,
        analysis_function = None,
        fitting_model = None,
        fit_quadrature: str = 'i',
        plotting_labels: dict = None,
        qubit: int = None,
        drive_bus: str = None,
        readout_bus: str = None,
        parameter: str = None,
        drift_timeout: float = 0,
        data_validation_threshold: float = 0.96,
        number_of_random_datapoints: int = 10,
        manual_check: bool = False,
        needs_recalibration = False
    ):
        self._node_id = node_id
        self._experiment = experiment
        self._sweep_interval = sweep_interval
        self._is_refinement = is_refinement
        self._analysis_function = self.analysis if analysis_function is None else analysis_function
        self._fitting_model = fitting_model
        if fit_quadrature != 'i' and fit_quadrature != 'q':
            raise ValueError("Fit quadrature can only be 'i' or 'q'")
        self._fit_quadrature = fit_quadrature 
        self._plotting_labels = plotting_labels
        self._qubit = qubit
        self._drive_bus = drive_bus
        self._readout_bus = readout_bus
        self._parameter = parameter
        self._drift_timeout = drift_timeout
        if not(0 <= data_validation_threshold <= 1): raise ValueError("Data validation threshold must be between 0 and 1, as it represent the R-squared value of a fit.")
        self._data_validation_threshold = data_validation_threshold
        self._number_of_random_datapoints = number_of_random_datapoints
        self._manual_check = manual_check
        self._timestamps = {}
        self._experiment_results = None
        self._needs_recalibration = needs_recalibration
    
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
    def experiment(self):
        return self._experiment
    
    @property
    def sweep_interval(self):
        return self._sweep_interval
    
    @sweep_interval.setter
    def sweep_interval(self, value):
        self._sweep_interval = value
        
    def sweep_interval_as_array(self) -> list:
        return np.arange(self._sweep_interval["start"], self._sweep_interval["stop"], self._sweep_interval["step"])
    
    @property
    def is_refinement(self):
        return self._is_refinement
    
    @property
    def analysis_function(self):
        return self._analysis_function
    
    @property
    def fitting_model(self):
        return self._fitting_model
    
    @property
    def fit_quadrature(self):
        return self._fit_quadrature
    
    @property
    def drive_bus(self):
        return self._drive_bus
    
    @property
    def readout_bus(self):
        return self._readout_bus
    
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
    def data_validation_threshold(self):
        return self._data_validation_threshold
    
    @property
    def timestamps(self):
        return self._timestamps
    
    def add_timestamp(self, timestamp: float | dict, type_of_timestamp: str = None):
        if isinstance(timestamp, float):
            if type_of_timestamp is None:
                raise ValueError("Timestamp must have a type_of_timestamp attribute associated.")
            self._timestamps[timestamp] = type_of_timestamp
        elif isinstance(timestamp, dict):
            dict_key = list(timestamp)[0]    
            self._timestamps[dict_key] = timestamp[dict_key]   
        
    def get_latest_timestamp(self, value_only: bool = False) -> dict:
        """Gets the latest timestamp associated with the node. For more details on the meaning of these timestamp, see documentation
        of the CalibrationNode class.

        Args:
            value_only (bool, optional): The _timestamps attribute of the CalibrationNode class is a dictionary where keys are UNIX timestamps
            and values are strings indicating how the timestamp was generated (if by a calibration experiment or else). If this argument is set 
            to True, the function only returns the value of the most recent UNIX timestamp, not the string. Otherwise it returns a dictionary with 
            only 1 key and value, where the key is the most recent UNIX timestamp and the value is its corresponding string as described above.

        Returns:
            float | dict: Depending on the value of the 'value_only' attribute, just a timestamp or a dictionary with only 1 key and value. See description
            of the 'value_only' argument for more information.
        """    
        if self._timestamps is None or (not hasattr(self, 'timestamps')) or len(self._timestamps) == 0:
            return {}
        latest_timestamp_key = list(self.timestamps)[-1]
        if value_only:
            return latest_timestamp_key    
        return {latest_timestamp_key: self.timestamps[latest_timestamp_key]}
        
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
        