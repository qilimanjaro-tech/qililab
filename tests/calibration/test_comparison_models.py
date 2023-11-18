"""Test for the comparison models."""
import json
import re

import numpy as np
import pytest

from qililab.calibration.comparison_models import (
    IQ_norm_root_mean_sqrt_error,
    norm_root_mean_sqrt_error,
    ssro_comparison_2D,
)


# Mocked export
def export_nb_outputs(outputs):
    """Mocked export_nb_outputs."""

    def ndarray_to_list(iter_):
        if isinstance(iter_, dict):
            for k, v in iter_.items():
                iter_[k] = ndarray_to_list(v)

        if isinstance(iter_, list):
            for idx, elem in enumerate(iter_):
                iter_[idx] = ndarray_to_list(elem)

        if isinstance(iter_, tuple):
            tuple_list = []
            for elem in iter_:
                tuple_list.append(ndarray_to_list(elem))
            return tuple(tuple_list)

        return iter_.tolist() if isinstance(iter_, np.ndarray) else iter_

    ndarray_to_list(outputs)
    return json.dumps(outputs)


def dump_load(outputs):
    """Make the two functions together."""
    return json.loads(export_nb_outputs(outputs))


# Global constants
basic_interval = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9])
basic_results = np.array([2, 4, 6, 8, 10, 12, 14, 16, 18])
changed_results = np.array([2, 5, 7, 8, 10, 12, 12, 16, 18])
very_changed_results = np.array([-2, 0, 16, 8, 0, 12, 10, 12, -18])

twoD_gaussians = np.array([2, 2, 3, 2, 5, 6, 2, 1, 1])
changed_twoD_gaussians = np.array([3, 4, 4, 3, 7, 7, 3, 2, 3])
very_changed_twoD_gaussians = np.array([10, -4, 1, 0, 7, -17, 30, 29, 3])


# fmt: off
long_interval = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9])
long_results = np.array([2, 4, 6, 8, 10, 12, 14, 16, 18, 2, 4, 6, 8, 10, 12, 14, 16, 18, 2, 4, 6, 8, 10, 12, 14, 16, 18, 2, 4, 6, 8, 10, 12, 14, 16, 18, 2, 4, 6, 8, 10, 12, 14, 16, 18, 2, 4, 6, 8, 10, 12, 14, 16, 18, 2, 4, 6, 8, 10, 12, 14, 16, 18, 2, 4, 6, 8, 10, 12, 14, 16, 18, 2, 4, 6, 8, 10, 12, 14, 16, 18, 2, 4, 6, 8, 10, 12, 14, 16, 18, 2, 4, 6, 8, 10, 12, 14, 16, 18, 2, 4, 6, 8, 10, 12, 14, 16, 18, 2, 4, 6, 8, 10, 12, 14, 16, 18, 2, 4, 6, 8, 10, 12, 14, 16, 18, 2, 4, 6, 8, 10, 12, 14, 16, 18])
long_changed_results = np.array([2, 5, 7, 8, 10, 12, 12, 16, 18, 2, 5, 7, 8, 10, 12, 12, 16, 18, 2, 5, 7, 8, 10, 12, 12, 16, 18, 2, 5, 7, 8, 10, 12, 12, 16, 18, 2, 5, 7, 8, 10, 12, 12, 16, 18, 2, 5, 7, 8, 10, 12, 12, 16, 18, 2, 5, 7, 8, 10, 12, 12, 16, 18, 2, 5, 7, 8, 10, 12, 12, 16, 18, 2, 5, 7, 8, 10, 12, 12, 16, 18, 2, 5, 7, 8, 10, 12, 12, 16, 18, 2, 5, 7, 8, 10, 12, 12, 16, 18, 2, 5, 7, 8, 10, 12, 12, 16, 18, 2, 5, 7, 8, 10, 12, 12, 16, 18, 2, 5, 7, 8, 10, 12, 12, 16, 18, 2, 5, 7, 8, 10, 12, 12, 16, 18])
long_very_changed_results = np.array([2, 0, -16, 8, 0, 12, 10, 12, 18, 2, 0, -16, 8, 0, 12, 10, -12, 18, 2, 0, 16, 8, 0, 12, 10, 12, 18, 2, 0, 16, 8, 0, 12, 10, 12, 18, 2, 0, 16, 8, 0, 12, 10, 12, 18, 2, 0, 16, 8, 0, 12, 10, 12, -18, 2, 0, 16, 8, 0, 12, 10, 12, 18, 2, 0, 16, 8, 0, 12, 10, 12, 18, 2, 0, 16, 8, 0, 12, 10, 12, 18, 2, 0, 16, 8, 0, 12, 10, 12, 18, 2, 0, 16, 8, 0, 12, 10, 12, 18, 2, 0, 16, 8, 0, 12, 10, -12, 18, 2, 0, 16, 8, 0, 12, 10, 12, 18, 2, 0, 16, 8, 0, 12, 10, -12, 18, 2, 0, 16, 8, 0, -12, 10, 12, 18])

long_twoD_gaussians = np.array([2, 2, 3, 2, 5, 6, 2, 1, 1, 2, 2, 3, 2, 5, 6, 2, 1, 1, 2, 2, 3, 2, 5, 6, 2, 1, 1, 2, 2, 3, 2, 5, 6, 2, 1, 1, 2, 2, 3, 2, 5, 6, 2, 1, 1, 2, 2, 3, 2, 5, 6, 2, 1, 1, 2, 2, 3, 2, 5, 6, 2, 1, 1, 2, 2, 3, 2, 5, 6, 2, 1, 1, 2, 2, 3, 2, 5, 6, 2, 1, 1, 2, 2, 3, 2, 5, 6, 2, 1, 1, 2, 2, 3, 2, 5, 6, 2, 1, 1, 2, 2, 3, 2, 5, 6, 2, 1, 1, 2, 2, 3, 2, 5, 6, 2, 1, 1, 2, 2, 3, 2, 5, 6, 2, 1, 1, 2, 2, 3, 2, 5, 6, 2, 1, 1])
long_changed_twoD_gaussians = np.array([3, 4, 4, 3, 7, 7, 3, 2, 3, 3, 4, 4, 3, 7, 7, 3, 2, 3, 3, 4, 4, 3, 7, 7, 3, 2, 3, 3, 4, 4, 3, 7, 7, 3, 2, 3, 3, 4, 4, 3, 7, 7, 3, 2, 3, 3, 4, 4, 3, 7, 7, 3, 2, 3, 3, 4, 4, 3, 7, 7, 3, 2, 3, 3, 4, 4, 3, 7, 7, 3, 2, 3, 3, 4, 4, 3, 7, 7, 3, 2, 3, 3, 4, 4, 3, 7, 7, 3, 2, 3, 3, 4, 4, 3, 7, 7, 3, 2, 3, 3, 4, 4, 3, 7, 7, 3, 2, 3, 3, 4, 4, 3, 7, 7, 3, 2, 3, 3, 4, 4, 3, 7, 7, 3, 2, 3, 3, 4, 4, 3, 7, 7, 3, 2, 3])
long_very_changed_twoD_gaussians = np.array([10, 4, 1, 0, 7, 17, -30, 29, 3, 10, 4, 1, 0, 7, 17, 30, 29, 3, -10, 4, 1, 0, 7, 17, 30, 29, 3, 10, 4, 1, 0, 7, 17, 30, 29, 3, 10, 4, 1, 0, 7, 17, 30, 29, 3, 10, 4, 1, 0, 7, 17, 30, 29, 3, -10, 4, 1, 0, 7, 17, 30, -29, 3, 10, 4, 1, 0, 7, 17, 30, 29, 3, 10, 4, 1, 0, 7, 17, 30, 29, 3, 10, 4, 1, 0, 7, 17, 30, 29, 3, 10, 4, 1, 0, 7, 17, 30, 29, 3, 10, 4, 1, 0, 7, 17, 30, 29, 3, 10, 4, 1, 0, 7, 17, 30, 29, 3, 10, 4, 1, 0, 7, -17, 30, 29, 3])
# fmt: on

obtained = dump_load({"sweep_interval": basic_interval, "results": basic_results, "fit": basic_results})
long_obtained = dump_load({"sweep_interval": long_interval, "results": long_results, "fit": long_results})


obtained_IQ = dump_load(
    {
        "sweep_interval": basic_interval,
        "results": np.array([basic_results, basic_results]),
        "fit": np.array([basic_results, basic_results]),
    }
)
obtained_2D = dump_load(
    {
        "sweep_interval": len(twoD_gaussians),
        "results": np.array([[twoD_gaussians, twoD_gaussians], [twoD_gaussians, twoD_gaussians]]),
        "fit": "",
    }
)

long_obtained_2D = dump_load(
    {
        "sweep_interval": len(long_twoD_gaussians),
        "results": np.array([[long_twoD_gaussians, long_twoD_gaussians], [long_twoD_gaussians, long_twoD_gaussians]]),
        "fit": np.array([long_twoD_gaussians, long_twoD_gaussians]),
    }
)


######################################################
#################### TEST 1D ERROR ###################
######################################################


class TestNormRootMeanSqrtError:
    """Test the norm_root_mean_sqrt_error comparison model."""

    @pytest.mark.parametrize(
        "comparison",
        [
            dump_load(
                {
                    "sweep_interval": np.array([basic_interval, basic_interval]),
                    "results": basic_results,
                    "fit": basic_results,
                }
            ),
            dump_load(
                {
                    "sweep_interval": basic_interval,
                    "results": np.array([changed_results, changed_results]),
                    "fit": basic_results,
                }
            ),
            dump_load(
                {
                    "sweep_interval": np.array([basic_interval, basic_interval]),
                    "results": np.array([changed_results, changed_results]),
                    "fit": np.array([changed_results, changed_results]),
                }
            ),
        ],
    )
    def test_norm_root_mean_sqrt_error_bad_shape(self, comparison):
        """Test bad shape comparisons."""
        with pytest.raises(
            ValueError,
            match="Incorrect 'check_parameters' shape for this notebook output.",
        ):
            norm_root_mean_sqrt_error(obtained=obtained, comparison=comparison)

    @pytest.mark.parametrize(
        "comparison",
        [
            dump_load({"results": basic_results, "fit": basic_results}),
            dump_load({"sweep_interval": basic_interval, "fit": basic_results}),
        ],
    )
    def test_norm_root_mean_sqrt_error_not_inside(self, comparison):
        """Test bad shape comparisons."""
        with pytest.raises(
            ValueError,
            match=re.escape(
                "Keys in the `check_parameters` are not 'sweep_interval', 'results' (and 'fit', optional), as is needed."
            ),
        ):
            norm_root_mean_sqrt_error(obtained=obtained, comparison=comparison)

    @pytest.mark.parametrize(
        "comparison",
        [
            dump_load({"sweep_interval": np.array([]), "results": np.array([]), "fit": np.array([])}),
            dump_load({"sweep_interval": np.array([]), "results": np.array([])}),
        ],
    )
    def test_norm_root_mean_sqrt_error_empty(self, comparison):
        """Test bad shape comparisons."""
        with pytest.raises(
            ValueError,
            match="Empty 'sweep_interval' or 'results' in `check_parameters`'s notebook output.",
        ):
            norm_root_mean_sqrt_error(obtained=obtained, comparison=comparison)

    @pytest.mark.parametrize(
        "output, comparison",
        [
            (
                "in_spec",
                dump_load({"sweep_interval": basic_interval, "results": basic_results}),
            ),
            (
                "out_of_spec",
                dump_load({"sweep_interval": basic_interval, "results": changed_results}),
            ),
            (
                "bad_data",
                dump_load({"sweep_interval": basic_interval, "results": very_changed_results}),
            ),
        ],
    )
    def test_norm_root_mean_sqrt_error_results(self, output, comparison):
        """Test a valid comparison with results."""
        error = norm_root_mean_sqrt_error(obtained, comparison)

        if output == "in_spec":
            assert error < 0.05

        elif output == "out_of_spec":
            assert 0.05 < error < 0.3

        elif output == "bad_data":
            assert 0.3 < error < 5.0

    @pytest.mark.parametrize(
        "output, comparison",
        [
            (
                "in_spec",
                dump_load({"sweep_interval": basic_interval, "results": basic_results, "fit": basic_results}),
            ),
            (
                "out_of_spec",
                dump_load({"sweep_interval": basic_interval, "results": basic_results, "fit": changed_results}),
            ),
            (
                "bad_data",
                dump_load({"sweep_interval": basic_interval, "results": basic_results, "fit": very_changed_results}),
            ),
        ],
    )
    def test_norm_root_mean_sqrt_error_fit(self, output, comparison):
        """Test a valid comparison with the fit."""
        error = norm_root_mean_sqrt_error(obtained, comparison)

        if output == "in_spec":
            assert error < 0.05

        elif output == "out_of_spec":
            assert 0.05 < error < 0.3

        elif output == "bad_data":
            assert 0.3 < error < 5.0

    @pytest.mark.parametrize(
        "output, comparison",
        [
            (
                "in_spec",
                dump_load({"sweep_interval": long_interval, "results": long_results, "fit": long_results}),
            ),
            (
                "out_of_spec",
                dump_load({"sweep_interval": long_interval, "results": long_results, "fit": long_changed_results}),
            ),
            (
                "bad_data",
                dump_load({"sweep_interval": long_interval, "results": long_results, "fit": long_very_changed_results}),
            ),
        ],
    )
    def test_norm_root_mean_sqrt_error_long(self, output, comparison):
        """Test a valid comparison with the long."""
        error = norm_root_mean_sqrt_error(long_obtained, comparison)

        if output == "in_spec":
            assert error < 0.05

        elif output == "out_of_spec":
            assert 0.05 < error < 0.3

        elif output == "bad_data":
            assert 0.3 < error < 5.0


######################################################
#################### TEST IQ ERROR ###################
######################################################


class TestIQNormRootMeanSqrtError:
    """Test the IQ_norm_root_mean_sqrt_error comparison model."""

    @pytest.mark.parametrize(
        "comparison",
        [
            dump_load(
                {
                    "sweep_interval": basic_interval,
                    "results": np.array([basic_results]),
                    "fit": np.array([basic_results, basic_results]),
                }
            ),
            dump_load(
                {
                    "sweep_interval": basic_interval,
                    "results": np.array([changed_results, changed_results]),
                    "fit": np.array([basic_results]),
                }
            ),
            dump_load(
                {
                    "sweep_interval": basic_interval,
                    "results": np.array([very_changed_results]),
                    "fit": np.array([basic_results]),
                }
            ),
        ],
    )
    def test_norm_root_mean_sqrt_error_bad_shape(self, comparison):
        """Test bad shape comparisons."""
        with pytest.raises(
            ValueError,
            match="Incorrect 'check_parameters' shape for this notebook output",
        ):
            norm_root_mean_sqrt_error(obtained=obtained, comparison=comparison)

    @pytest.mark.parametrize(
        "comparison",
        [
            dump_load(
                {"results": np.array([basic_results, basic_results]), "fit": np.array([basic_results, basic_results])}
            ),
            dump_load({"sweep_interval": basic_interval, "fit": np.array([basic_results, basic_results])}),
        ],
    )
    def test_norm_root_mean_sqrt_error_not_inside(self, comparison):
        """Test bad shape comparisons."""
        with pytest.raises(
            ValueError,
            match=re.escape(
                "Keys in the `check_parameters` are not 'sweep_interval', 'results' (and 'fit', optional), as is needed."
            ),
        ):
            norm_root_mean_sqrt_error(obtained=obtained, comparison=comparison)

    @pytest.mark.parametrize(
        "comparison",
        [
            dump_load(
                {
                    "sweep_interval": np.array([]),
                    "results": np.array([]),
                    "fit": np.array([]),
                }
            ),
            dump_load(
                {
                    "sweep_interval": np.array([]),
                    "results": np.array([]),
                }
            ),
        ],
    )
    def test_norm_root_mean_sqrt_error_empty(self, comparison):
        """Test bad shape comparisons."""
        with pytest.raises(
            ValueError,
            match="Empty 'sweep_interval' or 'results' in `check_parameters`'s notebook output.",
        ):
            norm_root_mean_sqrt_error(obtained=obtained, comparison=comparison)

    @pytest.mark.parametrize(
        "output, comparison_IQ",
        [
            (
                "in_spec",
                dump_load(
                    {
                        "sweep_interval": basic_interval,
                        "results": np.array([basic_results, basic_results]),
                    }
                ),
            ),
            (
                "out_of_spec",
                dump_load(
                    {
                        "sweep_interval": basic_interval,
                        "results": np.array([changed_results, changed_results]),
                    }
                ),
            ),
            (
                "bad_data",
                dump_load(
                    {
                        "sweep_interval": basic_interval,
                        "results": np.array([very_changed_results, very_changed_results]),
                    }
                ),
            ),
        ],
    )
    def test_IQ_norm_root_mean_sqrt_error_results(self, output, comparison_IQ):
        """Test a valid comparison with the results."""
        error = IQ_norm_root_mean_sqrt_error(obtained_IQ, comparison_IQ)

        if output == "in_spec":
            assert error < 0.05

        elif output == "out_of_spec":
            assert 0.05 < error < 0.3

        elif output == "bad_data":
            assert 0.3 < error < 5.0

    @pytest.mark.parametrize(
        "output, comparison_IQ",
        [
            (
                "in_spec",
                dump_load(
                    {
                        "sweep_interval": basic_interval,
                        "results": np.array([basic_results, basic_results]),
                        "fit": np.array([basic_results, basic_results]),
                    }
                ),
            ),
            (
                "out_of_spec",
                dump_load(
                    {
                        "sweep_interval": basic_interval,
                        "results": np.array([basic_results, basic_results]),
                        "fit": np.array([changed_results, changed_results]),
                    }
                ),
            ),
            (
                "bad_data",
                dump_load(
                    {
                        "sweep_interval": basic_interval,
                        "results": np.array([basic_results, basic_results]),
                        "fit": np.array([very_changed_results, very_changed_results]),
                    }
                ),
            ),
        ],
    )
    def test_IQ_norm_root_mean_sqrt_error_fit(self, output, comparison_IQ):
        """Test a valid comparison with the fit."""
        error = IQ_norm_root_mean_sqrt_error(obtained_IQ, comparison_IQ)

        if output == "in_spec":
            assert error < 0.05

        elif output == "out_of_spec":
            assert 0.05 < error < 0.3

        elif output == "bad_data":
            assert 0.3 < error < 5.0


######################################################
#################### TEST 2D ERROR ###################
######################################################


class TestSSROComparison2D:
    """Test the ssro_comparison_2D comparison model."""

    @pytest.mark.parametrize(
        "comparison",
        [
            dump_load(
                {
                    "sweep_interval": 2,
                    "results": np.array([twoD_gaussians, twoD_gaussians]),
                }
            ),
            dump_load(
                {
                    "sweep_interval": len(changed_twoD_gaussians),
                    "results": np.array([[changed_twoD_gaussians, changed_twoD_gaussians]]),
                }
            ),
            dump_load(
                {
                    "sweep_interval": len(changed_twoD_gaussians),
                    "results": np.array([changed_twoD_gaussians, changed_twoD_gaussians]),
                }
            ),
        ],
    )
    def test_ssro_comparison_2D_bad_shape(self, comparison):
        """Test bad shape comparisons."""
        with pytest.raises(
            ValueError,
            match="Incorrect 'check_parameters' shape for this notebook output.",
        ):
            ssro_comparison_2D(obtained=obtained_2D, comparison=comparison)

    @pytest.mark.parametrize(
        "comparison",
        [
            dump_load(
                {
                    "results": np.array([[twoD_gaussians, twoD_gaussians], [twoD_gaussians, twoD_gaussians]]),
                    "fit": "",
                }
            ),
            dump_load(
                {
                    "sweep_interval": len(twoD_gaussians),
                    "fit": np.array([[twoD_gaussians, twoD_gaussians], [twoD_gaussians, twoD_gaussians]]),
                }
            ),
        ],
    )
    def test_ssro_comparison_2D_not_inside(self, comparison):
        """Test bad shape comparisons."""
        with pytest.raises(
            ValueError,
            match="Keys in the `check_parameters` are not 'sweep_interval' and 'results', as is needed.",
        ):
            ssro_comparison_2D(obtained=obtained_2D, comparison=comparison)

    @pytest.mark.parametrize(
        "comparison",
        [
            dump_load(
                {
                    "sweep_interval": 0,
                    "results": np.array([[[], []], [[], []]]),
                    "fit": np.array([twoD_gaussians, twoD_gaussians]),
                }
            ),
            dump_load(
                {
                    "sweep_interval": 0,
                    "results": np.array([[[], []], [[], []]]),
                }
            ),
        ],
    )
    def test_ssro_comparison_2D_empty(self, comparison):
        """Test bad shape comparisons."""
        with pytest.raises(
            ValueError,
            match="Empty 'sweep_interval' or 'results' in `check_parameters`'s notebook output.",
        ):
            ssro_comparison_2D(obtained=obtained_2D, comparison=comparison)

    @pytest.mark.parametrize(
        "output, comparison_2D",
        [
            (
                "in_spec",
                dump_load(
                    {
                        "sweep_interval": len(twoD_gaussians),
                        "results": np.array([[twoD_gaussians, twoD_gaussians], [twoD_gaussians, twoD_gaussians]]),
                        "fit": np.array([[], []]),
                    }
                ),
            ),
            (
                "out_of_spec",
                dump_load(
                    {
                        "sweep_interval": len(changed_twoD_gaussians),
                        "results": np.array(
                            [
                                [changed_twoD_gaussians, changed_twoD_gaussians],
                                [changed_twoD_gaussians, changed_twoD_gaussians],
                            ]
                        ),
                    }
                ),
            ),
            (
                "bad_data",
                dump_load(
                    {
                        "sweep_interval": len(very_changed_twoD_gaussians),
                        "results": np.array(
                            [
                                [very_changed_twoD_gaussians, very_changed_twoD_gaussians],
                                [very_changed_twoD_gaussians, very_changed_twoD_gaussians],
                            ]
                        ),
                        "fit": np.array([[], []]),
                    }
                ),
            ),
        ],
    )
    def test_ssro_comparison_2D(self, output, comparison_2D):
        """Test a valid comparison."""
        error = ssro_comparison_2D(obtained_2D, comparison_2D)

        if output == "in_spec":
            assert error < 0.05

        elif output == "out_of_spec":
            assert 0.05 < error < 0.3

        elif output == "bad_data":
            assert 0.3 < error < 5.0

    @pytest.mark.parametrize(
        "output, comparison_2D",
        [
            (
                "in_spec",
                dump_load(
                    {
                        "sweep_interval": len(long_twoD_gaussians),
                        "results": np.array(
                            [[long_twoD_gaussians, long_twoD_gaussians], [long_twoD_gaussians, long_twoD_gaussians]]
                        ),
                        "fit": np.array([[], []]),
                    }
                ),
            ),
            (
                "out_of_spec",
                dump_load(
                    {
                        "sweep_interval": len(long_changed_twoD_gaussians),
                        "results": np.array(
                            [
                                [long_changed_twoD_gaussians, long_changed_twoD_gaussians],
                                [long_changed_twoD_gaussians, long_changed_twoD_gaussians],
                            ]
                        ),
                    }
                ),
            ),
            (
                "bad_data",
                dump_load(
                    {
                        "sweep_interval": len(long_very_changed_twoD_gaussians),
                        "results": np.array(
                            [
                                [long_very_changed_twoD_gaussians, long_very_changed_twoD_gaussians],
                                [long_very_changed_twoD_gaussians, long_very_changed_twoD_gaussians],
                            ]
                        ),
                    }
                ),
            ),
        ],
    )
    def test_ssro_comparison_2D_long(self, output, comparison_2D):
        """Test a valid comparison."""
        error = ssro_comparison_2D(long_obtained_2D, comparison_2D)

        if output == "in_spec":
            assert error < 0.05

        elif output == "out_of_spec":
            assert 0.05 < error < 0.3

        elif output == "bad_data":
            assert 0.3 < error < 5.0
