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

import numpy as np
import numpy.typing as npt


def product(array: npt.NDArray | list | tuple, start: int = 0, stop: int = -1):
    """Takes in an array and does the product-of-a-sequence of the elements between `start_index` and `end_index`"""
    if stop == -1:
        stop = len(array)

    return 1 if stop - start <= 0 else np.prod(array[start:stop])


def summation(array: npt.NDArray | list | tuple, start: int = 0, stop: int = -1):
    """Takes in an array and does the summation of the elements between `start_index` and `end_index`"""
    if stop == -1:
        stop = len(array)

    return 0 if stop - start <= 0 else np.sum(array[start:stop])


def _do_target_dimensions_check(new_dimension_shape: npt.NDArray | list | tuple):
    """Checks that all target dimensions should have at least one element."""
    if any(size < 1 for size in new_dimension_shape):
        raise ValueError(f"Sizes of of target array should not be 0 nor negative: {str(new_dimension_shape)}")


def _do_size_match_check(original_size: int, new_dimension_shape: npt.NDArray | list | tuple):
    """Checks that sizes of original and target spaces are compatible."""
    new_space_size = np.prod(new_dimension_shape)
    if new_space_size != original_size:
        raise ValueError(
            f"Sizes of original and target arrays do not match:"
            f" original size {original_size} does not match"
            f" size of {str(new_dimension_shape)}: {new_space_size}"
        )


def _coordinate_decomposition_checks(original_size: int, new_dimension_shape: npt.NDArray | list | tuple):
    """Perform some checks before applying the algorithm"""
    _do_target_dimensions_check(new_dimension_shape=new_dimension_shape)
    _do_size_match_check(original_size=original_size, new_dimension_shape=new_dimension_shape)


def _get_nth_coordinate(
    coord_elem_idx: int,
    new_indices: npt.NDArray | list | tuple,
    original_idx: int,
    new_dimension_shape: npt.NDArray | list | tuple,
    number_of_dimensions: int,
):
    """Builds precisely the i_k by using:
    i_k = ((r - sum_{p=k+1}^{D-1}(i_p*prod_{l=p+1}*{D-1}(I_l))) / (prod_{l+1}^{D-1}(I_l))) % I_k"""

    numerator_series_elements = [
        new_indices[k] * product(new_dimension_shape, start=k + 1, stop=number_of_dimensions)
        for k in range(coord_elem_idx + 1, number_of_dimensions)
    ]
    numerator = original_idx - summation(numerator_series_elements, start=coord_elem_idx + 1, stop=number_of_dimensions)
    denominator = product(new_dimension_shape, start=coord_elem_idx + 1, stop=number_of_dimensions)
    modulus = new_dimension_shape[coord_elem_idx]

    return (numerator / denominator) % modulus


def coordinate_decompose(
    new_dimension_shape: npt.NDArray | list | tuple,
    original_size: int,
    original_idx: int,
):
    """Converts an index from a 1D array to an index in an NDArray, as long as both expressions have the same sizes.
    i.e. expresses the index r in an array of R elements as the indices [n, m, l] of nested arrays with shape [N, M, L],
    as log as N*M*L==R.
    In this case, we can see that r can be expressed as r = n*M*L + m*L + l
    Mod-Dividing each side by L:
    l = r % L
    Isolating m and mod-dividing by M:
    m = ((r - l) / (M*L) ) % M
    Isolating n and mod-dividing by N:
    n = ((r - l - m*L) / (N*M*L)) % N

    In general, r can be expressed as r = sum_{k=0}^{D-1} (i_k) * prod_{l=k+1}^{D-1} (I_k), where:
     * i_k is the index in the kth dimension, for k belonging to [0, D-1]
     * I_k is the size of the kth dimension, for k belonging to [0, D-1]
     * D is the number of dimensions

    This can be inverted to get the i_k component, assuming we already know [i_{k+1}, ..., i_{D-1}]:
    i_k = ((r - sum_{p=k+1}^{D-1}(i_p*prod_{l=p+1}*{D-1}(I_l))) / (prod_{l+1}^{D-1}(I_l))) % I_k

    Args:
        new_dimension_shape: array containing the sizes of the dimensions: `{I_k}`
        original_size: number of elements in the original space, for checking compatibility
        original_idx: index of the element in the original array: `r`

    Returns: array of new indices.

    """

    _coordinate_decomposition_checks(original_size=original_size, new_dimension_shape=new_dimension_shape)

    number_of_dimensions = len(new_dimension_shape)
    new_indices = np.zeros_like(new_dimension_shape)

    for coord_elem_idx in reversed(range(len(new_dimension_shape))):
        new_indices[coord_elem_idx] = _get_nth_coordinate(
            coord_elem_idx=coord_elem_idx,
            new_indices=new_indices,
            original_idx=original_idx,
            new_dimension_shape=new_dimension_shape,
            number_of_dimensions=number_of_dimensions,
        )

    return new_indices
