""" Tests for CoordinateDecompose"""

from qililab.utils import coordinate_decompose


class TestCoordinateDecompose:
    """Unit tests checking the Experiment attributes and methods"""

    def test_coordinate_decompose_trivial_case(self):
        """Test that coordinate decomposition works well for the trivial case: 1D to 1D"""
        original_array = list(range(10))
        original_size = len(original_array)
        new_dimension_shape = [original_size]
        for index in original_array:
            new_indices = coordinate_decompose(
                new_dimension_shape=new_dimension_shape, original_size=original_size, original_idx=index
            )
            assert new_indices[0] == index

    def test_coordinate_decompose_2d(self):
        """Test that coordinate decomposition works well for the trivial case: 1D to 2D"""
        original_array = list(range(2 * 5))
        original_size = len(original_array)
        new_dimension_shape = [2, 5]

        test_index = 7
        target_result = [1, 2]

        new_indices = coordinate_decompose(
            new_dimension_shape=new_dimension_shape, original_size=original_size, original_idx=test_index
        )

        assert all(target_result == new_indices)

    def test_coordinate_decompose_3d(self):
        """Test that coordinate decomposition works well for the trivial case: 1D to 3D"""
        original_array = list(range(2 * 3 * 5))
        original_size = len(original_array)
        new_dimension_shape = [2, 3, 5]

        test_index = 27
        target_result = [1, 2, 2]

        new_indices = coordinate_decompose(
            new_dimension_shape=new_dimension_shape, original_size=original_size, original_idx=test_index
        )

        assert all(target_result == new_indices)

    def test_coordinate_decompose_4d(self):
        """Test that coordinate decomposition works well for the trivial case: 1D to 3D"""
        original_array = list(range(2 * 2 * 2 * 2))
        original_size = len(original_array)
        new_dimension_shape = [2, 2, 2, 2]

        test_index = 5
        target_result = [0, 1, 0, 1]

        new_indices = coordinate_decompose(
            new_dimension_shape=new_dimension_shape, original_size=original_size, original_idx=test_index
        )

        assert all(target_result == new_indices)
