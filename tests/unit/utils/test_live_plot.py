""" Tests for LivePlot """

import warnings
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
    return Loop(alias="rs_0", parameter=Parameter.LO_FREQUENCY, values=np.linspace(start=0.2, stop=1.2, num=10))


@pytest.fixture(name="another_loop")
def fixture_create_another_loop() -> Loop:
    """Create another loop
    Returns:
        Loop: created loop
    """
    return Loop(alias="X", parameter=Parameter.GAIN, values=np.linspace(start=100, stop=1000, num=50))


class TestLivePlot:
    """Unit tests checking the Experiment attributes and methods"""

    def test_live_plot_instance_no_connection(self, connection: API):
        """Test that the LivePlot instance is created correctly without any connection"""
        plot = LivePlot(connection=connection, num_schedules=10)
        assert isinstance(plot, LivePlot)

    def test_ranges_with_one_loop(self, connection: API, one_loop: Loop):
        """test live plot ranges with one loop"""

        plot = LivePlot(connection=connection, loops=[one_loop], num_schedules=1)
        assert len(list(plot.x_iterator)) == len(one_loop.values)

    def test_ranges_with_no_loops(self, connection: API):
        """Test the X and Y ranges when no loops are defined."""
        plot = LivePlot(connection=connection, num_schedules=7)
        assert np.allclose(list(plot.x_iterator), list(range(7)))

    def test_ranges_with_two_nested_loops(self, connection: API, one_loop: Loop):
        """test live plot ranges with two loops"""
        loop = Loop(
            alias="X", parameter=Parameter.GAIN, values=np.linspace(start=100, stop=1000, num=50), loop=one_loop
        )
        plot = LivePlot(connection=connection, loops=[loop], num_schedules=1)
        ranges = np.meshgrid(one_loop.values, loop.values)
        assert np.allclose(list(plot.x_iterator), ranges[0].flatten())
        assert np.allclose(list(plot.y_iterator), ranges[1].flatten())

    def test_ranges_with_two_parallel_loops(self, connection: API, one_loop: Loop):
        """test live plot ranges with two loops"""
        loop = Loop(alias="X", parameter=Parameter.GAIN, values=np.linspace(start=100, stop=1000, num=50))
        plot = LivePlot(connection=connection, loops=[loop, one_loop], num_schedules=1)
        assert np.allclose(list(plot.x_iterator), loop.values)

    def test_ranges_with_two_parallel_loops_and_multiple_sequences(self, connection: API, one_loop: Loop):
        """test live plot ranges with two loops"""
        loop = Loop(alias="X", parameter=Parameter.GAIN, values=np.linspace(start=100, stop=1000, num=50))
        plot = LivePlot(connection=connection, loops=[loop, one_loop], num_schedules=7)
        assert np.allclose(list(plot.x_iterator), list(range(7)))
        assert np.allclose(list(plot.y_iterator), loop.values)

    def test_ranges_with_two_nested_loops_and_multiple_sequences(self, connection: API, one_loop: Loop):
        """test live plot ranges with two loops"""
        loop = Loop(
            alias="X", parameter=Parameter.GAIN, values=np.linspace(start=100, stop=1000, num=50), loop=one_loop
        )
        plot = LivePlot(connection=connection, loops=[one_loop, loop], num_schedules=7)
        ranges = np.meshgrid(one_loop.values, loop.values)
        assert np.allclose(list(plot.x_iterator), ranges[0].flatten())
        assert np.allclose(list(plot.y_iterator), ranges[1].flatten())

    def test_3_nested_loops_raises_error(self, connection: API):
        """Test that instantiating a ``LivePlot`` class with 3 loops raises a warning."""
        loop3 = Loop(alias="X", parameter=Parameter.GAIN, values=np.linspace(start=100, stop=1000, num=50))
        loop2 = Loop(alias="X", parameter=Parameter.GAIN, values=np.linspace(start=100, stop=1000, num=50), loop=loop3)
        loop1 = Loop(alias="X", parameter=Parameter.GAIN, values=np.linspace(start=100, stop=1000, num=50), loop=loop2)
        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to al ways be triggered.
            warnings.simplefilter("always")
            plot = LivePlot(connection=connection, loops=[loop1], num_schedules=1)
            assert len(w) == 1
            assert issubclass(w[-1].category, UserWarning)
            assert (
                "The experiment contains 3 dimensions. Live plotting only supports 1D and 2D plots. The remaining dimensions won't be plotted"
                in str(w[-1].message)
            )
        ranges = np.meshgrid(loop2.values, loop1.values)
        assert np.allclose(list(plot.x_iterator), ranges[0].flatten())
        assert np.allclose(list(plot.y_iterator), ranges[1].flatten())

    def test_send_points_with_one_loop(self, connection: API):
        """Test the ``send_points`` method with a ``LivePlot`` that contains one loop."""
        loop = Loop(alias="X", parameter=Parameter.GAIN, values=np.linspace(start=100, stop=1000, num=50))
        plot = LivePlot(connection=connection, loops=[loop], num_schedules=1)
        plot.send_points(value=4)
        x_value = float(loop.values[0])
        connection.send_plot_points.assert_called_once_with(plot_id=plot.plot_id, x=x_value, y=4)

    def test_send_points_with_two_loops(self, connection: API):
        """Test the ``send_points`` method with a ``LivePlot`` that contains one loop."""
        loop2 = Loop(alias="X", parameter=Parameter.GAIN, values=np.linspace(start=100, stop=1000, num=50))
        loop = Loop(alias="X", parameter=Parameter.GAIN, values=np.linspace(start=100, stop=1000, num=50), loop=loop2)
        plot = LivePlot(connection=connection, loops=[loop], num_schedules=1)
        plot.send_points(value=4)
        x_value = float(loop.values[0])
        y_value = float(loop2.values[0])
        connection.send_plot_points.assert_called_once_with(plot_id=plot.plot_id, x=x_value, y=y_value, z=4)

    def test_send_all_points_of_a_plot_with_one_loop(self, connection: API):
        """Test calling the ``send_points`` multiple times until the iterators finish."""
        loop = Loop(alias="X", parameter=Parameter.GAIN, values=np.linspace(start=100, stop=1000, num=50))
        plot = LivePlot(connection=connection, loops=[loop], num_schedules=1)
        idx = 0
        while True:
            if idx == 50:
                with pytest.raises(StopIteration):
                    plot.send_points(value=5)
                break
            plot.send_points(value=5)
            idx += 1

    def test_send_all_points_of_a_plot_with_two_loops(self, connection: API):
        """Test calling the ``send_points`` multiple times until the iterators finish."""
        loop2 = Loop(alias="X", parameter=Parameter.GAIN, values=np.linspace(start=100, stop=1000, num=50))
        loop = Loop(alias="X", parameter=Parameter.GAIN, values=np.linspace(start=100, stop=1000, num=50), loop=loop2)
        plot = LivePlot(connection=connection, loops=[loop], num_schedules=1)
        idx = 0
        while True:
            if idx == 50 * 50:
                with pytest.raises(StopIteration):
                    plot.send_points(value=5)
                break
            plot.send_points(value=5)
            idx += 1

    def test_create_live_plot(self, connection: API):
        """Test the ``create_live_plot`` method."""
        plot = LivePlot(connection=connection, num_schedules=10)
        _ = plot.create_live_plot(title="test_name")
        connection.create_liveplot.assert_called()
