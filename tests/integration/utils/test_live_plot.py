""" Tests for LivePlot """

import time

import numpy as np
import pytest

from qililab.remote_connection.remote_api import RemoteAPI
from qililab.typings.enums import Parameter
from qililab.utils.live_plot import LivePlot
from qililab.utils.loop import Loop


@pytest.fixture(name="one_loop")
def fixture_create_one_loop() -> Loop:
    """Create one loop
    Returns:
        Loop: created loop
    """
    return Loop(parameter=Parameter.FREQUENCY, start=0, stop=1, num=100)


@pytest.fixture(name="another_loop")
def fixture_create_another_loop() -> Loop:
    """Create another loop
    Returns:
        Loop: created loop
    """
    return Loop(parameter=Parameter.GAIN, start=0, stop=0.1, num=10)


class TestLivePlot:
    """Unit tests checking the Experiment attributes and methods"""

    def test_live_plot_instance_no_connection(self, valid_remote_api: RemoteAPI):
        """Test that the LivePlot instance is created correctly without any connection"""
        plot = LivePlot(remote_api=valid_remote_api)
        assert isinstance(plot, LivePlot)

    def test_live_plot_ranges_with_one_loop(self, valid_remote_api: RemoteAPI, one_loop: Loop):
        """test live plot ranges with one loop"""

        plot = LivePlot(remote_api=valid_remote_api, loops=[one_loop])
        for x_value in one_loop.range:
            plot.send_points(value=x_value**2)
            time.sleep(0.1)

    def test_live_plot_ranges_with_two_loops(self, valid_remote_api: RemoteAPI, one_loop: Loop):
        """test live plot ranges with two loops"""
        loop = Loop(parameter=Parameter.GAIN, start=1, stop=11, num=10, loop=one_loop)
        plot = LivePlot(remote_api=valid_remote_api, loops=[loop])
        for x_value in loop.range:
            for y_value in one_loop.range:
                z_value = float(np.sin(x_value * y_value / (2 * np.pi)))
                plot.send_points(value=z_value)
