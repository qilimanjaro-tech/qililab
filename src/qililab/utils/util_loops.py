""" Utilities for Loops """
from typing import List

import numpy as np

from qililab.utils.loop import Loop


def find_minimum_outer_range_from_loops(loops: List[Loop] | None):
    """find minimum outer range from same level loops"""
    if loops is None or len(loops) <= 0:
        return np.array([], dtype=object)
    minimum_outer_range = loops[0].outer_loop_range
    minimum_range_length = len(loops[0].outer_loop_range)
    for loop in loops:
        if len(loop.outer_loop_range) < minimum_range_length:
            minimum_outer_range = loop.outer_loop_range
            minimum_range_length = len(loop.outer_loop_range)
    return minimum_outer_range


def find_minimum_inner_range_from_loops(loops: List[Loop] | None):
    """find minimum inner range from same level loops"""
    if loops is None or len(loops) <= 0:
        return np.array([], dtype=object)

    if loops[0].inner_loop_range is None:
        return np.array([], dtype=object)
    minimum_inner_range = loops[0].inner_loop_range
    minimum_range_length = len(loops[0].inner_loop_range)

    for loop in loops:
        if loop.inner_loop_range is None:
            continue
        if len(loop.inner_loop_range) < minimum_range_length:
            minimum_inner_range = loop.inner_loop_range
            minimum_range_length = len(loop.inner_loop_range)
    return minimum_inner_range


def _find_minimum_range_from_loops(loops: List[Loop] | None):
    """find minimum range from same level loops"""
    if loops is None or len(loops) <= 0:
        return np.array([], dtype=object)
    minimum_range = loops[0].range
    minimum_range_length = len(loops[0].range)
    for loop in loops:
        if len(loop.range) < minimum_range_length:
            minimum_range = loop.range
            minimum_range_length = len(loop.range)
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
