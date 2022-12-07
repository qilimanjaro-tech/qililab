"""Module containing utilities for the tests."""
from typing import List, Tuple

import numpy as np


def name_generator(base: str):
    """Unique name generator
    Args:
        base (str): common name for all the elements.
    Yields:
        str: Unique name in the format base_id.
    """
    next_id = 0
    while True:
        yield f"{base}_{str(next_id)}"
        next_id += 1


def compare_pair_of_arrays(
    pair_a: Tuple[List[float], List[float]],
    pair_b: Tuple[List[float], List[float]],
    tolerance: float,
) -> bool:
    """Compares two pairs of arrays of the same length up to a given tolerance.

    Args:
        pair_a (Tuple[List[float], List[float]]): First pair of arrays.
        pair_b (Tuple[List[float], List[float]]): Second pair of arrays.
        tolerance (float): Absolute amount up to which the arrays can differ to be considered equal.

    Returns:
        bool: True if the arrays are equal up to the given tolerance, False otherwise.
    """
    path0_ok = all(np.isclose(pair_a[0], pair_b[0], atol=tolerance))
    path1_ok = all(np.isclose(pair_a[1], pair_b[1], atol=tolerance))
    return path0_ok and path1_ok


def complete_array(array: List[float], filler: float, final_length: int) -> List[float]:
    """Fills a given array with the given float as a filler up to the final_length specified.

    Args:
        array (List[float]): Original array.
        filler (float): Number to use as a filler.
        final_length (int): Final length of the array.

    Returns:
        List[float]: List of length `final_length` where the first `len(array)` elements are those of the original
            array, and the remaining elements are are repetitions of `filler`.
    """
    return array + [filler] * (final_length - len(array))


dummy_qrm_name_generator = name_generator("dummy_qrm")
dummy_qcm_name_generator = name_generator("dummy_qcm")
