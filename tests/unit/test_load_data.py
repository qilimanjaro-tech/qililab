"""Tests for the load function."""
from qililab.result import Results
from qililab.utils import Loop


def test_load_function(loaded_results: Results):
    """Test the load function."""
    assert isinstance(loaded_results.loop, Loop)
