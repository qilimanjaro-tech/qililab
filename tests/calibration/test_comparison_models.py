"""Test for the comparison models."""
import pytest

from qililab.calibration.comparison_models import (
    IQ_norm_root_mean_sqrt_error,
    norm_root_mean_sqrt_error,
    scipy_ks_2_samples_error,
    ssro_comparison_2D,
)

# Global constants
basic_interval = [1, 2, 3, 4, 5, 6, 7, 8, 9]
basic_results = [2, 4, 6, 8, 10, 12, 14, 16, 18]
changed_results = [2, 5, 7, 8, 10, 12, 12, 16, 18]
very_changed_results = [2, 0, 16, 8, 0, 12, 10, 12, 18]
obtained = {"sweep_interval": basic_interval, "results": basic_results, "fit": basic_results}
obtained_IQ = {
    "sweep_interval": basic_interval,
    "results": [basic_results, basic_results],
    "fit": [basic_results, basic_results],
}
obtained_2D = {
    "sweep_interval": [basic_results, basic_results],
    "results": [basic_results, basic_results],
    "fit": [basic_results, basic_results],
}


######################################################
#################### TEST 1D ERROR ###################
######################################################


class TestNormRootMeanSqrtError:
    """Test the norm_root_mean_sqrt_error comparison model."""

    @pytest.mark.parametrize(
        "comparison",
        [
            {"sweep_interval": [basic_interval, basic_interval], "results": basic_results, "fit": basic_results},
            {"sweep_interval": basic_interval, "results": [changed_results, changed_results], "fit": basic_results},
            {
                "sweep_interval": [basic_interval, basic_interval],
                "results": [changed_results, changed_results],
                "fit": [changed_results, changed_results],
            },
        ],
    )
    def test_norm_root_mean_sqrt_error_bad_shape(self, comparison):
        """Test bad shape comparisons."""
        with pytest.raises(
            ValueError,
            match="Incorrect 'results' shape for this comparison model.",
        ):
            norm_root_mean_sqrt_error(obtained=obtained, comparison=comparison, fit=False)

    @pytest.mark.parametrize(
        "comparison",
        [
            {"results": basic_results, "fit": basic_results},
            {"sweep_interval": basic_interval, "fit": basic_results},
            {"sweep_interval": basic_interval, "results": changed_results},
        ],
    )
    def test_norm_root_mean_sqrt_error_not_inside(self, comparison):
        """Test bad shape comparisons."""
        with pytest.raises(
            ValueError,
            match="Keys in the `check_parameters` are not 'sweep_interval', 'results' and 'fit', as is need in for the comparison models.",
        ):
            norm_root_mean_sqrt_error(obtained=obtained, comparison=comparison, fit=False)

    @pytest.mark.parametrize(
        "comparison",
        [
            {"sweep_interval": [], "results": basic_results, "fit": basic_results},
            {"sweep_interval": basic_interval, "results": [], "fit": basic_results},
            {"sweep_interval": basic_interval, "results": basic_results, "fit": []},
        ],
    )
    def test_norm_root_mean_sqrt_error_empty(self, comparison):
        """Test bad shape comparisons."""
        with pytest.raises(
            ValueError,
            match="Empty 'sweep_interval', 'results' or 'fit' in  `check_parameters`. They are needed for the comparison models.",
        ):
            norm_root_mean_sqrt_error(obtained=obtained, comparison=comparison, fit=False)

    @pytest.mark.parametrize(
        "output, comparison",
        [
            ("in_spec", {"sweep_interval": basic_interval, "results": basic_results, "fit": basic_results}),
            ("out_of_spec", {"sweep_interval": basic_interval, "results": changed_results, "fit": basic_results}),
            ("bad_data", {"sweep_interval": basic_interval, "results": very_changed_results, "fit": basic_results}),
        ],
    )
    def test_norm_root_mean_sqrt_error_results(self, output, comparison):
        """Test a valid comparison with results."""
        error = norm_root_mean_sqrt_error(obtained, comparison, fit=False)

        if output == "in_spec":
            assert error < 0.0001

        elif output == "out_of_spec":
            assert 0.01 < error < 0.1

        elif output == "bad_data":
            assert 0.1 < error < 1.0

    @pytest.mark.parametrize(
        "output, comparison",
        [
            ("in_spec", {"sweep_interval": basic_interval, "results": basic_results, "fit": basic_results}),
            ("out_of_spec", {"sweep_interval": basic_interval, "results": basic_results, "fit": changed_results}),
            ("bad_data", {"sweep_interval": basic_interval, "results": basic_results, "fit": very_changed_results}),
        ],
    )
    def test_norm_root_mean_sqrt_error_fit(self, output, comparison):
        """Test a valid comparison with the fit."""
        error = norm_root_mean_sqrt_error(obtained, comparison)

        if output == "in_spec":
            assert error < 0.0001

        elif output == "out_of_spec":
            assert 0.01 < error < 0.1

        elif output == "bad_data":
            assert 0.1 < error < 1.0


######################################################
#################### TEST IQ ERROR ###################
######################################################


class TestIQNormRootMeanSqrtError:
    """Test the IQ_norm_root_mean_sqrt_error comparison model."""

    @pytest.mark.parametrize(
        "comparison",
        [
            {"sweep_interval": basic_interval, "results": [basic_results], "fit": [basic_results, basic_results]},
            {"sweep_interval": basic_interval, "results": [changed_results, changed_results], "fit": [basic_results]},
            {"sweep_interval": basic_interval, "results": [very_changed_results], "fit": [basic_results]},
        ],
    )
    def test_norm_root_mean_sqrt_error_bad_shape(self, comparison):
        """Test bad shape comparisons."""
        with pytest.raises(
            ValueError,
            match="Incorrect 'results' shape for this comparison model.",
        ):
            norm_root_mean_sqrt_error(obtained=obtained, comparison=comparison, fit=False)

    @pytest.mark.parametrize(
        "comparison",
        [
            {"results": [basic_results, basic_results], "fit": [basic_results, basic_results]},
            {"sweep_interval": basic_interval, "fit": [basic_results, basic_results]},
            {"sweep_interval": basic_interval, "results": [very_changed_results, very_changed_results]},
        ],
    )
    def test_norm_root_mean_sqrt_error_not_inside(self, comparison):
        """Test bad shape comparisons."""
        with pytest.raises(
            ValueError,
            match="Keys in the `check_parameters` are not 'sweep_interval', 'results' and 'fit', as is need in for the comparison models.",
        ):
            norm_root_mean_sqrt_error(obtained=obtained, comparison=comparison, fit=False)

    @pytest.mark.parametrize(
        "comparison",
        [
            {"sweep_interval": [], "results": [basic_results, basic_results], "fit": [basic_results, basic_results]},
            {"sweep_interval": basic_interval, "results": [], "fit": [basic_results, basic_results]},
            {"sweep_interval": basic_interval, "results": [very_changed_results, very_changed_results], "fit": []},
        ],
    )
    def test_norm_root_mean_sqrt_error_empty(self, comparison):
        """Test bad shape comparisons."""
        with pytest.raises(
            ValueError,
            match="Empty 'sweep_interval', 'results' or 'fit' in  `check_parameters`. They are needed for the comparison models.",
        ):
            norm_root_mean_sqrt_error(obtained=obtained, comparison=comparison, fit=False)

    @pytest.mark.parametrize(
        "output, comparison_IQ",
        [
            (
                "in_spec",
                {
                    "sweep_interval": basic_interval,
                    "results": [basic_results, basic_results],
                    "fit": [basic_results, basic_results],
                },
            ),
            (
                "out_of_spec",
                {
                    "sweep_interval": basic_interval,
                    "results": [changed_results, changed_results],
                    "fit": [basic_results, basic_results],
                },
            ),
            (
                "bad_data",
                {
                    "sweep_interval": basic_interval,
                    "results": [very_changed_results, very_changed_results],
                    "fit": [basic_results, basic_results],
                },
            ),
        ],
    )
    def test_IQ_norm_root_mean_sqrt_error_results(self, output, comparison_IQ):
        """Test a valid comparison with the results."""
        error = IQ_norm_root_mean_sqrt_error(obtained_IQ, comparison_IQ, fit=False)

        if output == "in_spec":
            assert error < 0.0001

        elif output == "out_of_spec":
            assert 0.01 < error < 0.1

        elif output == "bad_data":
            assert 0.1 < error < 1.0

    @pytest.mark.parametrize(
        "output, comparison_IQ",
        [
            (
                "in_spec",
                {
                    "sweep_interval": basic_interval,
                    "results": [basic_results, basic_results],
                    "fit": [basic_results, basic_results],
                },
            ),
            (
                "out_of_spec",
                {
                    "sweep_interval": basic_interval,
                    "results": [basic_results, basic_results],
                    "fit": [changed_results, changed_results],
                },
            ),
            (
                "bad_data",
                {
                    "sweep_interval": basic_interval,
                    "results": [basic_results, basic_results],
                    "fit": [very_changed_results, very_changed_results],
                },
            ),
        ],
    )
    def test_IQ_norm_root_mean_sqrt_error_fit(self, output, comparison_IQ):
        """Test a valid comparison with the fit."""
        error = IQ_norm_root_mean_sqrt_error(obtained_IQ, comparison_IQ)

        if output == "in_spec":
            assert error < 0.0001

        elif output == "out_of_spec":
            assert 0.01 < error < 0.1

        elif output == "bad_data":
            assert 0.1 < error < 1.0


######################################################
#################### TEST 2D ERROR ###################
######################################################


class TestSSROComparison2D:
    """Test the ssro_comparison_2D comparison model."""

    @pytest.mark.parametrize(
        "comparison",
        [
            {
                "sweep_interval": [basic_results, basic_results],
                "results": [basic_results],
                "fit": [basic_results, basic_results],
            },
            {
                "sweep_interval": [basic_results, basic_results],
                "results": [changed_results, changed_results],
                "fit": [basic_results],
            },
            {
                "sweep_interval": [basic_results, basic_results],
                "results": [very_changed_results],
                "fit": [basic_results],
            },
        ],
    )
    def test_ssro_comparison_2D_bad_shape(self, comparison):
        """Test bad shape comparisons."""
        with pytest.raises(
            ValueError,
            match="Incorrect 'results' shape for this comparison model.",
        ):
            ssro_comparison_2D(obtained=obtained, comparison=comparison, fit=False)

    @pytest.mark.parametrize(
        "comparison",
        [
            {"results": [basic_results, basic_results], "fit": [basic_results, basic_results]},
            {"sweep_interval": [basic_results, basic_results], "fit": [basic_results, basic_results]},
            {"sweep_interval": [basic_results, basic_results], "results": [very_changed_results, very_changed_results]},
        ],
    )
    def test_ssro_comparison_2D_not_inside(self, comparison):
        """Test bad shape comparisons."""
        with pytest.raises(
            ValueError,
            match="Keys in the `check_parameters` are not 'sweep_interval', 'results' and 'fit', as is need in for the comparison models.",
        ):
            ssro_comparison_2D(obtained=obtained, comparison=comparison, fit=False)

    @pytest.mark.parametrize(
        "comparison",
        [
            {"sweep_interval": [], "results": [basic_results, basic_results], "fit": [basic_results, basic_results]},
            {"sweep_interval": [basic_results, basic_results], "results": [], "fit": [basic_results, basic_results]},
            {
                "sweep_interval": [basic_results, basic_results],
                "results": [very_changed_results, very_changed_results],
                "fit": [],
            },
        ],
    )
    def test_ssro_comparison_2D_empty(self, comparison):
        """Test bad shape comparisons."""
        with pytest.raises(
            ValueError,
            match="Empty 'sweep_interval', 'results' or 'fit' in  `check_parameters`. They are needed for the comparison models.",
        ):
            ssro_comparison_2D(obtained=obtained, comparison=comparison, fit=False)

    @pytest.mark.parametrize(
        "output, comparison_2D",
        [
            (
                "in_spec",
                {
                    "sweep_interval": [basic_results, basic_results],
                    "results": [basic_results, basic_results],
                    "fit": [[], []],
                },
            ),
            (
                "out_of_spec",
                {
                    "sweep_interval": [changed_results, changed_results],
                    "results": [changed_results, changed_results],
                    "fit": [[], []],
                },
            ),
            (
                "bad_data",
                {
                    "sweep_interval": [very_changed_results, very_changed_results],
                    "results": [very_changed_results, very_changed_results],
                    "fit": [[], []],
                },
            ),
        ],
    )
    def test_ssro_comparison_2D(self, output, comparison_2D):
        """Test a valid comparison."""
        error = ssro_comparison_2D(obtained_2D, comparison_2D)
        error2 = ssro_comparison_2D(obtained_2D, comparison_2D, fit=False)

        if output == "in_spec":
            assert error == error2 < 0.0001

        elif output == "out_of_spec":
            assert 0.005 < error == error2 < 0.1

        elif output == "bad_data":
            assert 0.1 < error == error2 < 15.0
