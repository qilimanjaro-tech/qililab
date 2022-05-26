"""Tests for the defined experiments."""
from unittest.mock import MagicMock, patch

from qiboconnection.api import API

from qililab.experiment.cavity_spectroscopy import cavity_spectroscopy
from qililab.experiment.qubit_spectroscopy import qubit_spectroscopy

from ...conftest import mock_instruments


class TestExperiments:
    """Unit tests checking the defined experiments."""

    @patch("qililab.instruments.qblox.qblox_pulsar.Pulsar", autospec=True)
    @patch("qililab.instruments.rohde_schwarz.sgs100a.RohdeSchwarzSGS100A", autospec=True)
    def test_cavity_and_qubit_spectroscopy(self, mock_rs: MagicMock, mock_pulsar: MagicMock):
        """Test execute method with simulated qubit."""
        mock_instruments(mock_rs=mock_rs, mock_pulsar=mock_pulsar)
        connection = MagicMock(name="API", spec=API, autospec=True)
        connection.create_liveplot.return_value = 0
        cavity_spectroscopy(connection=connection)
        qubit_spectroscopy(connection=connection)
        connection.create_liveplot.assert_called()
        connection.send_plot_points.assert_called()
        mock_rs.assert_called()
        mock_pulsar.assert_called()
