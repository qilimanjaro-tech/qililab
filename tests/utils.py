"""Module containing utilities for the tests."""
from typing import List, Tuple

import numpy as np
import numpy.typing as npt

from qililab.result.qblox_results.scope_data import ScopeData


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
    pair_a: Tuple[npt.NDArray[np.float32], npt.NDArray[np.float32]],
    pair_b: Tuple[npt.NDArray[np.float32], npt.NDArray[np.float32]],
    tolerance: float,
) -> bool:
    path0_ok = all(np.isclose(pair_a[0], pair_b[0], atol=tolerance))
    path1_ok = all(np.isclose(pair_a[1], pair_b[1], atol=tolerance))
    return path0_ok and path1_ok


def complete_array(array: npt.NDArray[np.float32], filler: float, final_length: int) -> npt.NDArray[np.float32]:
    filler_list = np.ones(final_length - len(array)) * filler
    return np.append(array, filler_list)


dummy_qrm_name_generator = name_generator("dummy_qrm")
dummy_qcm_name_generator = name_generator("dummy_qcm")
