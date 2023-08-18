import networkx as nx

from calibration_utils.calibration_utils import is_timeout_expired, get_timestamp, get_random_values
from qililab.automatic_calibration.calibration_node import CalibrationNode
from qililab.platform.platform import Platform


class Controller:
    """Class that controls the automatic calibration sequence.

    Attributes:
        _calibration_graph (nx.DiGraph): The calibration graph. This is a directed graph where each node is a CalibrationNode object.
        _platform (Platform): The platform where the experiments will be run. See the Platform class for more information.
    """

    def __init__(self, platform: Platform, calibration_graph: nx.DiGraph = None, manual_check_all: bool = False):
        if calibration_graph is None:
            self._calibration_graph = nx.DiGraph()
        else:
            self._calibration_graph = calibration_graph
        # Note to future self: The calibration graph is initialized as an empty directed graph.
        # In methods that add a new node, make a check to see if the graph is still a DAG
        self._platform = platform
        
        if manual_check_all:
            for node in self._calibration_graph.nodes(): node.manual_check = True

    def maintain(self, node: CalibrationNode):
        """This is primary interface for our calibration procedure and it's the highest level algorithm.
        We call maintain on the node that we want in spec, and maintain will call all the subroutines necessary to do that.
        We design 'maintain' to start actually acquiring data (by calling 'check_data' or 'calibrate') in the optimal location
        in the graph to avoid extra work: for example if node A depends on node B, before trying to calibrate node A we check
        the state of node B. If node B is out of spec or has bad data, calibrating A will be a waste of resource because we
        will be doing so based on faulty data.

        Args:
            node (CalibrationNode): The node where we want to start the algorithm. At the beginning of the calibration procedure,
                                this node will be the highest level node in the calibration graph.
        """

        # Recursion over all the nodes that the current node depends on.
        for n in self.dependents(node):
            self.maintain(n)

        # check_state
        result = self.check_state(node)
        if result:
            return

        # check_data
        result = self.check_data(node)
        if result == "in_spec":
            return
        elif result == "bad_data":
            for n in self.dependents(node):
                self.diagnose(n)

        # calibrate
        result = self.calibrate(node)

        self.update_parameter(node = node, parameter_value = result)


    def diagnose(self, node: CalibrationNode):
        """This is a method called by 'maintain' in the special case that its call of 'check_data' finds bad data.
        'maintain' assumes that our knowledge of the state of the system matches the actual state of the
        system: if we knew a node would return bad data, we wouldn't bother running experiments on it.
        The fact that check_data returns bad data means that that's not the case: out knowledge of the state
        of the system is inaccurate. The purpose of diagnose is to repair inaccuracies in our knowledge of the
        state of the system so that maintain can resume.

        Args:
            node (CalibrationNode): The node where we want to start the algorithm.

        Returns:
            bool: True is there have been recalibrations, False otherwise. The return value is only used by recursive calls.
        """

        # check_data
        result = self.check_data(node)
        
        # in spec case
        if result == "in_spec":
            return False

        # bad data case
        if result == "bad_data":
            recalibrated = [self.diagnose(n) for n in self.dependents(node)]
        if not any(recalibrated):
            return False

        # calibrate
        result = self.calibrate(node)
    
        self.update_parameter(node = node, parameter_value = result)
        
        return True

    def run_calibration(self, node: CalibrationNode = None) -> None:
        """Run the calibration procedure starting from the given node.

        Args:
            node (CalibrationNode, optional): The node from which to start the calibration. When it is None it means we're in the root call.
                                         In that case we start from the highest level node in the calibration graph. 'maintain` will recursively
                                         calibrate all the lower level nodes.
        """
        if node is None:
            # Find highest level node in the calibration graph, the one that no other node depends on. If we call maintain from this node, 
            # 'maintain` will recursively call itself on all the lower level nodes.
            node = (
                [node for node, in_degree in self._calibration_graph.in_degree() if in_degree == 0]
            )  

        self.maintain(node)

    def check_state(self, node: CalibrationNode) -> bool:
        """
        Check if the node's parameters drift timeouts have passed since the last calibration or data validation (a call of check_data).
        These timeouts represent how long it usually takes for the parameters to drift.

        Args:
            node: The node whose parameters need to be checked.

        Returns:
            bool: True if the parameter's drift timeout has not yet expired, False otherwise.
        """
        
        return not is_timeout_expired(node.timestamps[-1], node.drift_timeout)

    def check_data(self, node: CalibrationNode) -> str:
        """
        Check if the parameters found in the last calibration are still valid. This removes the need to redo the entire calibration procedure,
        which is much more time-expensive than just calling this method.
        
        Args:
            node: The node whose parameters need to be checked.

        Returns:
            str: TODO: finish docstrings
        """

        # Choose random datapoints within the sweep interval.
        try:
            random_values = get_random_values(node.sweep_interval)
        except ValueError as e:
            print(e)

        for value in random_values:
            self.run_experiment(analyze=True, experiment_point=value)

        # #TODO: implement: Check if data obtained now is similar to the one obtained in the last calibration.
        # return in_spec, out_of_spec or bad_data

        # Add timestamp to the timestamps list of the node.
        node.add_timestamp(timestamp=get_timestamp(), timestamp_type="check_data")

    def calibrate(self, node: CalibrationNode) -> float | str | bool:
        """Run a node's calibration experiment on its default interval of sweep values.

        Args:
            node (CalibrationNode): The node where the calibration experiment is run.

        Returns:
            float | str | bool: The optimal parameter value found by the calibration experiment.
        """        

        optimal_parameter_value = self.run_experiment(node)

        # Add timestamp to the timestamps list of the node.
        node.add_timestamp(timestamp=get_timestamp, type_of_timestamp="calibration")
        
        return optimal_parameter_value

    def run_experiment(self, node: CalibrationNode, analyze: bool = True, experiment_point: float = None) -> float | str | bool:
        """
        Run the experiment, fit and plot data.

        Args:
            analyze (bool): If set to true the analysis function is run, otherwise it's not. Default value is True. TODO: is this useful? Is there a case when we don't want to analyze?
            manual_check (bool): If set to true, the user will be shown and asked to approve or reject the result of the fitting done by the analysis function. Default value is False.
            experiment_point (float): If None, the experiment was started by the 'calibrate' method, and will be run on the entire default sweep interval.
                                    If not None, the experiment was started by the 'check_data' method, and will be run only in the point specified by this argument.
        
        Returns:
            float | str | bool: The optimal parameter value found by the experiment.
        """
        if node.is_refinement:
            # FIXME: the following doesn't allow for nodes to depend on multiple other nodes and it's awful, please fix.
            previous_experiment_data = list(self._calibration_graph.successors(node))[0].experiment_results
            node.sweep_interval = node.sweep_interval + previous_experiment_data
            """
            Note: I'm not sure this can always be handled like this: I'm taking the example from
            LabScripts/QuantumPainHackathon/calibrations/single_qb_full_cal.py as universal which I
            already know I'm gonna regret
            """
        if experiment_point is None:
        # Case when the experiment is started by 'calibrate': the experiment is run on the entire default sweep interval
            """
            Here this happens:
                1.Experiment is run
                2.Analysis function is called to fit data
                3.Data is plotted
                4.User is asked to approve plot
                    if user approves: return
                    else: go back to 1.
            """
            user_approves_plot = "n"
            while user_approves_plot == "n":
                # Compile and run the QProgram on the platform.
                node.experiment_results = self._platform.execute_qprogram(node.qprogram(drive_bus = "drive_bus", readout_bus = "readout_bus", sweep_values = node.sweep_interval))

                if analyze:
                    # Call the general analysis function with the appropriate model, or the custom one (no need to specify the model in this case, it will already be hardcoded).
                    optimal_parameter_value = node.analysis_function(results = node.experiment_results)

                # If the 'manual_check' option is activated for the node, show the plot and ask the user for approval.
                if node.manual_check:
                    #TODO: print plot
                    user_approves_plot = input("Do you want to repeat the experiment? (y/n): ").lower()
                else:
                    user_approves_plot = "y"
        
            return optimal_parameter_value
        
        # Case when the experiment is started by 'check_data': the experiment is run only in 1 point.
        #TODO: for now I just return the data of the experiment in the point, figure out the details when implementing check_data
        return self._platform.execute_qprogram(node.qprogram(node.qprogram(drive_bus = "drive_bus", readout_bus = "readout_bus", sweep_values = list(experiment_point))))

    def update_parameter(self, node: CalibrationNode, parameter_value: float | bool | str) -> None:
        """Update a parameter value in the platform. 
        If the node does not have an associated parameter, or the parameter attribute of the node is None,
        this function does nothing. That is because some nodes, such as those associated with the AllXY 
        experiment, don't compute the value of a parameter.

        Args:
            node (CalibrationNode): The node that contains the experiment that gives the optimal value of the parameter.
            parameter_value (float | bool | str): The optimal value of the parameter found by the experiment.
        """        
        if hasattr(node, "parameter")  and node.parameter is not None:
            self.platform.set_parameter(alias = node.parameter, value = parameter_value)
        
    def dependents(self, node: CalibrationNode):
        """Find the nodes that a node depends on. 
        In this graph, if an edge goes from node A to node B, then node A depends on node B. Thus the nodes that A depends on are its successors.
            
        Args:
            node (CalibrationNode): The nodes of which we need the dependencies

        Returns:
            list: The nodes that the argument node depends on
        """        
        return list(self._calibration_graph.successors(node))
    
    @property
    def calibration_graph(self):
        return self._calibration_graph

    @calibration_graph.setter
    def calibration_graph(self, new_calibration_graph):
        self._calibration_graph = new_calibration_graph
        
    @property
    def platform(self):
        return self._platform