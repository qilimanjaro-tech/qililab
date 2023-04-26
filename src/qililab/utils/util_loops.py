""" Utilities for Loops """
from typing import List

import numpy as np

from qililab.utils.loop import Loop


def _find_minimum_range_from_loops(loops: List[Loop] | None):
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


def _create_loops_from_inner_loops(loops: List[Loop]):
    """create sequence of loops from inner loops (if exist)"""
    return list(filter(None, [loop.loop for loop in loops]))


def compute_ranges_from_loops(loops: List[Loop] | None):
    """compute ranges from a list of loops that may have inner loops"""
    if loops is None or len(loops) <= 0:
        return []
    ranges = compute_ranges_from_loops(loops=_create_loops_from_inner_loops(loops=loops))
    ranges.append(_find_minimum_range_from_loops(loops=loops))
    return ranges


def compute_shapes_from_loops(loops: List[Loop] | None):
    """compute the shapes from a list of loops that may have inner loops"""
    if loops is None:
        return []
    all_shapes = [loop.shape for loop in loops]
    max_len = max(len(shape) for shape in all_shapes)
    all_shapes_with_same_length = [shape + [0] * (max_len - len(shape)) for shape in all_shapes]
    return [min(values) for values in zip(*all_shapes_with_same_length)]
