"""Unit tests for the ``SSRO`` class."""
from copy import deepcopy
from unittest.mock import MagicMock, patch

import lmfit
import matplotlib.pyplot as plt
import numpy as np
import pytest
from qibo.gates import M
from scipy.special import erf

from qililab import build_platform
from qililab.experiment import SSRO
from qililab.transpiler.native_gates import Drag
from qililab.typings.enums import Parameter
from qililab.utils import Wait
from tests.data import Galadriel

START, STOP, NUM = (1, 2000, 4000)
I_AMPLITUDE, I_FREQ, I_PHASE, I_OFFSET = (5, 7 / (2 * np.pi), -np.pi / 2, 0)
Q_AMPLITUDE, Q_FREQ, Q_PHASE, Q_OFFSET = (9, 7 / (2 * np.pi), -np.pi / 2, 0)

x = np.linspace(START, STOP, NUM)
i = I_AMPLITUDE * np.cos(2 * np.pi * I_FREQ * x + I_PHASE)
q = Q_AMPLITUDE * np.cos(2 * np.pi * Q_FREQ * x + Q_PHASE)


@pytest.fixture(
    name="ssro",
    params=[Parameter.DURATION, Parameter.AMPLITUDE, Parameter.IF, Parameter.LO_FREQUENCY, Parameter.ATTENUATION, None],
)
def fixture_ssro(request: pytest.FixtureRequest):
    """Return Experiment object."""
    with patch("qililab.platform.platform_manager_yaml.yaml.safe_load", return_value=Galadriel.runcard) as mock_load:
        with patch("qililab.platform.platform_manager_yaml.open") as mock_open:
            platform = build_platform(name="_")
            mock_load.assert_called()
            mock_open.assert_called()
    analysis = SSRO(
        platform=platform,
        qubit=0,
        loop_values=np.linspace(start=START, stop=STOP, num=NUM),
        loop_parameter=request.param,
    )
    analysis.results = MagicMock()
    analysis.results.acquisitions.return_value = {
        "i": i,
        "q": q,
    }
    return analysis


class TestSSRO:
    """Unit tests for the ``SSRO`` portfolio experiment class."""

    def test_init(self, ssro: SSRO):
        """Test the ``__init__`` method."""
        # Test that the correct circuits are created
        assert len(ssro.circuits) == 2
        for circuit in ssro.circuits:
            for idx, gate in enumerate(circuit.queue):
                assert isinstance(gate, [Drag, Wait, M][idx])
                assert gate.qubits == (0,)
        # Test atributes
        assert hasattr(ssro, "qubit")
        assert hasattr(ssro, "loop_parameter")
        assert hasattr(ssro, "loop_values")

        # Test the experiment options
        if ssro.loop_parameter == Parameter.DURATION:
            assert len(ssro.options.loops) == 2
        else:
            assert len(ssro.options.loops) == 1

        # Check loops depending on the parameter
        if ssro.loop_parameter is None:
            assert ssro.loop.alias == "external"
            assert ssro.loop.parameter == Parameter.EXTERNAL
            assert ssro.loop.values == np.array([1])
            # Loop values
            assert ssro.loop.start == 1
            assert ssro.loop.stop == 1
            assert ssro.loop.num == 1
        else:
            if ssro.loop_parameter == Parameter.DURATION:
                # Test both loops are well created
                assert ssro.loop.alias == f"M({ssro.qubit})"
                assert ssro.options.loops[1].alias == "feedline_bus"

                assert ssro.loop.parameter == Parameter.DURATION
                assert ssro.options.loops[1].parameter == Parameter.INTEGRATION_LENGTH

                assert ssro.options.loops[1].channel_id == ssro.qubit

                assert ssro.options.loops[1].start == START
                assert ssro.options.loops[1].stop == STOP
                assert ssro.options.loops[1].num == NUM

            elif ssro.loop_parameter == Parameter.AMPLITUDE:
                assert ssro.loop.alias == f"M({ssro.qubit})"
                assert ssro.loop.parameter == ssro.loop_parameter

            elif ssro.loop_parameter == Parameter.IF:
                assert ssro.loop.alias == "feedline_bus"
                assert ssro.loop.parameter == ssro.loop_parameter
                assert ssro.loop.channel_id == ssro.qubit

            elif ssro.loop_parameter == Parameter.LO_FREQUENCY:
                assert ssro.loop.alias == "rs_1"
                assert ssro.loop.parameter == ssro.loop_parameter
                assert ssro.loop.channel_id is None

            elif ssro.loop_parameter == Parameter.ATTENUATION:
                assert ssro.loop.alias == "attenuator"
                assert ssro.loop.parameter == ssro.loop_parameter
            # Loop values
            assert ssro.loop.start == START
            assert ssro.loop.stop == STOP
            assert ssro.loop.num == NUM

    def test_func(self, ssro: SSRO):
        """Test the ``func`` method."""
        assert np.allclose(
            ssro.func(xdata=x, amplitude=I_AMPLITUDE, frequency=I_FREQ, phase=I_PHASE, offset=I_OFFSET),
            i,
        )

    def test_post_process_results(self, ssro: SSRO):
        """"""
        expected_iq = np.array(i + 1j * q)
        expected_iq = expected_iq.reshape(2, ssro.num_bins)
        assert not hasattr(ssro, "post_proccessed_results")

        shots_iq = ssro.post_process_results()

        assert hasattr(ssro, "post_proccessed_results")
        assert np.allclose(expected_iq, shots_iq)

    def test_fit(self, ssro: SSRO):
        """Test the ``fit`` method"""

        def two_gaussians(x, a0, std0, v0, std1, v1):
            a1 = 1 - a0
            cdf_0 = a0 * (1 + erf((x - v0) / (std0 * 2**0.5))) / 2
            cdf_1 = a1 * (1 + erf((x - v1) / (std1 * 2**0.5))) / 2
            return cdf_0 + cdf_1

        def joint_model(x, mmt_relax, thermal_pop, std0, v0, std1, v1, N):
            prep0_m0 = 1 - thermal_pop
            prep1_m0 = mmt_relax
            cdf_prep0 = N * two_gaussians(x, prep0_m0, std0, v0, std1, v1)
            cdf_prep1 = N * two_gaussians(x, prep1_m0, std0, v0, std1, v1)
            return np.concatenate((cdf_prep0, cdf_prep1))

        ssro.post_process_results()

        I_0, Q_0 = np.real(ssro.post_proccessed_results[0]), np.imag(ssro.post_proccessed_results[0])
        I_1, Q_1 = np.real(ssro.post_proccessed_results[1]), np.imag(ssro.post_proccessed_results[1])
        center_0_i, center_0_q = np.mean(I_0), np.mean(Q_0)
        center_1_i, center_1_q = np.mean(I_1), np.mean(Q_1)

        dist_i = center_1_i - center_0_i
        dist_q = center_1_q - center_0_q

        # x,y are I,Q centered in 0
        x_0 = I_0 - center_0_i
        y_0 = Q_0 - center_0_q
        x_1 = I_1 - center_0_i
        y_1 = Q_1 - center_0_q
        # u,v are x,v rotated
        theta = np.arctan2(dist_q, dist_i)
        expected_u_0 = x_0 * np.cos(theta) + y_0 * np.sin(theta)
        expected_u_1 = x_1 * np.cos(theta) + y_1 * np.sin(theta)

        perc_vec = np.linspace(0, 100, 101)
        expected_cdf_0 = np.percentile(expected_u_0, perc_vec)
        expected_cdf_1 = np.percentile(expected_u_1, perc_vec)

        expected_x_axis = np.linspace(
            np.min((expected_cdf_0, expected_cdf_1)), np.max((expected_cdf_0, expected_cdf_1)), 101
        )
        interp_cdf_0 = np.interp(expected_x_axis, expected_cdf_0, perc_vec)
        interp_cdf_1 = np.interp(expected_x_axis, expected_cdf_1, perc_vec)
        diff_cdf = interp_cdf_1 - interp_cdf_0

        idx_max = np.argmax(np.abs(diff_cdf))
        expected_threshold = expected_x_axis[idx_max]
        # Threshold in the u axis, but without the shifts
        expected_threshold_d = expected_threshold + center_0_i * np.cos(theta) + center_0_q * np.sin(theta)

        f_asg = np.abs(diff_cdf[idx_max])
        expected_f_avg = (100 + f_asg) / 2

        cdfs_mod = lmfit.Model(joint_model)

        v0_guess = np.mean(expected_u_0)
        std0_guess = np.std(expected_u_0)
        v1_guess = np.mean(expected_u_1)
        std1_guess = np.std(expected_u_1)

        cdfs_mod.set_param_hint("mmt_relax", value=0.7, min=0, max=1, vary=True)
        cdfs_mod.set_param_hint("thermal_pop", value=0.03, min=0, max=1, vary=True)
        cdfs_mod.set_param_hint("std0", value=std0_guess, vary=True)
        cdfs_mod.set_param_hint("std1", value=std1_guess, vary=True)
        cdfs_mod.set_param_hint("v0", value=v0_guess, vary=True)
        cdfs_mod.set_param_hint("v1", value=v1_guess, vary=True)
        cdfs_mod.set_param_hint("N", value=100, min=0, vary=False)
        params = cdfs_mod.make_params()
        fit_res = cdfs_mod.fit(data=np.concatenate((interp_cdf_1, interp_cdf_0)), x=expected_x_axis, params=params)

        expected_y_axis = joint_model(expected_x_axis, **fit_res.best_values)
        ideal_dict = deepcopy(fit_res.best_values)
        ideal_dict["mmt_relax"] = 0
        ideal_dict["thermal_pop"] = 0

        y_ideal = joint_model(expected_x_axis, **ideal_dict)
        f_asg_ideal = np.max(np.abs(y_ideal[: len(y_ideal) // 2] - y_ideal[len(y_ideal) // 2 :]))
        expected_f_avg_ideal = (100 + f_asg_ideal) / 2

        fitted_data = ssro.fit()

        # Check metadata is saved
        assert fitted_data["f_avg_discr"] == expected_f_avg_ideal
        assert fitted_data["f_avg"] == expected_f_avg
        assert np.allclose(fitted_data["x_axis"], expected_x_axis)
        assert np.allclose(fitted_data["y_axis"], expected_y_axis)
        assert np.allclose(fitted_data["us"], [expected_u_0, expected_u_1])
        assert np.allclose(fitted_data["cdfs"], [expected_cdf_0, expected_cdf_1])
        assert np.allclose(fitted_data["thresholds"], [expected_threshold, expected_threshold_d])
        assert fitted_data["fitted_values"] == fit_res.best_values

    def test_fit_raises(self, ssro: SSRO):
        """Test the ``fit`` method raises an exception when calling the fit before having post processed the data"""
        with pytest.raises(
            ValueError,
            match="The post-processed results must be computed before fitting.\nPlease call ``post_process_results`` first.",
        ):
            ssro.fit()

    @pytest.mark.xfail(reason="Can't retrieve X and Y properly from `hist2d` plot")
    def test_plot(self, ssro: SSRO):
        """Test the ``plot`` method returns a correct format of the figure"""
        ssro.post_process_results()
        ssro.fit()
        I_0, Q_0 = np.real(ssro.post_proccessed_results[0]), np.imag(ssro.post_proccessed_results[0])
        I_1, Q_1 = np.real(ssro.post_proccessed_results[1]), np.imag(ssro.post_proccessed_results[1])
        plt.clf()
        fig = ssro.plot()

        assert len(fig.axes) == 3
        assert hasattr(fig.axes[0], "hist")
        assert hasattr(fig.axes[1], "plot") or hasattr(fig.axes[0], "axvline")
        assert hasattr(fig.axes[2], "hist2d")

        # Get the lines for the first subplot
        for idx, line in enumerate(fig.axes[0].lines):
            assert ssro.fitted_data["us"][idx] == line.get_xdata()

        # Get the lines for the second subplot
        # Loop over plots
        for idx, line in enumerate(fig.axes[1].lines[:-1]):
            # The even plots have the same structure
            if idx % 2 == 0:
                cdf_idx = 0 if idx == 0 else 1
                assert np.allclose(ssro.fitted_data["cdfs"][cdf_idx], line.get_xdata())
                assert np.allclose(np.linspace(0, 100, 101), line.get_ydata())
            # The odd plots have the same structure
            else:
                start, stop = (
                    (len(ssro.fitted_data["y_axis"]) // 2, len(ssro.fitted_data["y_axis"]))
                    if idx == 1
                    else (0, len(ssro.fitted_data["y_axis"]) // 2)
                )
                assert np.allclose(ssro.fitted_data["x_axis"], line.get_xdata())
                assert np.allclose(ssro.fitted_data["y_axis"][start:stop], line.get_ydata())
        # Test plot vertical line
        line = fig.axes[1].lines[-1]
        assert np.allclose(ssro.fitted_data["thresholds"][0], line.get_xdata())

        # Get the lines for the third subplot

        expected_x, expected_y = np.concatenate((I_0, I_1)), np.concatenate((Q_0, Q_1))
        assert np.allclose(expected_x, fig.axes[2].xedges)
        assert np.allclose(expected_y, fig.axes[2].yedges)

    def test_plot_raises(self, ssro: SSRO):
        """Test the ``plot`` method raises an exception when calling the plot before having fitted the data"""
        with pytest.raises(
            ValueError, match="The fitted data results must be computed before plotting.\nPlease call ``fit`` first."
        ):
            ssro.plot()
