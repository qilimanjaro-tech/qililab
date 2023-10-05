import numpy as np


def normalized_mean_absolute_error(obtained: dict[str, list], comparison: dict[str, list]) -> float:
    """Returns the normalized MAE (mean absolute error) between the comparison and obtained samples.

    Args:
        obtained (dict): obtained samples to compare.
        comparison (dict): previous samples to compare.

    Returns:
        float: difference/error between the two samples.
    """
    absolute_error = sum(
        np.abs(obtained["y"][i] - comparison["y"][comparison["x"].index(obtained_x)])
        for i, obtained_x in enumerate(obtained["x"])
    )
    mean_absolute_error = absolute_error / len(obtained["y"])
    return mean_absolute_error / np.mean(comparison["y"])  # normalize the difference with the mean values


def normalized_mean_square_error(obtained: dict[str, list], comparison: dict[str, list]) -> float:
    """Returns the normalized MSE (mean square error) between the comparison and obtained samples.

    Args:
        obtained (dict): obtained samples to compare.
        comparison (dict): previous samples to compare.

    Returns:
        float: difference/error between the two samples.
    """
    square_error = sum(
        (obtained["y"][i] - comparison["y"][comparison["x"].index(obtained_x)]) ** 2
        for i, obtained_x in enumerate(obtained["x"])
    )
    mean_square_error = square_error / len(obtained["y"])
    return mean_square_error / np.mean(comparison["y"])  # normalize the difference with the mean values


def normalized_root_mean_square_error(obtained: dict[str, list], comparison: dict[str, list]) -> float:
    """Returns the normalized RMSE (mean absolute error) between the comparison and obtained samples.

    Args:
        obtained (dict): obtained samples to compare.
        comparison (dict): previous samples to compare.

    Returns:
        float: difference/error between the two samples.
    """
    square_error = sum(
        (obtained["y"][i] - comparison["y"][comparison["x"].index(obtained_x)]) ** 2
        for i, obtained_x in enumerate(obtained["x"])
    )
    root_mean_square_error = np.sqrt(square_error / len(obtained["y"]))
    return root_mean_square_error / np.mean(comparison["y"])  # normalize the difference with the mean values