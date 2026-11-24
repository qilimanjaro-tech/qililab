import logging
import re

import numpy as np
import pytest

from qililab import Calibration, Domain, IQPair, QProgram, Square
from qililab.pulse_distortion import ExponentialCorrection
from qililab.qprogram.blocks import Average
from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix
from qililab.qprogram.operations import Acquire, Play, Sync
from qililab.qprogram.prepass import ConditionalTrigger, prepare_qblox, prepare_shared

DRIVE_WF = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
WEIGHTS = IQPair(I=Square(amplitude=1.0, duration=100), Q=Square(amplitude=0.0, duration=100))


HERALD_WAIT_ERROR = (
    "On bus 'readout', qp.qblox.measure_herald() must come right after a qp.wait(bus='readout', duration=50) or "
    "longer, at the end of the loop when the herald comes first in it: a measurement on that bus ending less than 50 ns "
    "before the herald can be read as its first attempt or make the sequencer hang."
)


@pytest.fixture(name="flux_qprogram")
def fixture_flux_qprogram() -> QProgram:
    qp = QProgram()
    qp.set_offset(bus="flux1", offset_path0=0.1)
    with qp.average(2):
        qp.play(bus="flux1", waveform=Square(amplitude=0.5, duration=40))
    return qp


class TestPrepareQblox:
    def test_keeps_only_operations_on_qblox_buses(self):
        qp = QProgram()
        qp.qdac.play(bus="qdac_flux", waveform=Square(amplitude=0.5, duration=10), dwell=2)
        with qp.average(10):
            qp.play(bus="drive", waveform=DRIVE_WF)
            qp.set_offset(bus="qdac_flux", offset_path0=0.2)
            qp.sync()
            qp.qblox.acquire(bus="readout", weights=WEIGHTS)

        result = prepare_qblox(qp, qblox_buses=["drive", "readout"])

        assert result.qblox_buses == ["drive", "readout"]
        assert result.qprogram.buses == {"drive", "readout"}
        (average,) = result.qprogram.body.elements
        assert isinstance(average, Average)
        assert [type(element) for element in average.elements] == [Play, Sync, Acquire]
        assert qp.buses == {"drive", "readout", "qdac_flux"}

    def test_qblox_buses_default_to_every_bus(self):
        qp = QProgram()
        qp.play(bus="drive", waveform=DRIVE_WF)
        qp.wait(bus="flux", duration=100)

        result = prepare_qblox(qp)

        assert sorted(result.qblox_buses) == ["drive", "flux"]
        assert result.qprogram.buses == {"drive", "flux"}
        assert len(result.qprogram.body.elements) == 2

    def test_acquisition_metadata(self):
        """Per Qblox bus and block: the acquisitions directly in the block and the block's depth."""
        qp = QProgram()
        with qp.average(10) as average:
            qp.qblox.acquire(bus="readout", weights=WEIGHTS)
            qp.measure(bus="readout", waveform=WEIGHTS, weights=WEIGHTS)
            qp.qblox.acquire(bus="qdac_flux", weights=WEIGHTS)
        qp.qblox.acquire(bus="readout", weights=WEIGHTS)

        result = prepare_qblox(qp, qblox_buses=["readout"])

        assert result.acquisition_metadata == {"readout": {average.uuid: (2, 1), qp.body.uuid: (1, 0)}}

    @pytest.mark.parametrize(
        "wait_trigger_bus, qblox_buses, expected",
        [(None, ["drive"], False), ("drive", ["drive"], True), ("qdac_flux", ["drive"], False)],
    )
    def test_requires_external_trigger_with_wait_trigger(self, wait_trigger_bus, qblox_buses, expected):
        qp = QProgram()
        qp.play(bus="drive", waveform=DRIVE_WF)
        if wait_trigger_bus is not None:
            qp.wait_trigger(bus=wait_trigger_bus, duration=100)

        assert prepare_qblox(qp, qblox_buses=qblox_buses).requires_external_trigger is expected

    def test_if_trigger_wait_time_derived_from_qdac_dwell(self):
        qp = QProgram()
        qp.qdac.play(bus="qdac_flux", waveform=Square(amplitude=1.0, duration=100), dwell=3)
        qp.set_trigger(bus="qdac_flux", duration=100e-6, outputs=1, position="step")
        with qp.if_trigger():
            with qp.average(shots=10):
                qp.qblox.acquire(bus="readout", weights=WEIGHTS)

        result = prepare_qblox(qp, qblox_buses=["readout"])

        assert result.conditional == ConditionalTrigger(bus="readout", expected_wait_time_ns=3000, trigger_padding_ns=252)
        assert result.requires_external_trigger is True

    def test_if_trigger_explicit_wait_time_and_padding(self):
        qp = QProgram()
        with qp.if_trigger(trigger_padding_ns=300, expected_wait_time_ns=2252):
            with qp.average(shots=10):
                qp.qblox.acquire(bus="readout", weights=WEIGHTS)

        result = prepare_qblox(qp, qblox_buses=["readout"])

        assert result.conditional == ConditionalTrigger(bus="readout", expected_wait_time_ns=2252, trigger_padding_ns=300)

    def test_if_trigger_nested_block_raises_error(self):
        qp = QProgram()
        with qp.if_trigger(expected_wait_time_ns=2252):
            with qp.block():
                qp.qblox.acquire(bus="readout", weights=WEIGHTS)

        with pytest.raises(
            NotImplementedError,
            match=re.escape(
                "Block block cannot be nested inside qp.if_trigger() (only qp.average(...)/qp.for_loop(...) can be)."
            ),
        ):
            prepare_qblox(qp, qblox_buses=["readout"])

    def test_if_trigger_instruction_outside_block_raises_error(self):
        qp = QProgram()
        with qp.if_trigger(expected_wait_time_ns=2252):
            with qp.average(shots=10):
                qp.qblox.acquire(bus="readout", weights=WEIGHTS)
        qp.sync()

        with pytest.raises(
            NotImplementedError,
            match=re.escape(
                "Bus 'readout' cannot have instructions outside its qp.if_trigger() block: found Sync outside the "
                "conditional, which would break the synchronisation."
            ),
        ):
            prepare_qblox(qp, qblox_buses=["readout"])

    def test_no_if_trigger(self):
        qp = QProgram()
        qp.play(bus="drive", waveform=DRIVE_WF)

        assert prepare_qblox(qp).conditional is None

    def test_measure_reset_trigger_requirements(self):
        """The latch is enabled on the control bus, and the trigger network on the measurement bus, after mapping."""
        qp = QProgram()
        with qp.average(10):
            qp.qblox.measure_reset(
                bus="readout", waveform=WEIGHTS, weights=WEIGHTS, control_bus="drive", reset_pulse=DRIVE_WF, trigger_address=3
            )
            qp.qblox.measure_reset(
                bus="readout", waveform=WEIGHTS, weights=WEIGHTS, control_bus="drive", reset_pulse=DRIVE_WF, trigger_address=3
            )
        qp = prepare_shared(qp, bus_mapping={"readout": "readout_q0", "drive": "drive_q0"})

        result = prepare_qblox(qp, qblox_buses=["readout_q0", "drive_q0"])

        assert result.latch_buses == ["drive_q0"]
        assert result.trigger_network_addresses == {"readout_q0": 3}
        assert result.requires_external_trigger is False

    @pytest.mark.parametrize("qblox_buses", [["drive"], ["readout"]])
    def test_measure_reset_outside_qblox_buses_raises_error(self, qblox_buses):
        qp = QProgram()
        qp.qblox.measure_reset(bus="readout", waveform=WEIGHTS, weights=WEIGHTS, control_bus="drive", reset_pulse=DRIVE_WF)

        with pytest.raises(
            ValueError,
            match=re.escape(
                "qp.qblox.measure_reset() measures on bus 'readout' and resets on bus 'drive', but both must be Qblox "
                f"buses; the Qblox buses are {qblox_buses}."
            ),
        ):
            prepare_qblox(qp, qblox_buses=qblox_buses)

    def test_measure_herald_trigger_requirements(self):
        """The herald uses LINQ feedback: its bus needs neither the trigger latch nor the trigger network.

        The herald has its own acquisition: it isn't counted in the acquisition metadata.
        """
        qp = QProgram()
        with qp.average(10) as average:
            qp.qblox.measure_herald(bus="readout", waveform=WEIGHTS, weights=WEIGHTS)
            qp.measure(bus="readout", waveform=WEIGHTS, weights=WEIGHTS)
            qp.wait(bus="readout", duration=50)
        qp = prepare_shared(qp, bus_mapping={"readout": "readout_q0"})

        result = prepare_qblox(qp, qblox_buses=["readout_q0"])

        assert result.latch_buses == []
        assert result.trigger_network_addresses == {}
        assert result.acquisition_metadata == {"readout_q0": {average.uuid: (1, 1)}}
        assert result.requires_external_trigger is False

    def test_two_measure_heralds_raise_error(self):
        qp = QProgram()
        with qp.average(10):
            qp.qblox.measure_herald(bus="readout_q0", waveform=WEIGHTS, weights=WEIGHTS)
        with qp.average(10):
            qp.qblox.measure_herald(bus="readout_q1", waveform=WEIGHTS, weights=WEIGHTS)

        with pytest.raises(
            NotImplementedError, match=re.escape("Only one qp.qblox.measure_herald() is supported per QProgram.")
        ):
            prepare_qblox(qp)

    def test_measure_herald_outside_qblox_buses_raises_error(self):
        qp = QProgram()
        qp.qblox.measure_herald(bus="readout", waveform=WEIGHTS, weights=WEIGHTS)
        qp.play(bus="drive", waveform=DRIVE_WF)

        with pytest.raises(
            ValueError,
            match=re.escape(
                "qp.qblox.measure_herald() measures on bus 'readout', but it must be a Qblox bus; the Qblox buses are "
                "['drive']."
            ),
        ):
            prepare_qblox(qp, qblox_buses=["drive"])

    def test_measure_herald_after_measurement_ending_previous_shot_raises_error(self):
        """The shot's last operation on the herald's bus is a measurement: the drive and the sync don't count."""
        qp = QProgram()
        with qp.average(10):
            qp.qblox.measure_herald(bus="readout", waveform=WEIGHTS, weights=WEIGHTS)
            qp.play(bus="drive", waveform=DRIVE_WF)
            qp.sync()
            qp.measure(bus="readout", waveform=WEIGHTS, weights=WEIGHTS)

        with pytest.raises(ValueError, match=re.escape(HERALD_WAIT_ERROR)):
            prepare_qblox(qp)

    def test_measure_herald_right_after_measurement_raises_error(self):
        qp = QProgram()
        with qp.average(10):
            qp.measure(bus="readout", waveform=WEIGHTS, weights=WEIGHTS)
            qp.qblox.measure_herald(bus="readout", waveform=WEIGHTS, weights=WEIGHTS)
            qp.wait(bus="readout", duration=1000)

        with pytest.raises(ValueError, match=re.escape(HERALD_WAIT_ERROR)):
            prepare_qblox(qp)

    def test_measure_herald_after_loop_raises_error(self):
        """A nested block on the herald's bus counts as what runs just before it, even if it ends with a wait."""
        qp = QProgram()
        with qp.average(10):
            qp.qblox.measure_herald(bus="readout", waveform=WEIGHTS, weights=WEIGHTS)
            with qp.average(2):
                qp.measure(bus="readout", waveform=WEIGHTS, weights=WEIGHTS)
                qp.wait(bus="readout", duration=50)

        with pytest.raises(ValueError, match=re.escape(HERALD_WAIT_ERROR)):
            prepare_qblox(qp)

    def test_measure_herald_after_too_short_wait_raises_error(self):
        qp = QProgram()
        with qp.average(10):
            qp.qblox.measure_herald(bus="readout", waveform=WEIGHTS, weights=WEIGHTS)
            qp.measure(bus="readout", waveform=WEIGHTS, weights=WEIGHTS)
            qp.wait(bus="readout", duration=20)

        with pytest.raises(ValueError, match=re.escape(HERALD_WAIT_ERROR)):
            prepare_qblox(qp)

    def test_measure_herald_after_variable_wait_raises_error(self):
        """A variable wait's duration isn't known at compile time."""
        qp = QProgram()
        duration = qp.variable(label="duration", domain=Domain.Time)
        with qp.average(10):
            with qp.for_loop(variable=duration, start=100, stop=200, step=100):
                qp.qblox.measure_herald(bus="readout", waveform=WEIGHTS, weights=WEIGHTS)
                qp.measure(bus="readout", waveform=WEIGHTS, weights=WEIGHTS)
                qp.wait(bus="readout", duration=duration)

        with pytest.raises(ValueError, match=re.escape(HERALD_WAIT_ERROR)):
            prepare_qblox(qp)

    def test_measure_herald_after_wait_of_50_ns(self):
        """Operations on another bus after the wait don't count: only the herald's bus gets its results back."""
        qp = QProgram()
        frequency = qp.variable(label="frequency", domain=Domain.Frequency)
        with qp.average(10):
            with qp.for_loop(variable=frequency, start=1e6, stop=2e6, step=1e6):
                qp.qblox.measure_herald(bus="readout", waveform=WEIGHTS, weights=WEIGHTS)
                qp.measure(bus="readout", waveform=WEIGHTS, weights=WEIGHTS)
                qp.wait(bus="readout", duration=50)
                qp.measure(bus="readout2", waveform=WEIGHTS, weights=WEIGHTS)

        prepare_qblox(qp)

    def test_measure_herald_alone_on_its_bus(self):
        """Alone on its bus in the loop, the herald follows itself, whose last attempt waits for its own result."""
        qp = QProgram()
        with qp.average(10):
            qp.play(bus="drive", waveform=DRIVE_WF)
            qp.qblox.measure_herald(bus="readout", waveform=WEIGHTS, weights=WEIGHTS)

        prepare_qblox(qp)

    def test_measure_herald_padding_after_measure_below_linq_latency_raises_error(self):
        qp = QProgram()
        qp.qblox.measure_herald(bus="readout", waveform=WEIGHTS, weights=WEIGHTS, padding_after_measure=199)

        with pytest.raises(
            ValueError,
            match=re.escape(
                "qp.qblox.measure_herald()'s padding_after_measure (199) cannot be lower than 200 ns, the time LINQ "
                "feedback takes to bring the result back."
            ),
        ):
            prepare_qblox(qp)

    def test_crosstalk_uses_calibration_ac_matrix_over_explicit_one(self, flux_qprogram: QProgram):
        ac_crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], np.linalg.inv([[1, 0.3], [0.3, 1]]))
        explicit_crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], np.linalg.inv([[1, 0.5], [0.5, 1]]))
        calibration = Calibration()
        calibration.crosstalk_matrix = explicit_crosstalk
        calibration.crosstalk_matrix_ac = ac_crosstalk

        result = prepare_qblox(flux_qprogram, calibration=calibration, crosstalk=explicit_crosstalk)

        assert str(result.qprogram) == str(flux_qprogram.with_crosstalk_qblox(crosstalk=ac_crosstalk))
        assert str(result.qprogram) != str(flux_qprogram.with_crosstalk_qblox(crosstalk=explicit_crosstalk))

    def test_crosstalk_explicit_matrix_over_calibration_dc_matrix(self, flux_qprogram: QProgram):
        dc_crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], np.linalg.inv([[1, 0.3], [0.3, 1]]))
        explicit_crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], np.linalg.inv([[1, 0.5], [0.5, 1]]))
        calibration = Calibration()
        calibration.crosstalk_matrix = dc_crosstalk

        result = prepare_qblox(flux_qprogram, calibration=calibration, crosstalk=explicit_crosstalk)

        assert str(result.qprogram) == str(flux_qprogram.with_crosstalk_qblox(crosstalk=explicit_crosstalk))

    def test_crosstalk_falls_back_to_calibration_dc_matrix_with_warning(self, caplog, flux_qprogram: QProgram):
        dc_crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], np.linalg.inv([[1, 0.3], [0.3, 1]]))
        calibration = Calibration()
        calibration.crosstalk_matrix = dc_crosstalk

        with caplog.at_level(logging.WARNING):
            result = prepare_qblox(flux_qprogram, calibration=calibration)

        assert "Define `crosstalk_matrix_ac`" in caplog.text
        assert str(result.qprogram) == str(flux_qprogram.with_crosstalk_qblox(crosstalk=dc_crosstalk))

    def test_distortions_are_applied(self, flux_qprogram: QProgram):
        distortions = {"flux1": [ExponentialCorrection(tau_exponential=100.0, amp=0.5)]}

        result = prepare_qblox(flux_qprogram, bus_distortions=distortions)

        assert str(result.qprogram) == str(flux_qprogram.with_distortions(bus_distortions=distortions))
        assert str(result.qprogram) != str(flux_qprogram)
