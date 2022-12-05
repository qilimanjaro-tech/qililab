"""Tests for the BusesExecution class."""
from qililab.execution import ExecutionManager


class TestBusesExecution:
    """Unit tests checking the Experiment attributes and methods."""

    def test_waveforms_method(self, buses_execution: ExecutionManager):
        """Test waveforms method."""
        for resolution in [0.01, 0.1, 1.0, 10.0]:
            buses_execution.waveforms_dict(resolution=resolution)

    def test_draw_method(self, buses_execution: ExecutionManager):
        """Test draw method."""
        for resolution in [0.01, 0.1, 1.0, 10.0]:
            buses_execution.draw(resolution=resolution)
