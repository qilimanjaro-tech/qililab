""" Auxiliary methods """
from unittest.mock import patch

from qililab import build_platform
from qililab.platform import Buses
from tests.data import Galadriel


def buses() -> Buses:
    """Load Buses.

    Returns:
        Buses: Instance of the Buses class.
    """
    with patch("qililab.data_management.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.data_management.open") as mock_open:
            platform = build_platform(path="_")
            mock_load.assert_called()
            mock_open.assert_called()
    return platform.buses
