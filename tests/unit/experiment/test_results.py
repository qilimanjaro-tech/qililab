from copy import deepcopy

import pytest

from qililab import Results

from ...data import results_one_loops, results_two_loops


class TestsResults:
    """Test `Results` functionalities."""

    @pytest.mark.parametrize("results_dict", deepcopy([results_one_loops, results_two_loops]))
    def test_from_dict_method(self, results_dict: dict):
        """Tests from_dict() serialization of results gives out a valid Results instance."""
        results = Results.from_dict(results_dict)
        assert isinstance(results, Results)

    @pytest.mark.parametrize("results_dict", deepcopy([results_one_loops, results_two_loops]))
    def test_to_dict_method(self, results_dict: dict):
        """Tests to_dict() serialization of results gives the intended dictionary."""
        results_original = deepcopy(results_dict)
        results_final = Results.from_dict(results_dict).to_dict()
        assert results_final == results_original
