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
from scipy.stats import ks_2samp


def norm_root_mean_sqrt_error(obtained: dict[str, list], comparison: dict[str, list], fit: bool = True) -> float:
    """Returns the normalized RMSE (mean absolute error) between the comparison and obtained samples.

    Args:
        obtained (dict): obtained samples to compare.
        comparison (dict): previous samples to compare.
        fit (bool): flag, to wether compare against the previous fit or the previous results. Defaults to True (against fit).

    Returns:
        float: difference/error between the two samples.
    """
    # TODO: Check if statements regarding 'fit' to use fit to compare results
    # is_structure_of_check_parameters_correct(obtained, comparison)

    # for check_data in [obtained, comparison]:
    #     if (fit and not np.shape(check_data["results"]) == np.shape(check_data["fit"]) == (len(check_data["sweep_interval"]),)) or (not fit and not np.shape(check_data["results"]) == (len(check_data["sweep_interval"]),)):
    #         raise ValueError("Incorrect 'results' shape for this comparison model.")

    check = "fit" if fit else "results"

    square_error = sum(
        (obtained["results"][i] - comparison[check][comparison["sweep_interval"].index(obtained_x)]) ** 2
        for i, obtained_x in enumerate(obtained["sweep_interval"])
    )
    root_mean_square_error = np.sqrt(square_error / len(obtained["results"]))
    # TODO: Check which normalization we want.

    return root_mean_square_error / np.abs(
        np.mean(comparison[check]) + 0000000000.1
    )  # normalize the difference with the mean values


def IQ_norm_root_mean_sqrt_error(obtained: dict[str, list], comparison: dict[str, list], fit: bool = True) -> float:
    """Returns the normalized RMSE (mean absolute error) between the comparison and obtained samples.

    Args:
        obtained (dict): obtained samples to compare.
        comparison (dict): previous samples to compare.
        fit (bool): flag, to wether compare against the previous fit or the previous results. Defaults to True (against fit).

    Returns:
        float: difference/error between the two samples.
    """
    # is_structure_of_check_parameters_correct(obtained, comparison)

    # for check_data in [obtained, comparison]:
    #    if (fit and not np.shape(check_data["results"]) == np.shape(check_data["fit"]) == (2, len(check_data["sweep_interval"]))) or (not fit and not np.shape(check_data["results"]) == (2, len(check_data["sweep_interval"]))):
    #        raise ValueError("Incorrect 'results' shape for this comparison model.")

    i, q = obtained["results"]

    check = "fit" if fit else "results"

    errors = []
    for idx, obtained_results in enumerate([i, q]):
        square_error = sum(
            (obtained_results[index] - comparison[check][idx][comparison["sweep_interval"].index(obtained_x)]) ** 2
            for index, obtained_x in enumerate(obtained["sweep_interval"])
        )
        root_mean_square_error = np.sqrt(square_error / len(obtained_results))
        # TODO: Check which normalization we want.

        # normalize the difference with the mean values, and add it to the i or q error
        errors.append(root_mean_square_error / np.abs(np.mean(comparison[check]) + 0000000000.1))

    # Return the one with less errors, since it was the one used for the fitting.
    return np.min(errors)


def ssro_comparison_2D(obtained: dict[str, list], comparison: dict[str, list], fit: bool = True) -> float:
    """Returns the normalized RMSE (mean absolute error) between the comparison and obtained samples.

    Args:
        obtained (dict): obtained samples to compare.
        comparison (dict): previous samples to compare.
        fit (bool): flag, to wether compare against the previous fit or the previous results. Defaults to True (against fit).

    Returns:
        float: difference/error between the two samples.
    """
    for check_data in [obtained, comparison]:
        if "sweep_interval" not in check_data or "results" not in check_data:
            raise ValueError(
                "Keys in the `check_parameters` are not 'sweep_interval', 'results' and 'fit', as is need in for the comparison models."
            )

        if len(check_data["sweep_interval"]) == 0 or len(check_data["results"]) == 0:
            raise ValueError(
                "Empty 'sweep_interval', 'results' or 'fit' in  `check_parameters`. They are needed for the comparison models."
            )

        if np.shape(check_data["results"]) != np.shape(check_data["sweep_interval"]):
            raise ValueError("Incorrect 'results' shape for this comparison model.")

    _ = fit  # No fit for this case.
    # TODO:Add epsilons to cancel divergences for means 0.0 aka perfect match between compt and obtained :rock:
    obtn_i_0, obtn_i_1 = obtained["sweep_interval"]  # first gaussian I's
    obtn_q_0, obtn_q_1 = obtained["results"]  # second gaussian I's

    comp_i_0, comp_i_1 = comparison["sweep_interval"]  # first gaussian Q's
    comp_q_0, comp_q_1 = comparison["results"]  # second gaussian Q's

    # Difference in means of 2d histograms
    mean_diff_0 = ((np.mean(obtn_i_0) - np.mean(comp_i_0)) / np.mean(obtn_i_0)) ** 2 + (
        (np.mean(obtn_q_0) - np.mean(comp_q_0)) / np.mean(obtn_q_0)
    ) ** 2
    mean_diff_1 = ((np.mean(obtn_i_1) - np.mean(comp_i_1)) / np.mean(obtn_i_1)) ** 2 + (
        (np.mean(obtn_q_1) - np.mean(comp_q_1)) / np.mean(obtn_q_1)
    ) ** 2
    # Difference in std of 2d histograms
    std_dev_0 = ((np.std(obtn_i_0) - np.std(comp_i_0)) / np.std(obtn_i_0)) ** 2 + (
        (np.std(obtn_q_0) - np.std(comp_q_0)) / np.std(obtn_q_0)
    ) ** 2
    std_dev_1 = ((np.std(obtn_i_1) - np.std(comp_i_1)) / np.std(obtn_i_1)) ** 2 + (
        (np.std(obtn_q_1) - np.std(comp_q_1)) / np.std(obtn_q_1)
    ) ** 2

    return (
        np.sqrt((mean_diff_0 + mean_diff_1) * 4 + (std_dev_0 + std_dev_1) / (len(obtained["sweep_interval"][0]))) / 10
    )
    # TODO: Compare 2D guassian distributions, with a more specific function?


def is_structure_of_check_parameters_correct(obtained: dict[str, list], comparison: dict[str, list], fit: bool = True):
    """If the structure is incorrect it will raise an error.

    Args:
        obtained (dict): obtained samples to compare.
        comparison (dict): previous samples to compare.
        fit (bool): flag, to wether compare against the previous fit or the previous results. Defaults to True (against fit).

    Raises:
        ValueError: if keys or shapes don't match the expected.
    """
    for check_data in [obtained, comparison]:
        if "sweep_interval" not in check_data or "results" not in check_data or (fit and "fit" not in check_data):
            raise ValueError(
                "Keys in the `check_parameters` are not 'sweep_interval', 'results' and 'fit', as is need in for the comparison models."
            )

        if (
            len(check_data["sweep_interval"]) == 0
            or len(check_data["results"]) == 0
            or (fit and len(check_data["fit"]) == 0)
        ):
            raise ValueError(
                "Empty 'sweep_interval', 'results' or 'fit' in  `check_parameters`. They are needed for the comparison models."
            )


################################################################
#######################  OTHER COMPARISONS  ####################
################################################################


def scipy_ks_2_samples_error(obtained: dict[str, list], comparison: dict[str, list], fit: bool = True) -> float:
    """Returns the normalized RMSE (mean absolute error) between the comparison and obtained samples.

    Args:
        obtained (dict): obtained samples to compare.
        comparison (dict): previous samples to compare.
        fit (bool): flag, to wether compare against the previous fit or the previous results. Defaults to True (against fit).

    Returns:
        float: difference/error between the two samples.
    """
    is_structure_of_check_parameters_correct(obtained, comparison)

    for check_data in [obtained, comparison]:
        if not np.shape(check_data["results"]) == np.shape(check_data["fit"]) == (len(check_data["sweep_interval"]),):
            raise ValueError("Incorrect 'results' shape for this comparison model.")

    check = "fit" if fit else "results"
    return ks_2samp(obtained["results"], comparison[check])
    # TODO: This doesn't work since ks_2samp asumes homogenous distribution in the x axis!


################################################################
#####################  OTHER NORMALIZATIONS  ###################
################################################################


def norm_mean_abs_error(obtained: dict[str, list], comparison: dict[str, list], fit: bool = True) -> float:
    """Returns the normalized MAE (mean absolute error) between the comparison and obtained samples.

    Args:
        obtained (dict): obtained samples to compare.
        comparison (dict): previous samples to compare.
        fit (bool): flag, to wether compare against the previous fit or the previous results. Defaults to True (against fit).

    Returns:
        float: difference/error between the two samples.
    """
    is_structure_of_check_parameters_correct(obtained, comparison)

    for check_data in [obtained, comparison]:
        if not np.shape(check_data["results"]) == np.shape(check_data["fit"]) == (len(check_data["sweep_interval"]),):
            raise ValueError("Incorrect 'results' shape for this comparison model.")

    check = "fit" if fit else "results"

    absolute_error = sum(
        np.abs(obtained["results"][i] - comparison[check][comparison["sweep_interval"].index(obtained_x)])
        for i, obtained_x in enumerate(obtained["sweep_interval"])
    )
    mean_absolute_error = absolute_error / len(obtained["results"])
    return mean_absolute_error / np.abs(np.mean(comparison[check]) + 0000000000.1)


def norm_mean_sqrt_error(obtained: dict[str, list], comparison: dict[str, list], fit: bool = True) -> float:
    """Returns the normalized MSE (mean square error) between the comparison and obtained samples.

    Args:
        obtained (dict): obtained samples to compare.
        comparison (dict): previous samples to compare.
        fit (bool): flag, to wether compare against the previous fit or the previous results. Defaults to True (against fit).

    Returns:
        float: difference/error between the two samples.
    """
    is_structure_of_check_parameters_correct(obtained, comparison)

    for check_data in [obtained, comparison]:
        if not np.shape(check_data["results"]) == np.shape(check_data["fit"]) == (len(check_data["sweep_interval"]),):
            raise ValueError("Incorrect 'results' shape for this comparison model.")

    check = "fit" if fit else "results"

    square_error = sum(
        (obtained["results"][i] - comparison[check][comparison["sweep_interval"].index(obtained_x)]) ** 2
        for i, obtained_x in enumerate(obtained["sweep_interval"])
    )
    mean_square_error = square_error / len(obtained["results"])
    return mean_square_error / np.abs(np.mean(comparison[check]) + 0000000000.1)
