import numpy as np
import pytest

from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix, NonLinearCrosstalkMatrix


@pytest.fixture(name="crosstalk_array_buses")
def get_xtalk_array():
    """Get a tuple of crosstalk array and buses"""
    xtalk_array = np.array([[1, 0.2, 0.3], [0.1, 1, 0.3], [0, 1, 0]])
    buses = ["flux_0", "flux_1", "flux_2"]
    return (xtalk_array, buses)


@pytest.fixture(name="crosstalk_matrix")
def get_xtalk_matrix(crosstalk_array_buses):
    """Crosstalk matrix for the following xtalk
            flux_0  flux_1  flux_2
    flux_0  1       0.2     0.3
    flux_1  0.1     1       0.3
    flux_2  0       1       0
    """
    return CrosstalkMatrix.from_array(buses=crosstalk_array_buses[1], matrix_array=crosstalk_array_buses[0])

@pytest.fixture(name="non_linear_crosstalk_matrix")
def get_nl_xtalk_matrix(crosstalk_matrix):
    """Non Linear Crosstalk matrix for the following xtalk
            flux_0  flux_1  flux_2
    flux_0  1       0.2     0.3
    flux_1  0.1     1       0.3
    flux_2  0       1       0
    With no non-linear parameters.
    """
    nl_xtalk = NonLinearCrosstalkMatrix.from_linear(crosstalk_matrix)
    return nl_xtalk


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
        
    def test_to_array_two_independent_qubits(self):
        """Test to_array method when two independent qubits added
        The matrix has missing elements of the dictionary.
        """
        # Create the CrosstalkMatrix for qubit 1, only flux1_z and flux1_x
        crosstalk_matrix = CrosstalkMatrix.from_buses(
            buses={"flux1_z": {"flux1_x": 0.1, "flux1_z": 1.0}, "flux1_x": {"flux1_x": 1.0, "flux1_z": 0.5}}
        )

        # Add the elements for qubit 2, only flux2_z and flux2_x
        crosstalk_matrix["flux2_x"] = {"flux2_z": 0.3, "flux2_x": 1}
        crosstalk_matrix["flux2_z"] = {"flux2_z": 1, "flux2_x": 0.4}

        crosstalk_q1 = np.array([[1.0, 0.5], [0.1, 1.0]])
        crosstalk_q2 = np.array([[1.0, 0.3], [0.4, 1.0]])
        full_crosstalk = np.eye(4)
        full_crosstalk[0:2, 0:2] = crosstalk_q1  # first component is qubit 1
        full_crosstalk[2:4, 2:4] = crosstalk_q2  # second component is qubit 2
        # Elements outside the diagonal should be empty

        # Get and compare the crosstalk matrix as an array
        assert np.allclose(crosstalk_matrix.to_array(), full_crosstalk)

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

    def test_str_method_independent_value(self):
        """Test __str__ method"""
        crosstalk_matrix = CrosstalkMatrix()
        crosstalk_matrix["bus1"]["bus1"] = -0.5
        crosstalk_matrix["bus1"]["bus2"] = 0.5
        crosstalk_matrix["bus2"]["bus1"] = 0.7
        crosstalk_matrix["bus2"]["bus2"] = -0.5
        # New bus
        crosstalk_matrix["bus3"]["bus3"] = 0.2

        string = str(crosstalk_matrix)
        assert (
            string
            == """            bus1     bus2     bus3
bus1         -0.5      0.5      0.0
bus2          0.7     -0.5      0.0
bus3          0.0      0.0      0.2"""
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

    def test_flux_to_bias_with_array(self, crosstalk_matrix):
        """flux_to_bias should work element-wise when flux values are numpy arrays."""
        flux_dict = {
            "flux_0": np.array([0.1, 0.2, 0.3]),
            "flux_1": np.array([0.2, 0.3, 0.4]),
            "flux_2": np.array([0.05, 0.1, 0.15]),
        }
        bias = crosstalk_matrix.flux_to_bias(flux_dict)

        # check each point matches the scalar result
        for i in range(3):
            scalar_flux = {bus: float(flux_dict[bus][i]) for bus in flux_dict}
            scalar_bias = crosstalk_matrix.flux_to_bias(scalar_flux)
            for bus in flux_dict:
                assert float(bias[bus][i]) == pytest.approx(scalar_bias[bus], rel=1e-6)


class TestNonLinearCrosstalkMatrix:
    def test_from_linear_preserves_matrix(self, non_linear_crosstalk_matrix, crosstalk_matrix):
        assert non_linear_crosstalk_matrix.matrix == crosstalk_matrix.matrix

    def test_from_linear_initializes_nonlinear_to_none(self, non_linear_crosstalk_matrix):
        for bus_i in non_linear_crosstalk_matrix.matrix:
            for bus_j in non_linear_crosstalk_matrix.matrix[bus_i]:
                assert non_linear_crosstalk_matrix.beta_c_matrix[bus_i][bus_j] is None
                assert non_linear_crosstalk_matrix.non_lin_amp_matrix[bus_i][bus_j] is None

    def test_set_non_linear_params(self, non_linear_crosstalk_matrix):
        non_linear_crosstalk_matrix.set_non_linear_params("flux_0", "flux_1", beta_c=-0.3, amplitude=-0.08)
        assert non_linear_crosstalk_matrix.beta_c_matrix["flux_0"]["flux_1"] == pytest.approx(-0.3)
        assert non_linear_crosstalk_matrix.non_lin_amp_matrix["flux_0"]["flux_1"] == pytest.approx(-0.08)

    def test_set_non_linear_params_raises_on_partial_params(self, non_linear_crosstalk_matrix):
        with pytest.raises(ValueError, match="Both 'amplitude' and 'beta_c' must be provided together"):
            non_linear_crosstalk_matrix.set_non_linear_params("flux_0", "flux_1", beta_c=-0.3)
        with pytest.raises(ValueError, match="Both 'amplitude' and 'beta_c' must be provided together"):
            non_linear_crosstalk_matrix.set_non_linear_params("flux_0", "flux_1", amplitude=-0.08)

    def test_set_non_linear_params_raises_on_zero_beta_c(self, non_linear_crosstalk_matrix):
        with pytest.raises(ValueError, match="beta_c cannot be zero"):
            non_linear_crosstalk_matrix.set_non_linear_params("flux_0", "flux_1", beta_c=0, amplitude=-0.08)

    def test_set_non_linear_params_junction_asym_only(self, non_linear_crosstalk_matrix):
        non_linear_crosstalk_matrix.set_non_linear_params("flux_0", "flux_1", junction_asym=0.02)
        assert non_linear_crosstalk_matrix.junction_asym_matrix["flux_0"]["flux_1"] == pytest.approx(0.02)

    def test_set_non_linear_params_raises_on_missing_bus(self, non_linear_crosstalk_matrix):
        with pytest.raises(ValueError, match="not present in the crosstalk matrix"):
            non_linear_crosstalk_matrix.set_non_linear_params("nonexistent", "flux_1", beta_c=-0.3, amplitude=-0.08)

    def test_sin_beta_scaled_zero_at_zero_flux(self, non_linear_crosstalk_matrix):
        result = non_linear_crosstalk_matrix.sin_beta_scaled(flux=0.0, beta=-0.234, amp=-0.021)
        assert result == pytest.approx(0.0, abs=1e-10)

    def test_sin_beta_scaled_array_input(self, non_linear_crosstalk_matrix):
        flux = np.array([0.0, 0.1, 0.5])
        result = non_linear_crosstalk_matrix.sin_beta_scaled(flux=flux, beta=-0.234, amp=-0.021)
        assert result.shape == flux.shape

    def test_sin_beta_scaled_raises_on_nan_amplitude(self, non_linear_crosstalk_matrix):
        with pytest.raises(ValueError, match="Amplitude cannot be NaN"):
            non_linear_crosstalk_matrix.sin_beta_scaled(flux=0.1, beta=-0.234, amp=float("nan"))

    def test_junction_asymmetry_correction_zero_for_symmetric_squid(self, non_linear_crosstalk_matrix):
        result = non_linear_crosstalk_matrix.junction_asymmetry_correction(flux_x=0.25, d=0.0)
        assert result == pytest.approx(0.0, abs=1e-10)

    def test_junction_asymmetry_correction_known_value(self, non_linear_crosstalk_matrix):
        flux_x = 0.25
        d = 1.0
        phi_d = np.arctan(d * np.tan(np.pi * flux_x))
        expected = -phi_d / (2 * np.pi)
        result = non_linear_crosstalk_matrix.junction_asymmetry_correction(flux_x=flux_x, d=d)
        assert result == pytest.approx(expected, rel=1e-6)

    def test_junction_asymmetry_correction_array_input(self, non_linear_crosstalk_matrix):
        flux_x = np.array([0.0, 0.1, 0.25, 0.5])
        result = non_linear_crosstalk_matrix.junction_asymmetry_correction(flux_x=flux_x, d=0.5)
        assert isinstance(result, np.ndarray)
        assert result.shape == flux_x.shape

    def test_junction_asymmetry_correction_raises_on_nan_d(self, non_linear_crosstalk_matrix):
        with pytest.raises(ValueError, match="Junction asymetry cannot be NaN"):
            non_linear_crosstalk_matrix.junction_asymmetry_correction(flux_x=0.1, d=float("nan"))

    def test_flux_to_bias_no_nonlinear_matches_linear_inversion(self, non_linear_crosstalk_matrix):
        flux_vector_dict = {"flux_0": 0.5, "flux_1": 1, "flux_2": 0}
        bias = non_linear_crosstalk_matrix.flux_to_bias(flux_vector_dict)

        sorted_buses = sorted(flux_vector_dict.keys())
        flux_arr = np.array([flux_vector_dict[b] for b in sorted_buses])
        offsets = np.array([non_linear_crosstalk_matrix.flux_offsets.get(b, 0.0) for b in sorted_buses])
        expected = np.linalg.inv(non_linear_crosstalk_matrix.to_array()) @ (flux_arr - offsets)

        for i, bus in enumerate(sorted_buses):
            assert bias[bus] == pytest.approx(expected[i], rel=1e-6)

    def test_flux_to_bias_with_nonlinear_differs_from_linear(self, non_linear_crosstalk_matrix, crosstalk_matrix):
        non_linear_crosstalk_matrix.set_non_linear_params("flux_0", "flux_2", beta_c=-0.234, amplitude=-0.021)
        flux = {"flux_0": 0.1, "flux_1": 0.2, "flux_2": 0.05}
        bias_nonlinear = non_linear_crosstalk_matrix.flux_to_bias(flux)

        linear = NonLinearCrosstalkMatrix.from_linear(crosstalk_matrix)
        bias_linear = linear.flux_to_bias(flux)

        assert any(bias_nonlinear[bus] != pytest.approx(bias_linear[bus], rel=1e-6) for bus in flux)

