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
from typing import Any

import numpy as np

# Epsilon, for avoiding divisions by zero.
div_epsilon = 0.00000000000000000000000000001


def norm_root_mean_sqrt_error(obtained: dict[str, list], comparison: dict[str, list]) -> float:
    """Returns the normalized RMSE (mean absolute error) between the comparison and obtained samples.

    If the comparison has a fit, it will be used, if not, the results will.

    The samples have to have the following structure (lists can be arrays as well):

    obtained/comparison = {
        "sweep_interval": list_of_the_sweep,
        "results": list_of_results
        "fit": list_of_fitting,  # optional
    }

    Args:
        obtained (dict): obtained samples to compare. Structure following the function docstring.
        comparison (dict): previous samples to compare. Structure following the function docstring.

    Returns:
        float: difference/error between the two samples.
    """
    (fit, check) = (True, "fit") if "fit" in comparison else (False, "results")

    # Structure checks:
    is_structure_of_check_parameters_correct(obtained, comparison, fit)

    for check_data in [obtained, comparison]:
        if not np.shape(check_data[check]) == np.shape(check_data["results"]) == (len(check_data["sweep_interval"]),):
            raise ValueError("Incorrect 'check_parameters' shape for this notebook output.")

        if 0 in [len(check_data["sweep_interval"]), len(check_data["results"])]:
            raise ValueError("Empty 'sweep_interval' or 'results' in `check_parameters`'s notebook output.")

    # Error computation:
    # TODO: Avoid comparison "if obtained_x in comparison["sweep_interval"]" instead build comparison sweep interval taking into acount this
    # TODO: If no overlapping sweep intervals we must return a huge error so we get bad_data directly
    square_error = sum(
        (obtained["results"][i] - comparison[check][comparison["sweep_interval"].index(obtained_x)]) ** 2
        for i, obtained_x in enumerate(obtained["sweep_interval"])
        if obtained_x in comparison["sweep_interval"]
    )
    root_mean_square_error = np.sqrt(square_error / len(obtained["results"]))

    return root_mean_square_error / np.abs(np.mean(comparison[check]) + div_epsilon)


def IQ_norm_root_mean_sqrt_error(obtained: dict[str, list], comparison: dict[str, list]) -> float:
    """Returns the normalized RMSE (mean absolute error) between the comparison and obtained samples for I and Q.

    If the comparison has a fit, it will be used, if not, the results will.

    The samples have to have the following structure (lists can be arrays as well):

    obtained/comparison = {
        "sweep_interval": list_of_the_sweep,
        "results": [list_of_I_results, list_of_Q_results],
        "fit": [list_of_I_fitting, list_of_Q_fitting],  # optional
    }

    Args:
        obtained (dict): obtained samples to compare. Structure following the function docstring.
        comparison (dict): previous samples to compare. Structure following the function docstring.

    Returns:
        float: difference/error between the two samples.
    """
    (fit, check) = (True, "fit") if "fit" in comparison else (False, "results")

    # Structure checks:
    is_structure_of_check_parameters_correct(obtained, comparison, fit)

    for check_data in [obtained, comparison]:
        if not np.shape(check_data[check]) == np.shape(check_data["results"]) == (2, len(check_data["sweep_interval"])):
            raise ValueError("Incorrect 'check_parameters' shape for this notebook output.")

        if 0 in [len(check_data["sweep_interval"]), len(check_data["results"][0]), len(check_data["results"][1])]:
            raise ValueError("Empty 'sweep_interval' or 'results' in `check_parameters`'s notebook output.")

    # Error computation:
    i, q = obtained["results"]
    errors = []
    # TODO: Avoid comparison "if obtained_x in comparison["sweep_interval"]" instead build comparison sweep interval taking into acount this
    # TODO: If no overlapping sweep intervals we must return a huge error so we get bad_data directly
    for idx, obtained_results in enumerate([i, q]):
        square_error = sum(
            (obtained_results[index] - comparison[check][idx][comparison["sweep_interval"].index(obtained_x)]) ** 2
            for index, obtained_x in enumerate(obtained["sweep_interval"])
            if obtained_x in comparison["sweep_interval"]
        )
        root_mean_square_error = np.sqrt(square_error / len(obtained_results))

        # normalize the difference with the mean values, and add it to the i or q error
        errors.append(root_mean_square_error / np.abs(np.mean(comparison[check]) + div_epsilon))

    # Return the one with less errors, since it was the one used for the fitting.
    return np.min(errors)


# pylint: disable=too-many-locals
def ssro_comparison_2D(obtained: dict[str, Any], comparison: dict[str, Any]) -> float:
    """Returns a normalized error between the comparison and obtained samples, for 2D plots.

    Always compares results vs results, no fit used.

    The samples have to have the following structure (lists can be arrays as well):

    obtained/comparison = {
        "sweep_interval": NUM_BINS,
        "results": ((list_i_0, list_i_1), (list_q_0, list_q_1)),  # the index indicates the gaussian.
    }

    Args:
        obtained (dict): Obtained samples to compare. Structure following the function docstring.
        comparison (dict): pPrevious samples to compare. Structure following the function docstring.

    Returns:
        float: difference/error between the two samples.
    """
    # Structure checks:
    for check_data in [obtained, comparison]:
        if "sweep_interval" not in check_data or "results" not in check_data:
            raise ValueError("Keys in the `check_parameters` are not 'sweep_interval' and 'results', as is needed.")

        if np.shape(check_data["results"]) != (2, 2, check_data["sweep_interval"]):
            raise ValueError("Incorrect 'check_parameters' shape for this notebook output.")

        for i in range(2):
            if len(check_data["results"][0][i]) == 0 or len(check_data["results"][1][i]) == 0:
                raise ValueError("Empty 'sweep_interval' or 'results' in `check_parameters`'s notebook output.")

    i_s: list[list[list[list]]] = [[[], []], [[], []]]
    q_s: list[list[list[list]]] = [[[], []], [[], []]]
    mean_diff, std_dev_diff = 0, 0
    # Error computation:
    for gaussian_n in range(2):  # For first and secong gaussian
        for datas, data in enumerate([obtained, comparison]):
            i_s[gaussian_n][datas] = data["results"][0][datas]  # 0 for i's, and j for first or second gaussian
            q_s[gaussian_n][datas] = data["results"][1][datas]  # 1 for q's, and j for first or second gaussian

        # Difference in means of 2d histograms
        mean_diff += (
            (np.mean(i_s[gaussian_n][0]) - np.mean(i_s[gaussian_n][1])) / (np.mean(i_s[gaussian_n][0]) + div_epsilon)
        ) ** 2 + (
            (np.mean(q_s[gaussian_n][0]) - np.mean(q_s[gaussian_n][1])) / (np.mean(q_s[gaussian_n][0]) + div_epsilon)
        ) ** 2

        # Difference in std of 2d histograms
        std_dev_diff += (
            (np.std(i_s[gaussian_n][0]) - np.std(i_s[gaussian_n][1])) / (np.std(i_s[gaussian_n][0]) + div_epsilon)
        ) ** 2 + (
            (np.std(q_s[gaussian_n][0]) - np.std(q_s[gaussian_n][1])) / (np.std(q_s[gaussian_n][0]) + div_epsilon)
        ) ** 2

    # Return a weighted sum, with more weight in the average than the standard deviation:
    return np.sqrt((mean_diff) * 4 + (std_dev_diff) / (obtained["sweep_interval"] + div_epsilon)) / 10


def is_structure_of_check_parameters_correct(obtained: dict[str, list], comparison: dict[str, list], fit: bool = True):
    """If the structure is incorrect it will raise an error.

    Args:
        obtained (dict): obtained samples to compare.
        comparison (dict): previous samples to compare.
        fit (bool): flag, to wether compare against the previous fit as well as the previous results. Defaults to True (against fit).

    Raises:
        ValueError: if keys don't match the expected.
    """
    for check_data in [obtained, comparison]:
        if "sweep_interval" not in check_data or "results" not in check_data or (fit and "fit" not in check_data):
            raise ValueError(
                "Keys in the `check_parameters` are not 'sweep_interval', 'results' (and 'fit', optional), as is needed."
            )
