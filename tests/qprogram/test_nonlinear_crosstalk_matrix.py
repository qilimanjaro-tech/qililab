import numpy as np
import pytest
from scipy.special import jv

from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix, NonLinearCrosstalkMatrix


@pytest.fixture(name="linear_crosstalk_matrix")
def get_linear_crosstalk_matrix():
    """Linear crosstalk matrix for the following xtalk:
            flux_0  flux_1  flux_2
    flux_0  1       0.2     0.3
    flux_1  0.1     1       0.3
    flux_2  0       1       0
    """
    xtalk_array = np.array([[1, 0.2, 0.3], [0.1, 1, 0.3], [0, 1, 0]])
    buses = ["flux_0", "flux_1", "flux_2"]
    return CrosstalkMatrix.from_array(buses=buses, matrix_array=xtalk_array)


@pytest.fixture(name="nonlinear_crosstalk_matrix")
def get_nonlinear_crosstalk_matrix(linear_crosstalk_matrix):
    """NonLinearCrosstalkMatrix built from a linear one with nonlinear params set
    for the (flux_0, flux_2) and (flux_1, flux_2) pairs."""
    xtalk = NonLinearCrosstalkMatrix.from_linear(linear_crosstalk_matrix)
    xtalk.set_non_linear_params("flux_0", "flux_2", beta_c=-0.234, amplitude=-0.021)
    xtalk.set_non_linear_params("flux_1", "flux_2", beta_c=-0.253, amplitude=-0.021)
    return xtalk


@pytest.fixture(name="flux_dict")
def get_flux_dict():
    return {"flux_0": 0.1, "flux_1": 0.2, "flux_2": 0.05}


class TestNonLinearCrosstalkMatrixInit:
    """Tests for __init__ and basic structure."""

    def test_init_empty(self):
        xtalk = NonLinearCrosstalkMatrix()
        assert isinstance(xtalk.matrix, dict)
        assert isinstance(xtalk.beta_c_matrix, dict)
        assert isinstance(xtalk.non_lin_amp_matrix, dict)
        assert len(xtalk.matrix) == 0
        assert len(xtalk.beta_c_matrix) == 0
        assert len(xtalk.non_lin_amp_matrix) == 0

    def test_inherits_from_crosstalk_matrix(self):
        xtalk = NonLinearCrosstalkMatrix()
        assert isinstance(xtalk, CrosstalkMatrix)

    def test_setitem_initializes_nonlinear_entries(self):
        xtalk = NonLinearCrosstalkMatrix()
        xtalk["flux_0"] = {"flux_0": 1.0, "flux_1": 0.2}

        assert "flux_0" in xtalk.beta_c_matrix
        assert xtalk.beta_c_matrix["flux_0"]["flux_0"] is None
        assert xtalk.beta_c_matrix["flux_0"]["flux_1"] is None
        assert xtalk.non_lin_amp_matrix["flux_0"]["flux_0"] is None
        assert xtalk.non_lin_amp_matrix["flux_0"]["flux_1"] is None

    def test_setitem_does_not_overwrite_existing_nonlinear_entries(self):
        xtalk = NonLinearCrosstalkMatrix()
        xtalk["flux_0"] = {"flux_0": 1.0, "flux_1": 0.2}
        xtalk.beta_c_matrix["flux_0"]["flux_1"] = -0.23
        xtalk.non_lin_amp_matrix["flux_0"]["flux_1"] = -0.02

        # Re-setting the same key should not overwrite nonlinear params
        xtalk["flux_0"] = {"flux_0": 1.0, "flux_1": 0.3}
        assert xtalk.beta_c_matrix["flux_0"]["flux_1"] == -0.23
        assert xtalk.non_lin_amp_matrix["flux_0"]["flux_1"] == -0.02

    def test_setitem_adds_new_bus_to_existing_nonlinear_entries(self):
        """Covers the 'bus not in beta_c_matrix[key]' branch in __setitem__."""
        xtalk = NonLinearCrosstalkMatrix()
        xtalk["flux_0"] = {"flux_0": 1.0, "flux_1": 0.2}

        # Now add a new bus to the same key — should initialise new entry to None
        # without touching the existing ones
        xtalk["flux_0"] = {"flux_0": 1.0, "flux_1": 0.2, "flux_2": 0.3}

        assert xtalk.beta_c_matrix["flux_0"]["flux_2"] is None
        assert xtalk.non_lin_amp_matrix["flux_0"]["flux_2"] is None
        # existing entries untouched
        assert xtalk.beta_c_matrix["flux_0"]["flux_0"] is None
        assert xtalk.beta_c_matrix["flux_0"]["flux_1"] is None

    def test_setitem_adds_new_bus_preserves_existing_nonlinear_params(self):
        """Covers the 'bus not in beta_c_matrix[key]' branch when existing params are set."""
        xtalk = NonLinearCrosstalkMatrix()
        xtalk["flux_0"] = {"flux_0": 1.0, "flux_1": 0.2}
        xtalk.beta_c_matrix["flux_0"]["flux_1"] = -0.23
        xtalk.non_lin_amp_matrix["flux_0"]["flux_1"] = -0.02

        # Add a new bus — should only initialise the new one, not overwrite existing
        xtalk["flux_0"] = {"flux_0": 1.0, "flux_1": 0.2, "flux_2": 0.3}

        assert xtalk.beta_c_matrix["flux_0"]["flux_2"] is None
        assert xtalk.non_lin_amp_matrix["flux_0"]["flux_2"] is None
        assert xtalk.beta_c_matrix["flux_0"]["flux_1"] == -0.23
        assert xtalk.non_lin_amp_matrix["flux_0"]["flux_1"] == -0.02

    def test_raises_on_missing_bus_i_in_flux(self, nonlinear_crosstalk_matrix):
        """Covers bus_i has nonlinear params set but is missing from the flux dict."""
        with pytest.raises(ValueError, match="Bus 'flux_0' has nonlinear parameters set"):
            nonlinear_crosstalk_matrix.get_non_linear_flux_terms({"flux_1": 0.2, "flux_2": 0.05})


class TestFromLinear:
    """Tests for the from_linear classmethod."""

    def test_from_linear_copies_matrix(self, linear_crosstalk_matrix):
        xtalk = NonLinearCrosstalkMatrix.from_linear(linear_crosstalk_matrix)
        assert xtalk.matrix == linear_crosstalk_matrix.matrix

    def test_from_linear_copies_flux_offsets(self, linear_crosstalk_matrix):
        linear_crosstalk_matrix.set_offset({"flux_0": 0.1, "flux_1": -0.1, "flux_2": 0.0})
        xtalk = NonLinearCrosstalkMatrix.from_linear(linear_crosstalk_matrix)
        assert xtalk.flux_offsets == linear_crosstalk_matrix.flux_offsets

    def test_from_linear_copies_resistances(self, linear_crosstalk_matrix):
        linear_crosstalk_matrix.set_resistances({"flux_0": 1000.0, "flux_1": 1005.0, "flux_2": 998.0})
        xtalk = NonLinearCrosstalkMatrix.from_linear(linear_crosstalk_matrix)
        assert xtalk.resistances == linear_crosstalk_matrix.resistances

    def test_from_linear_initializes_nonlinear_to_none(self, linear_crosstalk_matrix):
        xtalk = NonLinearCrosstalkMatrix.from_linear(linear_crosstalk_matrix)
        for bus_i in xtalk.matrix:
            for bus_j in xtalk.matrix[bus_i]:
                assert xtalk.beta_c_matrix[bus_i][bus_j] is None
                assert xtalk.non_lin_amp_matrix[bus_i][bus_j] is None

    def test_from_linear_does_not_share_matrix_reference(self, linear_crosstalk_matrix):
        xtalk = NonLinearCrosstalkMatrix.from_linear(linear_crosstalk_matrix)
        xtalk.matrix["flux_0"]["flux_1"] = 999.0
        assert linear_crosstalk_matrix.matrix["flux_0"]["flux_1"] != 999.0


class TestSetNonLinearParams:
    """Tests for set_non_linear_params."""

    def test_set_non_linear_params(self, nonlinear_crosstalk_matrix):
        assert nonlinear_crosstalk_matrix.beta_c_matrix["flux_0"]["flux_2"] == pytest.approx(-0.234)
        assert nonlinear_crosstalk_matrix.non_lin_amp_matrix["flux_0"]["flux_2"] == pytest.approx(-0.021)
        assert nonlinear_crosstalk_matrix.beta_c_matrix["flux_1"]["flux_2"] == pytest.approx(-0.253)
        assert nonlinear_crosstalk_matrix.non_lin_amp_matrix["flux_1"]["flux_2"] == pytest.approx(-0.021)

    def test_set_non_linear_params_raises_on_missing_bus_i(self, nonlinear_crosstalk_matrix):
        with pytest.raises(ValueError, match="Bus 'nonexistent' not present"):
            nonlinear_crosstalk_matrix.set_non_linear_params("nonexistent", "flux_2", -0.2, -0.02)

    def test_set_non_linear_params_raises_on_missing_bus_j(self, nonlinear_crosstalk_matrix):
        with pytest.raises(ValueError, match="Bus 'nonexistent' not present"):
            nonlinear_crosstalk_matrix.set_non_linear_params("flux_0", "nonexistent", -0.2, -0.02)

    def test_set_non_linear_params_overwrite(self, nonlinear_crosstalk_matrix):
        nonlinear_crosstalk_matrix.set_non_linear_params("flux_0", "flux_2", beta_c=-0.999, amplitude=-0.999)
        assert nonlinear_crosstalk_matrix.beta_c_matrix["flux_0"]["flux_2"] == pytest.approx(-0.999)
        assert nonlinear_crosstalk_matrix.non_lin_amp_matrix["flux_0"]["flux_2"] == pytest.approx(-0.999)

    def test_set_non_linear_params_creates_missing_bus_i_entry(self):
        """Covers the 'bus_i not in beta_c_matrix' branch in set_non_linear_params."""
        xtalk = NonLinearCrosstalkMatrix()
        xtalk["flux_0"] = {"flux_0": 1.0, "flux_1": 0.2}
        xtalk["flux_1"] = {"flux_0": 0.1, "flux_1": 1.0}

        # Manually remove bus_i from the nonlinear dicts to simulate missing entry
        del xtalk.beta_c_matrix["flux_0"]
        del xtalk.non_lin_amp_matrix["flux_0"]

        # set_non_linear_params should recreate the entry
        xtalk.set_non_linear_params("flux_0", "flux_1", beta_c=-0.234, amplitude=-0.021)

        assert xtalk.beta_c_matrix["flux_0"]["flux_1"] == pytest.approx(-0.234)
        assert xtalk.non_lin_amp_matrix["flux_0"]["flux_1"] == pytest.approx(-0.021)
        
    def test_set_non_linear_params_raises_on_zero_beta_c(self, nonlinear_crosstalk_matrix):
        with pytest.raises(ValueError, match="beta_c cannot be zero"):
            nonlinear_crosstalk_matrix.set_non_linear_params("flux_0", "flux_2", beta_c=0, amplitude=-0.021)


class TestSinBetaScaled:
    """Tests for sin_beta_scaled."""

    def test_returns_zero_at_zero_flux(self):
        xtalk = NonLinearCrosstalkMatrix()
        result = xtalk.sin_beta_scaled(flux=0.0, beta=-0.234, amp=-0.021)
        assert result == pytest.approx(0.0, abs=1e-10)

    def test_known_value(self):
        """Manually compute a single-term approximation and compare."""
        xtalk = NonLinearCrosstalkMatrix()
        flux = 0.1
        beta = -0.234
        amp = -0.021
        phi = flux * 2 * np.pi

        expected = 2 * amp * sum((jv(k, k * beta) / (k * beta)) * np.sin(k * phi) for k in range(1, 51))
        result = xtalk.sin_beta_scaled(flux=flux, beta=beta, amp=amp)
        assert result == pytest.approx(expected, rel=1e-6)

    def test_array_input(self):
        xtalk = NonLinearCrosstalkMatrix()
        flux = np.array([0.0, 0.1, 0.2, 0.5])
        result = xtalk.sin_beta_scaled(flux=flux, beta=-0.234, amp=-0.021)
        assert result.shape == flux.shape

    def test_raises_on_nan_amplitude(self):
        xtalk = NonLinearCrosstalkMatrix()
        with pytest.raises(ValueError, match="Amplitude cannot be NaN"):
            xtalk.sin_beta_scaled(flux=0.1, beta=-0.234, amp=float("nan"))

    def test_k_max_convergence(self):
        """Higher k_max should converge to the same value for smooth inputs."""
        xtalk = NonLinearCrosstalkMatrix()
        r_low = xtalk.sin_beta_scaled(flux=0.1, beta=-0.234, amp=-0.021, k_max=20)
        r_high = xtalk.sin_beta_scaled(flux=0.1, beta=-0.234, amp=-0.021, k_max=100)
        assert r_low == pytest.approx(r_high, rel=1e-4)


class TestGetNonLinearFluxTerms:
    """Tests for get_non_linear_flux_terms."""

    def test_returns_zero_for_none_params(self, linear_crosstalk_matrix):
        """With all nonlinear params set to None, corrections should be zero."""
        xtalk = NonLinearCrosstalkMatrix.from_linear(linear_crosstalk_matrix)
        flux = {"flux_0": 0.1, "flux_1": 0.2, "flux_2": 0.05}
        corrections = xtalk.get_non_linear_flux_terms(flux)
        for bus in corrections:
            assert corrections[bus] == pytest.approx(0.0)

    def test_correction_nonzero_when_params_set(self, nonlinear_crosstalk_matrix, flux_dict):
        corrections = nonlinear_crosstalk_matrix.get_non_linear_flux_terms(flux_dict)
        assert corrections["flux_0"] != pytest.approx(0.0)
        assert corrections["flux_1"] != pytest.approx(0.0)
        assert corrections["flux_2"] == pytest.approx(0.0)

    def test_correction_matches_manual_calculation(self, nonlinear_crosstalk_matrix, flux_dict):
        corrections = nonlinear_crosstalk_matrix.get_non_linear_flux_terms(flux_dict)

        expected_flux_0 = nonlinear_crosstalk_matrix.sin_beta_scaled(flux=flux_dict["flux_2"], beta=-0.234, amp=-0.021)
        expected_flux_1 = nonlinear_crosstalk_matrix.sin_beta_scaled(flux=flux_dict["flux_2"], beta=-0.253, amp=-0.021)
        assert corrections["flux_0"] == pytest.approx(float(expected_flux_0), rel=1e-6)
        assert corrections["flux_1"] == pytest.approx(float(expected_flux_1), rel=1e-6)

    def test_raises_on_missing_amplitude(self, linear_crosstalk_matrix):
        xtalk = NonLinearCrosstalkMatrix.from_linear(linear_crosstalk_matrix)
        xtalk.beta_c_matrix["flux_0"]["flux_2"] = -0.234
        # Intentionally leave non_lin_amp_matrix["flux_0"]["flux_2"] as None
        with pytest.raises(ValueError, match="non_lin_amp is None"):
            xtalk.get_non_linear_flux_terms({"flux_0": 0.1, "flux_1": 0.2, "flux_2": 0.05})
            
    def test_raises_on_missing_bus_in_flux(self, nonlinear_crosstalk_matrix):
        with pytest.raises(ValueError, match="Bus 'flux_2' not found"):
            nonlinear_crosstalk_matrix.get_non_linear_flux_terms({"flux_0": 0.1, "flux_1": 0.2})


class TestFluxToBias:
    """Tests for flux_to_bias."""

    def test_flux_to_bias_returns_all_buses(self, nonlinear_crosstalk_matrix, flux_dict):
        bias = nonlinear_crosstalk_matrix.flux_to_bias(flux_dict)
        assert set(bias.keys()) == set(flux_dict.keys())

    def test_flux_to_bias_no_nonlinear_matches_linear_inverse(self, linear_crosstalk_matrix, flux_dict):
        """With no nonlinear params set, flux_to_bias should match the pure linear inversion."""
        xtalk = NonLinearCrosstalkMatrix.from_linear(linear_crosstalk_matrix)
        bias = xtalk.flux_to_bias(flux_dict)

        sorted_buses = sorted(flux_dict.keys())
        flux_arr = np.array([flux_dict[b] for b in sorted_buses])
        offsets = np.array([xtalk.flux_offsets.get(b, 0.0) for b in sorted_buses])
        expected = np.linalg.inv(linear_crosstalk_matrix.to_array()) @ (flux_arr - offsets)

        for i, bus in enumerate(sorted_buses):
            assert bias[bus] == pytest.approx(expected[i], rel=1e-6)

    def test_flux_to_bias_with_nonlinear_differs_from_linear(
        self, nonlinear_crosstalk_matrix, linear_crosstalk_matrix, flux_dict
    ):
        """Nonlinear flux_to_bias should differ from the pure linear result."""
        linear_xtalk = NonLinearCrosstalkMatrix.from_linear(linear_crosstalk_matrix)
        bias_linear = linear_xtalk.flux_to_bias(flux_dict)
        bias_nonlinear = nonlinear_crosstalk_matrix.flux_to_bias(flux_dict)

        assert any(bias_nonlinear[bus] != pytest.approx(bias_linear[bus], rel=1e-6) for bus in flux_dict)

    def test_flux_to_bias_with_offsets(self, nonlinear_crosstalk_matrix, flux_dict):
        nonlinear_crosstalk_matrix.set_offset({"flux_0": 0.05, "flux_1": -0.05, "flux_2": 0.0})
        bias_with_offset = nonlinear_crosstalk_matrix.flux_to_bias(flux_dict)

        nonlinear_crosstalk_matrix.set_offset({"flux_0": 0.0, "flux_1": 0.0, "flux_2": 0.0})
        bias_no_offset = nonlinear_crosstalk_matrix.flux_to_bias(flux_dict)

        assert any(bias_with_offset[bus] != pytest.approx(bias_no_offset[bus], rel=1e-6) for bus in flux_dict)
        
    def test_flux_to_bias_with_array(self, nonlinear_crosstalk_matrix):
        """NonLinearCrosstalkMatrix.flux_to_bias should apply nonlinear corrections
        element-wise when flux values are numpy arrays."""
        flux_dict = {
            "flux_0": np.array([0.1, 0.2, 0.3]),
            "flux_1": np.array([0.2, 0.3, 0.4]),
            "flux_2": np.array([0.05, 0.1, 0.15]),
        }
        bias = nonlinear_crosstalk_matrix.flux_to_bias(flux_dict)

        # each point must match the scalar result
        for i in range(3):
            scalar_flux = {bus: float(flux_dict[bus][i]) for bus in flux_dict}
            scalar_bias = nonlinear_crosstalk_matrix.flux_to_bias(scalar_flux)
            for bus in flux_dict:
                assert float(bias[bus][i]) == pytest.approx(float(scalar_bias[bus]), rel=1e-6)


class TestReprAndInheritedMethods:
    """Tests for __repr__ and inherited CrosstalkMatrix methods."""

    def test_repr(self, nonlinear_crosstalk_matrix):
        r = repr(nonlinear_crosstalk_matrix)
        assert "NonLinearCrosstalkMatrix" in r
        assert "beta_c" in r

    def test_to_array_inherited(self, nonlinear_crosstalk_matrix):
        arr = nonlinear_crosstalk_matrix.to_array()
        assert isinstance(arr, np.ndarray)
        assert arr.shape == (3, 3)

    def test_inverse_inherited(self, nonlinear_crosstalk_matrix):
        inv = nonlinear_crosstalk_matrix.inverse()
        product = nonlinear_crosstalk_matrix.to_array() @ inv.to_array()
        assert np.allclose(product, np.eye(3), atol=1e-10)
