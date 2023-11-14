# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Comparison models, to use in ``CalibrationController`` ``check_data()``."""
import numpy as np


def is_structure_of_check_parameters_correct(obtained: dict[str, list], comparison: dict[str, list]):
    """If the structure is incorrect it will raise an error.

    Args:
        obtained (dict): obtained samples to compare.
        comparison (dict): previous samples to compare.
        fit (bool): flag, to wether compare against the previous fit or the previous results. Defaults to True (against fit).

    Raises:
        ValueError: if keys or shapes don't match the expected.
    """
    for check_data in [obtained, comparison]:
        if "sweep_interval" not in check_data or "results" not in check_data or "fit" not in check_data:
            raise ValueError(
                "Keys in the `check_parameters` are not 'sweep_interval', 'results' and 'fit', as is need in for the comparison models."
            )

        if len(check_data["sweep_interval"]) == 0 or len(check_data["results"]) == 0 or len(check_data["fit"]) == 0:
            raise ValueError(
                "Empty 'sweep_interval', 'results' or 'fit' in  `check_parameters`. They are needed for the comparison models."
            )


# def norm_mean_abs_error(obtained: dict[str, list], comparison: dict[str, list], fit: bool = True) -> float:
#     """Returns the normalized MAE (mean absolute error) between the comparison and obtained samples.

#     Args:
#         obtained (dict): obtained samples to compare.
#         comparison (dict): previous samples to compare.
#         fit (bool): flag, to wether compare against the previous fit or the previous results. Defaults to True (against fit).

#     Returns:
#         float: difference/error between the two samples.
#     """
#     is_structure_of_check_parameters_correct(obtained, comparison)

#     if obtained["results"].shape() == 1:

#         check = "fit" if fit else "result"

#         absolute_error = sum(
#             np.abs(obtained["results"][i] - comparison[check][comparison["sweep_interval"].index(obtained_x)])
#             for i, obtained_x in enumerate(obtained["sweep_interval"])
#         )

#         mean_absolute_error = absolute_error / len(obtained["results"])
#         return mean_absolute_error / np.mean(comparison[check])  # normalize the difference with the mean values

#     raise ValueError("Shape too big for this comparison model.")


# def norm_mean_sqrt_error(obtained: dict[str, list], comparison: dict[str, list], fit: bool = True) -> float:
#     """Returns the normalized MSE (mean square error) between the comparison and obtained samples.

#     Args:
#         obtained (dict): obtained samples to compare.
#         comparison (dict): previous samples to compare.
#         fit (bool): flag, to wether compare against the previous fit or the previous results. Defaults to True (against fit).

#     Returns:
#         float: difference/error between the two samples.
#     """
#     is_structure_of_check_parameters_correct(obtained, comparison)

#     if obtained["results"].shape() == 1:

#         check = "fit" if fit else "result"

#         square_error = sum(
#             (obtained["results"][i] - comparison[check][comparison["sweep_interval"].index(obtained_x)]) ** 2
#             for i, obtained_x in enumerate(obtained["sweep_interval"])
#         )
#         mean_square_error = square_error / len(obtained["results"])
#         return mean_square_error / np.mean(comparison[check])  # normalize the difference with the mean values

#     raise ValueError("Shape too big for this comparison model.")


def norm_root_mean_sqrt_error(obtained: dict[str, list], comparison: dict[str, list], fit: bool = True) -> float:
    """Returns the normalized RMSE (mean absolute error) between the comparison and obtained samples.

    Args:
        obtained (dict): obtained samples to compare.
        comparison (dict): previous samples to compare.
        fit (bool): flag, to wether compare against the previous fit or the previous results. Defaults to True (against fit).

    Returns:
        float: difference/error between the two samples.
    """
    is_structure_of_check_parameters_correct(obtained, comparison)

    if np.asarray(obtained["results"]).shape() != (len(obtained["sweep_interval"]),):
        raise ValueError("Incorrect 'results' shape for this comparison model.")

    check = "fit" if fit else "result"

    square_error = sum(
        (obtained["results"][i] - comparison[check][comparison["sweep_interval"].index(obtained_x)]) ** 2
        for i, obtained_x in enumerate(obtained["sweep_interval"])
    )
    root_mean_square_error = np.sqrt(square_error / len(obtained["results"]))
    return root_mean_square_error / np.mean(comparison[check])  # normalize the difference with the mean values


def IQ_norm_root_mean_sqrt_error(obtained: dict[str, list], comparison: dict[str, list], fit: bool = True) -> float:
    """Returns the normalized RMSE (mean absolute error) between the comparison and obtained samples.

    Args:
        obtained (dict): obtained samples to compare.
        comparison (dict): previous samples to compare.
        fit (bool): flag, to wether compare against the previous fit or the previous results. Defaults to True (against fit).

    Returns:
        float: difference/error between the two samples.
    """
    is_structure_of_check_parameters_correct(obtained, comparison)

    if np.asarray(obtained["results"]).shape() != (2, len(obtained["sweep_interval"])):
        raise ValueError("Incorrect 'results' shape for this comparison model.")

    i, q = obtained["results"]

    check = "fit" if fit else "result"

    error = 0
    for obtained_results in i, q:
        square_error = sum(
            (obtained_results[i] - comparison[check][comparison["sweep_interval"].index(obtained_x)]) ** 2
            for i, obtained_x in enumerate(obtained["sweep_interval"])
        )
        root_mean_square_error = np.sqrt(square_error / len(obtained_results))
        error += root_mean_square_error / np.mean(comparison[check])  # normalize the difference with the mean values

    return error


def ssro_comparison_2D(obtained: dict[str, list], comparison: dict[str, list], fit: bool = True) -> float:
    """Returns the normalized RMSE (mean absolute error) between the comparison and obtained samples.

    Args:
        obtained (dict): obtained samples to compare.
        comparison (dict): previous samples to compare.
        fit (bool): flag, to wether compare against the previous fit or the previous results. Defaults to True (against fit).

    Returns:
        float: difference/error between the two samples.
    """
    if np.asarray(obtained["results"]).shape() != (2, len(obtained["sweep_interval"])):
        raise ValueError("Incorrect shape for this comparison model.")

    check = "fit" if fit else "result"

    obtained_i, obtained_q = obtained["results"]
    comparison_i, comparison_q = comparison[check]

    # Difference in means of 2d histograms
    mean_diff = (np.mean(obtained_i) - np.mean(comparison_i)) ** 2 + (np.mean(obtained_q) - np.mean(comparison_q)) ** 2
    # Difference in std of 2d histograms
    standard_dev = (np.std(obtained_i) - np.std(comparison_i)) ** 2 + (np.std(obtained_q) - np.std(comparison_q)) ** 2

    return np.sqrt(mean_diff * 4 + standard_dev / (5 * len(obtained["sweep_interval"])))
    # TODO: Compare 2D guassian distributions, with a more specific function.
