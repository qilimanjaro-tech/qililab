""" Tests for LivePlot """

import pytest

from qililab.remote_connection.remote_api import RemoteAPI
from qililab.typings.enums import Parameter
from qililab.utils.live_plot import LivePlot
from qililab.utils.loop import Loop


@pytest.fixture(name="remote_api_no_connection")
def fixture_create_mocked_remote_api_no_connection() -> RemoteAPI:
    """Create a mocked remote api connection
    Returns:
        RemoteAPI: Remote API mocked connection
    """
    return RemoteAPI()


@pytest.fixture(name="one_loop")
def fixture_create_one_loop() -> Loop:
    """Create one loop
    Returns:
        Loop: created loop
    """
    return Loop(parameter=Parameter.FREQUENCY, start=0.2, stop=1.2, num=10)


@pytest.fixture(name="another_loop")
def fixture_create_another_loop() -> Loop:
    """Create another loop
    Returns:
        Loop: created loop
    """
    return Loop(parameter=Parameter.GAIN, start=100, stop=1000, num=50)


class TestLivePlot:
    """Unit tests checking the Experiment attributes and methods"""

    def test_live_plot_instance_no_connection(self, remote_api_no_connection: RemoteAPI):
        """Test that the LivePlot instance is created correctly without any connection"""
        plot = LivePlot(remote_api=remote_api_no_connection)
        assert isinstance(plot, LivePlot)

    def test_live_plot_ranges_with_one_loop(self, remote_api_no_connection: RemoteAPI, one_loop: Loop):
        """test live plot ranges with one loop"""

        plot = LivePlot(remote_api=remote_api_no_connection, loop=one_loop)
        assert len(list(plot.x_iterator_ranges)) == len(one_loop.range)

    def test_live_plot_ranges_with_two_loops(self, remote_api_no_connection: RemoteAPI, one_loop: Loop):
        """test live plot ranges with two loops"""
        loop = Loop(parameter=Parameter.GAIN, start=100, stop=1000, num=50, loop=one_loop)
        plot = LivePlot(remote_api=remote_api_no_connection, loop=loop)
        assert len(list(plot.x_iterator_ranges)) == len(one_loop.range) * len(loop.range)
        assert len(list(plot.y_iterator_ranges)) == len(one_loop.range) * len(loop.range)
