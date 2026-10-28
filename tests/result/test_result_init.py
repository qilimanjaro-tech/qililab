"""Test the lazy attribute loading in qililab.result's package __init__."""

import pytest

import qililab.result
from qililab.result.experiment_live_plot import ExperimentLivePlot


class TestResultLazyGetattr:
    """Unit tests for `qililab.result.__getattr__`."""

    def test_experiment_live_plot_resolves_lazily(self):
        """Test that `ExperimentLivePlot` is resolved on access and matches the real class."""
        assert qililab.result.ExperimentLivePlot is ExperimentLivePlot

    def test_from_import_resolves_lazily(self):
        """Test that `from qililab.result import ExperimentLivePlot` also resolves correctly."""
        from qililab.result import ExperimentLivePlot as ImportedExperimentLivePlot

        assert ImportedExperimentLivePlot is ExperimentLivePlot

    def test_unknown_attribute_raises_attribute_error(self):
        """Test that accessing an undefined attribute raises AttributeError."""
        with pytest.raises(AttributeError, match="has no attribute 'not_a_real_attribute'"):
            qililab.result.not_a_real_attribute
