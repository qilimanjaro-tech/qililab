""" Tests for LivePlot """

import time

import numpy as np
import pytest
from qiboconnection.api import API, ConnectionConfiguration

from qililab.typings.enums import Parameter
from qililab.utils.live_plot import LivePlot
from qililab.utils.loop import Loop


@pytest.fixture(name="valid_api")
def fixture_create_valid_api() -> API:
    """Create a valid remote api connection
    Returns:
        RemoteAPI: Remote API connection
    """
    configuration = ConnectionConfiguration(
        username="write-a-valid-user",
        api_key="write-a-valid-key",
    )
    return API(configuration=configuration)


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
    return Loop(alias="X", parameter=Parameter.GAIN, range=np.linspace(start=0, stop=0.1, num=10))


class TestLivePlot:
    """Unit tests checking the Experiment attributes and methods"""

    def test_live_plot_instance_no_connection(self, valid_api: API):
        """Test that the LivePlot instance is created correctly without any connection"""
        plot = LivePlot(connection=valid_api, num_schedules=1)
        assert isinstance(plot, LivePlot)

    def test_live_plot_ranges_with_one_loop(self, valid_api: API, one_loop: Loop):
        """test live plot ranges with one loop"""

        plot = LivePlot(connection=valid_api, loops=[one_loop], num_schedules=1)
        for x_value in one_loop.range:
            plot.send_points(value=x_value**2)
            time.sleep(0.1)

    def test_live_plot_ranges_with_two_loops(self, valid_api: API, one_loop: Loop):
        """test live plot ranges with two loops"""
        loop = Loop(alias="X", parameter=Parameter.GAIN, range=np.linspace(start=1, stop=11, num=10), loop=one_loop)
        plot = LivePlot(connection=valid_api, loops=[loop], num_schedules=1)
        for x_value in loop.range:
            for y_value in one_loop.range:
                z_value = float(np.sin(x_value * y_value / (2 * np.pi)))
                plot.send_points(value=z_value)
