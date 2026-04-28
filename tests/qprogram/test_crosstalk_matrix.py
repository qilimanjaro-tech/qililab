import numpy as np
import pytest

from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix, FluxVector, NonLinearCrosstalkMatrix


@pytest.fixture(name="crosstalk_array_buses")
def get_xtalk_array():
    """Get a tuple of crosstalk array and buses"""
    xtalk_array = np.array([[1, 0.2, 0.3], [0.1, 1, 0.3], [0, 1, 0]])
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
    flux_0  1       0.2     0.3
    flux_1  0.1     1       0.3
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

    def test_get_bias(self, flux_vector):
        flux_vector.bias_vector = {"flux_0": 0.1, "flux_1": 0.2, "flux_2": 0.3}
        assert flux_vector["flux_0"] == 0.1

    def test_set_crosstalk_from_bias(self, flux_vector, crosstalk_matrix):
        flux = flux_vector.set_crosstalk_from_bias(crosstalk_matrix)
        assert flux_vector.crosstalk == crosstalk_matrix
        assert flux_vector.flux_vector == flux
        assert flux_vector.to_dict() == flux_vector.bias_vector

    def test_set_crosstalk_empty_flux_vector(self, crosstalk_matrix):
        flux_vector = FluxVector()
        flux_vector.set_crosstalk(crosstalk_matrix)
        assert flux_vector.crosstalk == crosstalk_matrix
        assert flux_vector.to_dict() == flux_vector.bias_vector

    def test_set_list(self, crosstalk_matrix):
        flux_vector = FluxVector()
        flux_vector.set_crosstalk(crosstalk_matrix)
        flux_vector["flux_0"] = [1, 2, 3, 4, 5]

        assert np.array_equal(flux_vector.flux_vector["flux_0"], np.array([1, 2, 3, 4, 5]))

    def test_set_crosstalk_from_bias_set_vector(self, flux_vector, crosstalk_matrix):
        flux = flux_vector.set_crosstalk_from_bias(
            crosstalk_matrix, bias_vector={"flux_0": 0.1, "flux_1": 0.2, "flux_2": 0.3}
        )
        assert flux_vector.crosstalk == crosstalk_matrix
        assert flux_vector.flux_vector == flux
        assert flux_vector.to_dict() == flux_vector.bias_vector

    def test_get_decomposed_vector(self, flux_vector, crosstalk_matrix):
        flux_vector.set_crosstalk_from_bias(crosstalk_matrix, bias_vector={"flux_0": 0.1, "flux_1": 0.2, "flux_2": 0.3})
        assert flux_vector.crosstalk == crosstalk_matrix
        flux_no_bus_list = flux_vector.get_decomposed_vector()
        flux_bus_list = flux_vector.get_decomposed_vector(bus_list=["flux_0", "flux_1"])
        assert flux_no_bus_list["flux_0"].flux_vector == pytest.approx({"flux_0": 0.23, "flux_1": 0, "flux_2": 0})
        assert flux_no_bus_list["flux_0"].bias_vector == pytest.approx(
            {"flux_0": 0.2555555555555556, "flux_1": 0.0, "flux_2": -0.08518518518518518}
        )
        assert flux_no_bus_list["flux_1"].flux_vector == pytest.approx({"flux_0": 0, "flux_1": 0.3, "flux_2": 0})
        assert flux_no_bus_list["flux_1"].bias_vector == pytest.approx(
            {"flux_0": -1 / 3, "flux_1": 0.0, "flux_2": 10 / 9}
        )
        assert flux_no_bus_list["flux_2"].flux_vector == pytest.approx({"flux_0": 0, "flux_1": 0, "flux_2": 0.2})
        assert flux_no_bus_list["flux_2"].bias_vector == pytest.approx(
            {"flux_0": 8 / 45, "flux_1": 0.2, "flux_2": -98 / 135}
        )
        assert flux_bus_list["flux_0"].flux_vector == pytest.approx({"flux_0": 0.23, "flux_1": 0, "flux_2": 0.2})
        assert flux_bus_list["flux_0"].bias_vector == pytest.approx(
            {"flux_0": 13 / 30, "flux_1": 0.2, "flux_2": -73 / 90}
        )
        assert flux_bus_list["flux_1"].flux_vector == pytest.approx({"flux_0": 0, "flux_1": 0.3, "flux_2": 0.2})
        assert flux_bus_list["flux_1"].bias_vector == pytest.approx(
            {"flux_0": -7 / 45, "flux_1": 0.2, "flux_2": 52 / 135}
        )

    def test_set_crosstalk_applies_nonlinear_corrections(self, crosstalk_matrix):
        """Regression test for the bug reported: FluxVector.set_crosstalk must apply
        nonlinear corrections when given a NonLinearCrosstalkMatrix, not silently
        fall back to the linear path."""
        nonlinear = NonLinearCrosstalkMatrix.from_linear(crosstalk_matrix)
        nonlinear.set_non_linear_params("flux_0", "flux_2", beta_c=-0.234, amplitude=-0.021)
        nonlinear.set_non_linear_params("flux_1", "flux_2", beta_c=-0.253, amplitude=-0.021)

        flux_dict = {"flux_0": 0.1, "flux_1": 0.2, "flux_2": 0.05}

        fv_linear = FluxVector.from_dict(flux_dict.copy())
        fv_linear.set_crosstalk(NonLinearCrosstalkMatrix.from_linear(crosstalk_matrix))

        fv_nonlinear = FluxVector.from_dict(flux_dict.copy())
        fv_nonlinear.set_crosstalk(nonlinear)

        # if nonlinear corrections were silently ignored the two bias vectors
        # would be equal — the original bug
        assert any(
            fv_nonlinear.bias_vector[bus] != pytest.approx(fv_linear.bias_vector[bus], rel=1e-6) for bus in flux_dict
        )

    def test_set_crosstalk_nonlinear_matches_flux_to_bias(self, crosstalk_matrix):
        """FluxVector.set_crosstalk with NonLinearCrosstalkMatrix must produce
        the same result as calling flux_to_bias directly."""
        nonlinear = NonLinearCrosstalkMatrix.from_linear(crosstalk_matrix)
        nonlinear.set_non_linear_params("flux_0", "flux_2", beta_c=-0.234, amplitude=-0.021)
        nonlinear.set_non_linear_params("flux_1", "flux_2", beta_c=-0.253, amplitude=-0.021)

        flux_dict = {"flux_0": 0.1, "flux_1": 0.2, "flux_2": 0.05}

        fv = FluxVector.from_dict(flux_dict.copy())
        fv.set_crosstalk(nonlinear)

        expected = nonlinear.flux_to_bias(flux_dict)
        for bus in flux_dict:
            assert fv.bias_vector[bus] == pytest.approx(expected[bus], rel=1e-6)


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

    def test_set_offset_raises_error_bus_not_in_matrix(self):
        """Test set_offset function"""
        crosstalk_matrix = CrosstalkMatrix()
        crosstalk_matrix["bus1"]["bus1"] = 1
        crosstalk_matrix["bus1"]["bus2"] = 0.5
        crosstalk_matrix["bus2"]["bus1"] = 0.7
        crosstalk_matrix["bus2"]["bus2"] = 1

        with pytest.raises(ValueError, match="Bus bus3 not included inside matrix."):
            crosstalk_matrix.set_offset(offset={"bus1": -1.0, "bus3": 0.5})

    def test_set_resistances(self):
        """Test set_resistances function"""
        crosstalk_matrix = CrosstalkMatrix()
        crosstalk_matrix["bus1"] = {"bus1": 1, "bus2": 0.5}
        crosstalk_matrix["bus2"]["bus1"] = 0.7
        crosstalk_matrix["bus2"]["bus2"] = 1

        # Before setting the resistance but after doing a set for bus_1 and bus_2
        assert crosstalk_matrix.resistances == {"bus1": None}

        crosstalk_matrix.set_resistances(resistances={"bus1": 1000, "bus2": 1005})

        assert isinstance(crosstalk_matrix.resistances, dict)
        assert crosstalk_matrix.resistances == {"bus1": 1000, "bus2": 1005}

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

    def test_flux_to_bias(self, crosstalk_matrix):
        """Test CrosstalkMatrix.flux_to_bias matches manual linear inversion."""
        flux_dict = {"flux_0": 0.1, "flux_1": 0.2, "flux_2": 0.05}
        bias = crosstalk_matrix.flux_to_bias(flux_dict)

        sorted_buses = sorted(flux_dict.keys())
        flux_arr = np.array([flux_dict[b] for b in sorted_buses])
        offsets = np.array([crosstalk_matrix.flux_offsets.get(b, 0.0) for b in sorted_buses])
        expected = np.linalg.inv(crosstalk_matrix.to_array()) @ (flux_arr - offsets)

        for i, bus in enumerate(sorted_buses):
            assert bias[bus] == pytest.approx(expected[i], rel=1e-6)
