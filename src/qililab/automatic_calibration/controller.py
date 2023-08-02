import networkx as nx
from qililab.automatic_calibration.calibration_utils.experiment_factory import ExperimentFactory
from qililab.automatic_calibration.calibration_node import CalibrationNode
from qililab.platform.platform import Platform

#TODO: remove experiment_factory probably
class Controller:
    """Class that controls the automatic calibration sequence.

    Attributes:
        _calibration_graph (nx.DiGraph): The calibration graph. This is a directed graph where each node is a CalibrationNode object.
        _platform (Platform): The platform where the experiments will be run. See the Platform class for more information.
        _experiment_factory (ExperimentFactory): The factory object that is used to create experiments so they can be inserted into Experiment objects.
    """

    def __init__(self, platform: Platform, calibration_graph: nx.DiGraph = None):
        if calibration_graph is None:
            self._calibration_graph = nx.DiGraph()
        else:
            self._calibration_graph = calibration_graph
        # Note to future self: The calibration graph is initialized as an empty directed graph.
        # In methods that add a new node, make a check to see if the graph is still a DAG
        self._platform = platform
        self._experiment_factory = ExperimentFactory()

    @property
    def calibration_graph(self):
        return self._calibration_graph

    @property.setter
    def calibration_graph(self, new_calibration_graph):
        self._calibration_graph = new_calibration_graph

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
        # TODO: Verify what dependents are and in what order they are handled

        # Recursion over all the dependencies of the node
        for n in node.dependents:
            self.maintain(n)

        # check_state
        result = node.check_state()
        if result.success:
            return

        # check_data
        result = node.check_data()
        if result.in_spec:
            return
        elif result.bad_data:
            for n in node.dependents:
                self.diagnose(n)

        # calibrate
        result = node.calibrate()
        node.updateParameters(result)
        return

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
        result = node.check_data()

        # in spec case
        if result.in_spec:
            return False

        # bad data case
        if result.bad_data:
            recalibrated = [self.diagnose(n) for n in node.dependents]
        if not any(recalibrated):
            return False

        # calibrate
        result = node.calibrate()
        node.update_parameters(result)
        return True

    def run_calibration(self, node: CalibrationNode = None):
        """Run the calibration procedure starting from the given node.

        Args:
            node (CalibrationNode, optional): The node from which to start the calibration. When it is None it means we're in the root call.
                                         In that case we start from the highest level node in the calibration graph. 'maintain` will recursively
                                         calibrate all the lower level nodes.
        """
        if node is None:
            node = (
                CalibrationNode()
            )  # TODO: node = the highest level node in the calibration graph. Find it with a networkx function.

        self.maintain(node)
