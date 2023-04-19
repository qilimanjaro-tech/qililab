""" Tests for LivePlot """

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from qiboconnection.api import API

from qililab.typings.enums import Parameter
from qililab.utils.live_plot import LivePlot
from qililab.utils.loop import Loop


@pytest.fixture(name="connection")
@patch("qiboconnection.api.API")
def fixture_create_mocked_connection(mock_api: MagicMock) -> API:
    """Create a mocked remote api connection
    Returns:
        API: Remote API mocked connection
    """
    return mock_api()


@pytest.fixture(name="one_loop")
def fixture_create_one_loop() -> Loop:
    """Create one loop
    Returns:
        Loop: created loop
    """
    return Loop(alias="rs_0", parameter=Parameter.LO_FREQUENCY, range=np.linspace(start=0.2, stop=1.2, num=10))


@pytest.fixture(name="another_loop")
def fixture_create_another_loop() -> Loop:
    """Create another loop
    Returns:
        Loop: created loop
    """
    return Loop(alias="X", parameter=Parameter.GAIN, range=np.linspace(start=100, stop=1000, num=50))


class TestLivePlot:
    """Unit tests checking the Experiment attributes and methods"""

    def test_live_plot_instance_no_connection(self, connection: API):
        """Test that the LivePlot instance is created correctly without any connection"""
        plot = LivePlot(connection=connection, num_schedules=1)
        assert isinstance(plot, LivePlot)

    def test_live_plot_ranges_with_one_loop(self, connection: API, one_loop: Loop):
        """test live plot ranges with one loop"""

        plot = LivePlot(connection=connection, loops=[one_loop], num_schedules=1)
        assert len(list(plot.x_iterator_ranges)) == len(one_loop.range)

    def test_live_plot_ranges_with_two_loops(self, connection: API, one_loop: Loop):
        """test live plot ranges with two loops"""
        loop = Loop(alias="X", parameter=Parameter.GAIN, range=np.linspace(start=100, stop=1000, num=50), loop=one_loop)
        plot = LivePlot(connection=connection, loops=[loop], num_schedules=1)
        assert len(list(plot.x_iterator_ranges)) == len(one_loop.range) * len(loop.range)
        assert len(list(plot.y_iterator_ranges)) == len(one_loop.range) * len(loop.range)

    def test_create_live_plot(self, connection: API):
        """Test the ``create_live_plot`` method."""
        plot = LivePlot(connection=connection, num_schedules=1)
        _ = plot.create_live_plot(title="test_name")
        connection.create_liveplot.assert_called()
