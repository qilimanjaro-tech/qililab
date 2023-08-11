""" Auxiliary methods """
from qililab.platform import Buses
from tests.data import Galadriel
from tests.test_utils import build_platform


def buses() -> Buses:
    """Load Buses.

    Returns:
        Buses: Instance of the Buses class.
    """
    platform = build_platform(Galadriel.runcard)
    return platform.buses
