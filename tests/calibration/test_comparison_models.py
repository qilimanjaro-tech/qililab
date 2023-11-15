"""Test for the comparison models."""
import json

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


# Global constants
basic_interval = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9])
basic_results = np.array([2, 4, 6, 8, 10, 12, 14, 16, 18])
changed_results = np.array([2, 5, 7, 8, 10, 12, 12, 16, 18])
very_changed_results = np.array([2, 0, 16, 8, 0, 12, 10, 12, 18])

long_interval = np.array(
    [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
    ]
)
long_results = np.array(
    [
        2,
        4,
        6,
        8,
        10,
        12,
        14,
        16,
        18,
        2,
        4,
        6,
        8,
        10,
        12,
        14,
        16,
        18,
        2,
        4,
        6,
        8,
        10,
        12,
        14,
        16,
        18,
        2,
        4,
        6,
        8,
        10,
        12,
        14,
        16,
        18,
        2,
        4,
        6,
        8,
        10,
        12,
        14,
        16,
        18,
        2,
        4,
        6,
        8,
        10,
        12,
        14,
        16,
        18,
        2,
        4,
        6,
        8,
        10,
        12,
        14,
        16,
        18,
        2,
        4,
        6,
        8,
        10,
        12,
        14,
        16,
        18,
        2,
        4,
        6,
        8,
        10,
        12,
        14,
        16,
        18,
        2,
        4,
        6,
        8,
        10,
        12,
        14,
        16,
        18,
        2,
        4,
        6,
        8,
        10,
        12,
        14,
        16,
        18,
        2,
        4,
        6,
        8,
        10,
        12,
        14,
        16,
        18,
        2,
        4,
        6,
        8,
        10,
        12,
        14,
        16,
        18,
        2,
        4,
        6,
        8,
        10,
        12,
        14,
        16,
        18,
        2,
        4,
        6,
        8,
        10,
        12,
        14,
        16,
        18,
    ]
)
long_changed_results = np.array(
    [
        2,
        5,
        7,
        8,
        10,
        12,
        12,
        16,
        18,
        2,
        5,
        7,
        8,
        10,
        12,
        12,
        16,
        18,
        2,
        5,
        7,
        8,
        10,
        12,
        12,
        16,
        18,
        2,
        5,
        7,
        8,
        10,
        12,
        12,
        16,
        18,
        2,
        5,
        7,
        8,
        10,
        12,
        12,
        16,
        18,
        2,
        5,
        7,
        8,
        10,
        12,
        12,
        16,
        18,
        2,
        5,
        7,
        8,
        10,
        12,
        12,
        16,
        18,
        2,
        5,
        7,
        8,
        10,
        12,
        12,
        16,
        18,
        2,
        5,
        7,
        8,
        10,
        12,
        12,
        16,
        18,
        2,
        5,
        7,
        8,
        10,
        12,
        12,
        16,
        18,
        2,
        5,
        7,
        8,
        10,
        12,
        12,
        16,
        18,
        2,
        5,
        7,
        8,
        10,
        12,
        12,
        16,
        18,
        2,
        5,
        7,
        8,
        10,
        12,
        12,
        16,
        18,
        2,
        5,
        7,
        8,
        10,
        12,
        12,
        16,
        18,
        2,
        5,
        7,
        8,
        10,
        12,
        12,
        16,
        18,
    ]
)
long_very_changed_results = np.array(
    [
        2,
        0,
        16,
        8,
        0,
        12,
        10,
        12,
        18,
        2,
        0,
        16,
        8,
        0,
        12,
        10,
        12,
        18,
        2,
        0,
        16,
        8,
        0,
        12,
        10,
        12,
        18,
        2,
        0,
        16,
        8,
        0,
        12,
        10,
        12,
        18,
        2,
        0,
        16,
        8,
        0,
        12,
        10,
        12,
        18,
        2,
        0,
        16,
        8,
        0,
        12,
        10,
        12,
        18,
        2,
        0,
        16,
        8,
        0,
        12,
        10,
        12,
        18,
        2,
        0,
        16,
        8,
        0,
        12,
        10,
        12,
        18,
        2,
        0,
        16,
        8,
        0,
        12,
        10,
        12,
        18,
        2,
        0,
        16,
        8,
        0,
        12,
        10,
        12,
        18,
        2,
        0,
        16,
        8,
        0,
        12,
        10,
        12,
        18,
        2,
        0,
        16,
        8,
        0,
        12,
        10,
        12,
        18,
        2,
        0,
        16,
        8,
        0,
        12,
        10,
        12,
        18,
        2,
        0,
        16,
        8,
        0,
        12,
        10,
        12,
        18,
        2,
        0,
        16,
        8,
        0,
        12,
        10,
        12,
        18,
    ]
)


obtained = json.loads(
    export_nb_outputs({"sweep_interval": basic_interval, "results": basic_results, "fit": basic_results})
)
long_obtained = obtained = json.loads(
    export_nb_outputs({"sweep_interval": long_interval, "results": long_results, "fit": long_results})
)

obtained_IQ = json.loads(
    export_nb_outputs(
        {
            "sweep_interval": basic_interval,
            "results": np.array([basic_results, basic_results]),
            "fit": np.array([basic_results, basic_results]),
        }
    )
)
obtained_2D = json.loads(
    export_nb_outputs(
        {
            "sweep_interval": np.array([basic_results, basic_results]),
            "results": np.array([basic_results, basic_results]),
            "fit": np.array([basic_results, basic_results]),
        }
    )
)


######################################################
#################### TEST 1D ERROR ###################
######################################################


class TestNormRootMeanSqrtError:
    """Test the norm_root_mean_sqrt_error comparison model."""

    @pytest.mark.parametrize(
        "comparison",
        [
            json.loads(
                export_nb_outputs(
                    {
                        "sweep_interval": np.array([basic_interval, basic_interval]),
                        "results": basic_results,
                        "fit": basic_results,
                    }
                )
            ),
            json.loads(
                export_nb_outputs(
                    {
                        "sweep_interval": basic_interval,
                        "results": [changed_results, changed_results],
                        "fit": basic_results,
                    }
                )
            ),
            json.loads(
                export_nb_outputs(
                    {
                        "sweep_interval": [basic_interval, basic_interval],
                        "results": [changed_results, changed_results],
                        "fit": [changed_results, changed_results],
                    }
                )
            ),
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
            json.loads(export_nb_outputs({"results": basic_results, "fit": basic_results})),
            json.loads(export_nb_outputs({"sweep_interval": basic_interval, "fit": basic_results})),
            json.loads(export_nb_outputs({"sweep_interval": basic_interval, "results": changed_results})),
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
            json.loads(export_nb_outputs({"sweep_interval": [], "results": basic_results, "fit": basic_results})),
            json.loads(export_nb_outputs({"sweep_interval": basic_interval, "results": [], "fit": basic_results})),
            json.loads(export_nb_outputs({"sweep_interval": basic_interval, "results": basic_results, "fit": []})),
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
            (
                "in_spec",
                json.loads(
                    export_nb_outputs(
                        {"sweep_interval": basic_interval, "results": basic_results, "fit": basic_results}
                    )
                ),
            ),
            (
                "out_of_spec",
                json.loads(
                    export_nb_outputs(
                        {"sweep_interval": basic_interval, "results": changed_results, "fit": basic_results}
                    )
                ),
            ),
            (
                "bad_data",
                json.loads(
                    export_nb_outputs(
                        {"sweep_interval": basic_interval, "results": very_changed_results, "fit": basic_results}
                    )
                ),
            ),
        ],
    )
    def test_norm_root_mean_sqrt_error_results(self, output, comparison):
        """Test a valid comparison with results."""
        error = norm_root_mean_sqrt_error(obtained, comparison, fit=False)

        if output == "in_spec":
            assert error < 0.05

        elif output == "out_of_spec":
            assert 0.05 < error < 0.3

        elif output == "bad_data":
            assert 0.3 < error < 1.0

    @pytest.mark.parametrize(
        "output, comparison",
        [
            (
                "in_spec",
                json.loads(
                    export_nb_outputs(
                        {"sweep_interval": basic_interval, "results": basic_results, "fit": basic_results}
                    )
                ),
            ),
            (
                "out_of_spec",
                json.loads(
                    export_nb_outputs(
                        {"sweep_interval": basic_interval, "results": basic_results, "fit": changed_results}
                    )
                ),
            ),
            (
                "bad_data",
                json.loads(
                    export_nb_outputs(
                        {"sweep_interval": basic_interval, "results": basic_results, "fit": very_changed_results}
                    )
                ),
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
            assert 0.3 < error < 1.0

    @pytest.mark.parametrize(
        "output, comparison",
        [
            (
                "in_spec",
                json.loads(
                    export_nb_outputs({"sweep_interval": long_interval, "results": long_results, "fit": long_results})
                ),
            ),
            (
                "out_of_spec",
                json.loads(
                    export_nb_outputs(
                        {"sweep_interval": long_interval, "results": long_results, "fit": long_changed_results}
                    )
                ),
            ),
            (
                "bad_data",
                json.loads(
                    export_nb_outputs(
                        {"sweep_interval": long_interval, "results": long_results, "fit": long_very_changed_results}
                    )
                ),
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
            assert 0.3 < error < 1.0


######################################################
#################### TEST IQ ERROR ###################
######################################################


class TestIQNormRootMeanSqrtError:
    """Test the IQ_norm_root_mean_sqrt_error comparison model."""

    @pytest.mark.parametrize(
        "comparison",
        [
            json.loads(
                export_nb_outputs(
                    {
                        "sweep_interval": basic_interval,
                        "results": [basic_results],
                        "fit": [basic_results, basic_results],
                    }
                )
            ),
            json.loads(
                export_nb_outputs(
                    {
                        "sweep_interval": basic_interval,
                        "results": [changed_results, changed_results],
                        "fit": [basic_results],
                    }
                )
            ),
            json.loads(
                export_nb_outputs(
                    {"sweep_interval": basic_interval, "results": [very_changed_results], "fit": [basic_results]}
                )
            ),
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
            json.loads(
                export_nb_outputs({"results": [basic_results, basic_results], "fit": [basic_results, basic_results]})
            ),
            json.loads(export_nb_outputs({"sweep_interval": basic_interval, "fit": [basic_results, basic_results]})),
            json.loads(
                export_nb_outputs(
                    {"sweep_interval": basic_interval, "results": [very_changed_results, very_changed_results]}
                )
            ),
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
            json.loads(
                export_nb_outputs(
                    {
                        "sweep_interval": [],
                        "results": [basic_results, basic_results],
                        "fit": [basic_results, basic_results],
                    }
                )
            ),
            json.loads(
                export_nb_outputs(
                    {"sweep_interval": basic_interval, "results": [], "fit": [basic_results, basic_results]}
                )
            ),
            json.loads(
                export_nb_outputs(
                    {
                        "sweep_interval": basic_interval,
                        "results": [very_changed_results, very_changed_results],
                        "fit": [],
                    }
                )
            ),
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
                json.loads(
                    export_nb_outputs(
                        {
                            "sweep_interval": basic_interval,
                            "results": [basic_results, basic_results],
                            "fit": [basic_results, basic_results],
                        }
                    )
                ),
            ),
            (
                "out_of_spec",
                json.loads(
                    export_nb_outputs(
                        {
                            "sweep_interval": basic_interval,
                            "results": [changed_results, changed_results],
                            "fit": [basic_results, basic_results],
                        }
                    )
                ),
            ),
            (
                "bad_data",
                json.loads(
                    export_nb_outputs(
                        {
                            "sweep_interval": basic_interval,
                            "results": [very_changed_results, very_changed_results],
                            "fit": [basic_results, basic_results],
                        }
                    )
                ),
            ),
        ],
    )
    def test_IQ_norm_root_mean_sqrt_error_results(self, output, comparison_IQ):
        """Test a valid comparison with the results."""
        error = IQ_norm_root_mean_sqrt_error(obtained_IQ, comparison_IQ, fit=False)

        if output == "in_spec":
            assert error < 0.05

        elif output == "out_of_spec":
            assert 0.05 < error < 0.3

        elif output == "bad_data":
            assert 0.3 < error < 1.0

    @pytest.mark.parametrize(
        "output, comparison_IQ",
        [
            (
                "in_spec",
                json.loads(
                    export_nb_outputs(
                        {
                            "sweep_interval": basic_interval,
                            "results": [basic_results, basic_results],
                            "fit": [basic_results, basic_results],
                        }
                    )
                ),
            ),
            (
                "out_of_spec",
                json.loads(
                    export_nb_outputs(
                        {
                            "sweep_interval": basic_interval,
                            "results": [basic_results, basic_results],
                            "fit": [changed_results, changed_results],
                        }
                    )
                ),
            ),
            (
                "bad_data",
                json.loads(
                    export_nb_outputs(
                        {
                            "sweep_interval": basic_interval,
                            "results": [basic_results, basic_results],
                            "fit": [very_changed_results, very_changed_results],
                        }
                    )
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
            assert 0.3 < error < 1.0


######################################################
#################### TEST 2D ERROR ###################
######################################################


class TestSSROComparison2D:
    """Test the ssro_comparison_2D comparison model."""

    @pytest.mark.parametrize(
        "comparison",
        [
            json.loads(
                export_nb_outputs(
                    {
                        "sweep_interval": [basic_results, basic_results],
                        "results": [basic_results],
                        "fit": [basic_results, basic_results],
                    }
                )
            ),
            json.loads(
                export_nb_outputs(
                    {
                        "sweep_interval": [basic_results, basic_results],
                        "results": [changed_results, changed_results],
                        "fit": [basic_results],
                    }
                )
            ),
            json.loads(
                export_nb_outputs(
                    {
                        "sweep_interval": [basic_results, basic_results],
                        "results": [very_changed_results],
                        "fit": [basic_results],
                    }
                )
            ),
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
            json.loads(
                export_nb_outputs({"results": [basic_results, basic_results], "fit": [basic_results, basic_results]})
            ),
            json.loads(
                export_nb_outputs(
                    {"sweep_interval": [basic_results, basic_results], "fit": [basic_results, basic_results]}
                )
            ),
            json.loads(
                export_nb_outputs(
                    {
                        "sweep_interval": [basic_results, basic_results],
                        "results": [very_changed_results, very_changed_results],
                    }
                )
            ),
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
            assert error == error2 < 0.005

        elif output == "out_of_spec":
            assert 0.005 < error == error2 < 0.3

        elif output == "bad_data":
            assert 0.3 < error == error2 < 15.0
