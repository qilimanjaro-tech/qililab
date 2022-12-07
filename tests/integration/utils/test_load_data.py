"""Tests for the load function."""
import os
from pathlib import Path

from qililab import load
from qililab.experiment import Experiment
from qililab.result.results import Results

os.environ["DATA"] = str(Path(__file__).parent.parent.parent.parent / "examples" / "data")


def test_load_last_experiments():
    """Test load last experiments."""

    exp, results = load()
    assert isinstance(exp, Experiment)
    assert isinstance(results, Results)
