"""Tests for the ExecutionManager class."""
from qililab.execution import ExecutionManager


class TestExecutionManager:
    """Unit tests checking the Experiment attributes and methods."""

    def test_waveforms_method(self, execution_manager: ExecutionManager):
        """Test waveforms method."""
        for resolution in [0.01, 0.1, 1.0, 10.0]:
            execution_manager.waveforms_dict(resolution=resolution)

    def test_draw_method(self, execution_manager: ExecutionManager):
        """Test draw method."""
        for resolution in [0.01, 0.1, 1.0, 10.0]:
            execution_manager.draw(resolution=resolution)
