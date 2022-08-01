import copy

import pytest

from qililab.result import Results

from ...data import results_one_loops, results_two_loops


class TestsResults:
    """Test `Results` functionalities."""

    @pytest.mark.parametrize("results_dict", [results_one_loops, results_two_loops])
    def test_to_dict_method(self, results_dict: dict):
        """Tests to_dict() serialization of results"""
        results_origin = copy.deepcopy(results_dict)
        results_final = Results(**results_dict).to_dict()
        assert results_final == results_origin
