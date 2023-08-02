""" Utilities for Loops."""
import numpy as np

from qililab.utils.loop import Loop


def _find_minimum_range_from_loops(loops: list[Loop] | None):
    """find minimum range from same level loops"""
    if loops is None or len(loops) <= 0:
        return np.array([], dtype=object)
    minimum_range = loops[0].values
    minimum_range_length = len(loops[0].values)
    for loop in loops:
        if len(loop.values) < minimum_range_length:
            minimum_range = loop.values
            minimum_range_length = len(loop.values)
    return minimum_range


def _create_loops_from_inner_loops(loops: list[Loop]):
    """create sequence of loops from inner loops (if exist)"""
    return list(filter(None, [loop.loop for loop in loops]))


def compute_ranges_from_loops(loops: list[Loop] | None):
    """compute ranges from a list of loops that may have inner loops"""
    if loops is None or len(loops) <= 0:
        return []
    ranges = compute_ranges_from_loops(loops=_create_loops_from_inner_loops(loops=loops))
    ranges.append(_find_minimum_range_from_loops(loops=loops))
    return ranges


def compute_shapes_from_loops(loops: list[Loop]):
    """Computes the shape of the results obtained from running a list of parallel loops that might contain
    inner loops.

    When running parallel loops, the shape of the results correspond to the minimum range of each nested loop.

    Args:
        loops (list[.Loop]): list of parallel loops that might contain inner loops

    Returns:
        list[int]: shape of the results obtained from running the parallel loops
    """
    if loops is None:
        return []
    all_shapes = [loop.shape for loop in loops]
    max_len = max(len(shape) for shape in all_shapes)
    final_shape: list[None | int] = [None] * max_len
    for shape in all_shapes:
        for i, dim in enumerate(shape):
            if final_shape[i] is None or dim < final_shape[i]:  # type: ignore
                final_shape[i] = dim
    return final_shape
