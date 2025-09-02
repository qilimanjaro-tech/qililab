import numpy as np
import pytest

from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix, FluxVector


@pytest.fixture(name="crosstalk_array_buses")
def get_xtalk_array():
    """Get a tuple of crosstalk array and buses"""
    xtalk_array = np.array([[1, 2, 3], [0.1, 0.2, 0.3], [0, 1, 0]])
    buses = ["flux_0", "flux_1", "flux_2"]
    return (xtalk_array, buses)


@pytest.fixture(name="flux_vector_dict")
def get_flux_vector_dict():
    return {"flux_0": 0.5, "flux_1": 1, "flux_2": 0}


@pytest.fixture(name="flux_vector")
def get_flux_vector(flux_vector_dict):
    """Get a flux vector from CrosstalkMatrix.FluxVector"""
    return FluxVector.from_dict(flux_vector_dict)


@pytest.fixture(name="crosstalk_matrix")
def get_xtalk_matrix(crosstalk_array_buses):
    """Crosstalk matrix for the following xtalk
            flux_0  flux_1  flux_2
    flux_0  1       2       3
    flux_1  0.1     0.2     0.3
    flux_2  0       1       0
    """
    return CrosstalkMatrix.from_array(buses=crosstalk_array_buses[1], matrix_array=crosstalk_array_buses[0])


class TestFluxVector:
    """Unit test for the FluxVector class"""

    def test_init(self):
        flux_vector = FluxVector()
        assert flux_vector.bias_vector == {}

    def test_from_dict(self, flux_vector, flux_vector_dict):
        assert flux_vector.flux_vector == flux_vector_dict

    def test_to_dict(self, flux_vector, flux_vector_dict):
        assert flux_vector.to_dict() == flux_vector_dict

    def test_get(self, flux_vector):
        assert flux_vector["flux_0"] == 0.5

    def test_set_crosstalk_from_bias(self, flux_vector, crosstalk_matrix):
        flux = flux_vector.set_crosstalk_from_bias(crosstalk_matrix)
        assert flux_vector.crosstalk == crosstalk_matrix
        assert flux_vector.flux_vector == flux
        assert flux_vector.to_dict() == flux_vector.bias_vector

    def test_set_crosstalk_from_bias_set_vector(self, flux_vector, crosstalk_matrix):
        flux = flux_vector.set_crosstalk_from_bias(
            crosstalk_matrix, bias_vector={"flux_0": 0.1, "flux_1": 0.2, "flux_2": 0.3}
        )
        assert flux_vector.crosstalk == crosstalk_matrix
        assert flux_vector.flux_vector == flux
        assert flux_vector.to_dict() == flux_vector.bias_vector


class TestCrosstalkMatrix:
    """Unit tests checking the Calibration attributes and methods."""

    def test_from_array(self, crosstalk_matrix, crosstalk_array_buses):
        """Test that from array works as intended"""
        xtalk_array, buses = crosstalk_array_buses
        assert (
            sum(
                crosstalk_matrix[bus1][bus2] == xtalk_array[i, j]
                for i, bus1 in enumerate(buses)
                for j, bus2 in enumerate(buses)
            )
            == xtalk_array.shape[0] * xtalk_array.shape[1]
        )

    def test_to_array(self, crosstalk_matrix, crosstalk_array_buses):
        assert np.allclose(crosstalk_matrix.to_array(), crosstalk_array_buses[0])

    def test_inverse(self, crosstalk_matrix):
        inv_array = np.linalg.inv(crosstalk_matrix.to_array())
        inv_matrix = crosstalk_matrix.inverse()
        assert (
            sum(
                inv_matrix[bus1][bus2] == inv_array[i, j]
                for i, bus1 in enumerate(inv_matrix.matrix.keys())
                for j, bus2 in enumerate(inv_matrix.matrix.keys())
            )
            == inv_array.shape[0] * inv_array.shape[1]
        )

    def test_init(self):
        """Test init method"""
        crosstalk_matrix = CrosstalkMatrix()

        assert isinstance(crosstalk_matrix, CrosstalkMatrix)
        assert isinstance(crosstalk_matrix.matrix, dict)
        assert len(crosstalk_matrix.matrix) == 0

    def test_set_get_methods(self):
        """Test __setitem__ and __getitem__ methods"""
        crosstalk_matrix = CrosstalkMatrix()
        crosstalk_matrix["bus1"]["bus2"] = 0.5

        assert isinstance(crosstalk_matrix["bus1"], dict)
        assert len(crosstalk_matrix["bus1"]) == 1
        assert crosstalk_matrix["bus1"]["bus2"] == 0.5

        # Reshape a given key
        crosstalk_matrix["bus1"] = {"bus2": 0.6}
        assert isinstance(crosstalk_matrix["bus1"], dict)
        assert len(crosstalk_matrix["bus1"]) == 1
        assert crosstalk_matrix["bus1"]["bus2"] == 0.6

        # New key
        crosstalk_matrix["bus2"] = {"bus1": 0.1}
        assert isinstance(crosstalk_matrix["bus2"], dict)
        assert len(crosstalk_matrix["bus2"]) == 1
        assert crosstalk_matrix["bus2"]["bus1"] == 0.1

    def test_set_offset(self):
        """Test set_offset function"""
        crosstalk_matrix = CrosstalkMatrix()
        crosstalk_matrix["bus1"]["bus1"] = 1
        crosstalk_matrix["bus1"]["bus2"] = 0.5
        crosstalk_matrix["bus2"]["bus1"] = 0.7
        crosstalk_matrix["bus2"]["bus2"] = 1

        crosstalk_matrix.set_offset(offset={"bus1": -1.0, "bus2": 0.5})

        assert isinstance(crosstalk_matrix.flux_offsets, dict)
        assert crosstalk_matrix.flux_offsets == {"bus1": -1.0, "bus2": 0.5}

    def test_str_method(self):
        """Test __str__ method"""
        crosstalk_matrix = CrosstalkMatrix()
        crosstalk_matrix["bus1"]["bus1"] = -0.5
        crosstalk_matrix["bus1"]["bus2"] = 0.5
        crosstalk_matrix["bus2"]["bus1"] = 0.7
        crosstalk_matrix["bus2"]["bus2"] = -0.5

        string = str(crosstalk_matrix)
        assert (
            string
            == """            bus1     bus2
bus1         -0.5      0.5
bus2          0.7     -0.5"""
        )

    def test_repr_method(self):
        """Test __repr__ method"""
        crosstalk_matrix = CrosstalkMatrix()
        crosstalk_matrix["bus1"]["bus1"] = -0.5
        crosstalk_matrix["bus1"]["bus2"] = 0.5
        crosstalk_matrix["bus2"]["bus1"] = 0.7
        crosstalk_matrix["bus2"]["bus2"] = -0.5

        representation = repr(crosstalk_matrix)
        assert (
            representation
            == "CrosstalkMatrix({'bus1': {'bus1': -0.5, 'bus2': 0.5}, 'bus2': {'bus1': 0.7, 'bus2': -0.5}})"
        )

    def test_from_buses_method(self):
        """Test from_buses class method"""
        buses = {
            "bus1": {"bus1": 1.0, "bus2": 1.0, "bus3": 1.0},
            "bus2": {"bus1": 1.0, "bus2": 1.0, "bus3": 1.0},
            "bus3": {"bus1": 1.0, "bus2": 1.0, "bus3": 1.0},
        }
        crosstalk_matrix = CrosstalkMatrix.from_buses(buses)

        assert isinstance(crosstalk_matrix, CrosstalkMatrix)
        assert isinstance(crosstalk_matrix.matrix, dict)

        assert "bus1" in crosstalk_matrix.matrix
        assert "bus2" in crosstalk_matrix.matrix["bus1"]
        assert "bus3" in crosstalk_matrix.matrix["bus1"]
        assert crosstalk_matrix["bus1"]["bus2"] == 1.0
        assert crosstalk_matrix["bus1"]["bus3"] == 1.0

        assert "bus2" in crosstalk_matrix.matrix
        assert "bus1" in crosstalk_matrix.matrix["bus2"]
        assert "bus3" in crosstalk_matrix.matrix["bus2"]
        assert crosstalk_matrix["bus2"]["bus1"] == 1.0
        assert crosstalk_matrix["bus2"]["bus3"] == 1.0

        assert "bus3" in crosstalk_matrix.matrix
        assert "bus1" in crosstalk_matrix.matrix["bus3"]
        assert "bus2" in crosstalk_matrix.matrix["bus3"]
        assert crosstalk_matrix["bus3"]["bus1"] == 1.0
        assert crosstalk_matrix["bus3"]["bus2"] == 1.0
