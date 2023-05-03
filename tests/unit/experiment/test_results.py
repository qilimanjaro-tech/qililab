""" Test Results """
import pandas as pd
import pytest

from qililab import Results

from ...data import results_one_loops, results_one_loops_empty, results_two_loops


class TestsResults:
    """Test `Results` functionalities."""

    @pytest.mark.parametrize("results_dict", [results_one_loops, results_two_loops])
    def test_from_dict_method(self, results_dict: dict):
        """Tests from_dict() serialization of results gives out a valid Results instance."""
        results = Results.from_dict(results_dict)
        assert isinstance(results, Results)

    @pytest.mark.parametrize("results_dict", [results_one_loops, results_two_loops])
    def test_to_dict_method(self, results_dict: dict):
        """Tests to_dict() serialization of results gives the intended dictionary."""
        results_final = Results.from_dict(results_dict).to_dict()
        assert results_final == results_dict

    @pytest.mark.parametrize("results_dict", [results_one_loops, results_two_loops, results_one_loops_empty])
    def test_acquisitions_method(self, results_dict: dict):
        """Tests to_dataframe() serialization of results gives a valid dataframe."""
        results = Results.from_dict(results_dict)
        acquisitions_df = results.acquisitions()
        assert isinstance(acquisitions_df, pd.DataFrame)

    @pytest.mark.parametrize("results_dict", [results_one_loops, results_two_loops, results_one_loops_empty])
    def test_probabilities_method(self, results_dict: dict):
        """Tests the probabilities method gives a valid dictionary."""
        results = Results.from_dict(results_dict)
        probabilities = results.probabilities()
        assert isinstance(probabilities, dict)

    @pytest.mark.parametrize("results_dict", [results_one_loops, results_two_loops, results_one_loops_empty])
    def test_single_probabilities_method(self, results_dict: dict):
        """Tests the probabilities method for each result inside the Results objects."""
        results = Results.from_dict(results_dict)
        for result in results.results:
            assert isinstance(result.probabilities(), dict)
