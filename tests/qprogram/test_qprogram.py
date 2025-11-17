import os
from itertools import product

import numpy as np
import pytest

from qililab import Domain, DragCorrection, Gaussian, IQPair, QProgram, Square
from qililab.qprogram.blocks import Average
from qililab.qprogram.calibration import Calibration
from qililab.qprogram.operations import (
    Acquire,
    AcquireWithCalibratedWeights,
    Measure,
    MeasureReset,
    MeasureWithCalibratedWaveform,
    MeasureWithCalibratedWaveformWeights,
    MeasureWithCalibratedWeights,
    Play,
    PlayWithCalibratedWaveform,
    ResetPhase,
    SetFrequency,
    SetGain,
    SetMarkers,
    SetOffset,
    SetPhase,
    Sync,
    Wait,
)
from qililab.utils.serialization import deserialize, deserialize_from, serialize, serialize_to
from tests.qprogram.test_structured_program import (
    TestStructuredProgram,
)


@pytest.fixture(name="sample_qprogram_string")
def get_sample_qprogram_string():
    """Sample qprogram and its corresponding string to tests the __str__ method"""
    r_amp = 0.5
    r_duration = 40
    d_duration = 40

    r_wf_I = Square(amplitude=r_amp, duration=r_duration)
    r_wf_Q = Square(amplitude=0.0, duration=r_duration)
    d_wf = IQPair.DRAG(amplitude=1.0, duration=d_duration, num_sigmas=4, drag_coefficient=0.1)

    weights_shape = Square(amplitude=1, duration=r_duration)

    qp = QProgram()
    amp = qp.variable(label="amplitude", domain=Domain.Voltage)
    freq = qp.variable(label="frequency", domain=Domain.Frequency)

    with qp.average(100):
        with qp.for_loop(variable=amp, start=0.2, stop=1, step=0.1):
            qp.set_gain(bus="dummy_bus_0", gain=amp)
            with qp.for_loop(variable=freq, start=0, stop=20, step=5):
                qp.set_frequency(bus="dummy_bus_1", frequency=freq)
                # DRAG PULSE
                qp.play(bus="dummy_bus_0", waveform=d_wf)
                qp.sync()
                # READOUT PULSE
                qp.measure(
                    bus="readout", waveform=IQPair(I=r_wf_I, Q=r_wf_Q), weights=IQPair(I=weights_shape, Q=weights_shape)
                )
                qp.wait(bus="readout", duration=200)

    qp_string = """Average:\n\tshots: 100\n\tForLoop:\n\t\tstart: 0.2\n\t\tstop: 1\n\t\tstep: 0.1\n\t\tSetGain:\n\t\t\tbus: dummy_bus_0\n\t\t\tgain: None\n\t\tForLoop:\n\t\t\tstart: 0\n\t\t\tstop: 20\n\t\t\tstep: 5\n\t\t\tSetFrequency:\n\t\t\t\tbus: dummy_bus_1\n\t\t\t\tfrequency: None\n\t\t\tPlay:\n\t\t\t\tbus: dummy_bus_0\n\t\t\t\twait_time: None\n\t\t\t\tWaveform I Gaussian:\n\t\t\t\t\t[0.         0.03369997 0.07235569 0.11612685 0.1650374  0.21894866\n\t\t\t\t\t 0.27753626 0.34027302 0.40641993 0.47502707 0.54494577 0.61485281\n\t\t\t\t\t 0.68328653 0.74869396 0.80948709 0.86410559 0.9110827  0.94911031\n\t\t\t\t\t 0.97709942 0.99423184 1.         0.99423184 0.97709942 0.94911031\n\t\t\t\t\t 0.9110827  0.86410559 0.80948709 0.74869396 0.68328653 0.61485281\n\t\t\t\t\t 0.54494577 0.47502707 0.40641993 0.34027302 0.27753626 0.21894866\n\t\t\t\t\t 0.1650374  0.11612685 0.07235569 0.03369997]\n\t\t\t\tWaveform Q DragCorrection):\n\t\t\t\t\t[ 0.          0.0006403   0.0013024   0.00197416  0.0026406   0.00328423\n\t\t\t\t\t  0.00388551  0.00442355  0.00487704  0.0052253   0.00544946  0.00553368\n\t\t\t\t\t  0.00546629  0.00524086  0.00485692  0.00432053  0.00364433  0.00284733\n\t\t\t\t\t  0.0019542   0.00099423 -0.         -0.00099423 -0.0019542  -0.00284733\n\t\t\t\t\t -0.00364433 -0.00432053 -0.00485692 -0.00524086 -0.00546629 -0.00553368\n\t\t\t\t\t -0.00544946 -0.0052253  -0.00487704 -0.00442355 -0.00388551 -0.00328423\n\t\t\t\t\t -0.0026406  -0.00197416 -0.0013024  -0.0006403 ]\n\t\t\tSync:\n\t\t\t\tbuses: None\n\t\t\tMeasure:\n\t\t\t\tbus: readout\n\t\t\t\tsave_adc: False\n\t\t\t\trotation: None\n\t\t\t\tdemodulation: True\n\t\t\t\tWaveform I Square:\n\t\t\t\t\t[0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5\n\t\t\t\t\t 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5\n\t\t\t\t\t 0.5 0.5 0.5 0.5]\n\t\t\t\tWaveform Q Square):\n\t\t\t\t\t[0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.\n\t\t\t\t\t 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0. 0.]\n\t\t\t\tWeights I Square:\n\t\t\t\t\t[1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1.\n\t\t\t\t\t 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1.]\n\t\t\t\tWeights Q Square:\n\t\t\t\t\t[1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1.\n\t\t\t\t\t 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1. 1.]\n\t\t\tWait:\n\t\t\t\tbus: readout\n\t\t\t\tduration: 200\n"""
    return (qp, qp_string)


class TestQProgram(TestStructuredProgram):
    """Unit tests checking the QProgram attributes and methods"""

    @pytest.fixture
    def instance(self):
        return QProgram()

    def test_with_bus_mapping_method(self):
        """Test with_bus_mapping method"""
        qp = QProgram()
        with qp.average(1000):
            qp.wait(bus="drive_bus", duration=100)
            qp.sync(buses=["drive_bus", "readout_bus"])
            qp.play(bus="drive_bus", waveform=Square(1.0, 100))

        new_qp = qp.with_bus_mapping(bus_mapping={"drive_bus": "drive_q0_bus", "readout_bus": "readout_q0_bus"})

        assert len(new_qp.buses) == 2
        assert "drive_bus" not in new_qp.buses
        assert "readout_bus" not in new_qp.buses
        assert "drive_q0_bus" in new_qp.buses
        assert "readout_q0_bus" in new_qp.buses

        assert new_qp.body.elements[0].elements[0].bus == "drive_q0_bus"
        assert new_qp.body.elements[0].elements[1].buses[0] == "drive_q0_bus"
        assert new_qp.body.elements[0].elements[1].buses[1] == "readout_q0_bus"
        assert new_qp.body.elements[0].elements[2].bus == "drive_q0_bus"

        self_mapping_qp = qp.with_bus_mapping(bus_mapping={"drive_bus": "drive_bus", "readout_bus": "readout_bus"})

        assert len(self_mapping_qp.buses) == 2
        assert "drive_bus" in self_mapping_qp.buses
        assert "readout_bus" in self_mapping_qp.buses

        assert self_mapping_qp.body.elements[0].elements[0].bus == "drive_bus"
        assert self_mapping_qp.body.elements[0].elements[1].buses[0] == "drive_bus"
        assert self_mapping_qp.body.elements[0].elements[1].buses[1] == "readout_bus"
        assert self_mapping_qp.body.elements[0].elements[2].bus == "drive_bus"

        non_existant_mapping_qp = qp.with_bus_mapping(
            bus_mapping={"non_existant": "drive_bus", "non_existant_readout": "readout_bus"}
        )

        assert len(non_existant_mapping_qp.buses) == 2
        assert "drive_bus" in non_existant_mapping_qp.buses
        assert "readout_bus" in non_existant_mapping_qp.buses

        assert non_existant_mapping_qp.body.elements[0].elements[0].bus == "drive_bus"
        assert non_existant_mapping_qp.body.elements[0].elements[1].buses[0] == "drive_bus"
        assert non_existant_mapping_qp.body.elements[0].elements[1].buses[1] == "readout_bus"
        assert non_existant_mapping_qp.body.elements[0].elements[2].bus == "drive_bus"

    def test_with_calibration_method(self):
        """Test with_bus_mapping method"""
        xgate = IQPair.DRAG(amplitude=1.0, duration=40, num_sigmas=4.5, drag_coefficient=-4.5)
        readout = IQPair(I=Square(1.0, 200), Q=Square(1.0, 200))
        weights = IQPair(I=Square(1.0, 2000), Q=Square(1.0, 2000))

        calibration = Calibration()
        calibration.add_waveform(bus="drive_q0_bus", name="xgate", waveform=xgate)
        calibration.add_waveform(bus="readout_q0_bus", name="readout", waveform=readout)
        calibration.add_weights(bus="readout_q0_bus", name="weights", weights=weights)

        qp = QProgram()
        with qp.average(1000):
            qp.play(bus="drive_q0_bus", waveform="xgate")
            qp.qblox.play(bus="drive_q0_bus", waveform="xgate", wait_time=100)
            qp.qblox.acquire(bus="readout_q0_bus", weights="weights")
            qp.measure(bus="readout_q0_bus", waveform="readout", weights=weights)
            qp.measure(bus="readout_q0_bus", waveform=readout, weights="weights")
            qp.measure(bus="readout_q0_bus", waveform="readout", weights="weights")
            qp.quantum_machines.measure(bus="readout_q0_bus", waveform="readout", weights=weights, rotation=np.pi)
            qp.quantum_machines.measure(bus="readout_q0_bus", waveform=readout, weights="weights", rotation=np.pi)
            qp.quantum_machines.measure(bus="readout_q0_bus", waveform="readout", weights="weights", rotation=np.pi)

        # Check that qp has named operations
        assert qp.has_calibrated_waveforms_or_weights() is True
        assert isinstance(qp.body.elements[0].elements[0], PlayWithCalibratedWaveform)
        assert qp.body.elements[0].elements[0].waveform == "xgate"
        assert isinstance(qp.body.elements[0].elements[1], PlayWithCalibratedWaveform)
        assert qp.body.elements[0].elements[1].waveform == "xgate"
        assert isinstance(qp.body.elements[0].elements[2], AcquireWithCalibratedWeights)
        assert qp.body.elements[0].elements[2].weights == "weights"
        assert isinstance(qp.body.elements[0].elements[3], MeasureWithCalibratedWaveform)
        assert qp.body.elements[0].elements[3].waveform == "readout"
        assert isinstance(qp.body.elements[0].elements[4], MeasureWithCalibratedWeights)
        assert qp.body.elements[0].elements[4].weights == "weights"
        assert isinstance(qp.body.elements[0].elements[5], MeasureWithCalibratedWaveformWeights)
        assert qp.body.elements[0].elements[5].waveform == "readout"
        assert qp.body.elements[0].elements[5].weights == "weights"
        assert isinstance(qp.body.elements[0].elements[6], MeasureWithCalibratedWaveform)
        assert qp.body.elements[0].elements[6].waveform == "readout"
        assert isinstance(qp.body.elements[0].elements[7], MeasureWithCalibratedWeights)
        assert qp.body.elements[0].elements[7].weights == "weights"
        assert isinstance(qp.body.elements[0].elements[8], MeasureWithCalibratedWaveformWeights)
        assert qp.body.elements[0].elements[8].waveform == "readout"
        assert qp.body.elements[0].elements[8].weights == "weights"

        new_qp = qp.with_calibration(calibration=calibration)

        # Check that qp remain unchanged
        assert qp.has_calibrated_waveforms_or_weights() is True
        assert isinstance(qp.body.elements[0].elements[0], PlayWithCalibratedWaveform)
        assert qp.body.elements[0].elements[0].waveform == "xgate"
        assert isinstance(qp.body.elements[0].elements[1], PlayWithCalibratedWaveform)
        assert qp.body.elements[0].elements[1].waveform == "xgate"
        assert isinstance(qp.body.elements[0].elements[2], AcquireWithCalibratedWeights)
        assert qp.body.elements[0].elements[2].weights == "weights"
        assert isinstance(qp.body.elements[0].elements[3], MeasureWithCalibratedWaveform)
        assert qp.body.elements[0].elements[3].waveform == "readout"
        assert isinstance(qp.body.elements[0].elements[4], MeasureWithCalibratedWeights)
        assert qp.body.elements[0].elements[4].weights == "weights"
        assert isinstance(qp.body.elements[0].elements[5], MeasureWithCalibratedWaveformWeights)
        assert qp.body.elements[0].elements[5].waveform == "readout"
        assert qp.body.elements[0].elements[5].weights == "weights"
        assert isinstance(qp.body.elements[0].elements[6], MeasureWithCalibratedWaveform)
        assert qp.body.elements[0].elements[6].waveform == "readout"
        assert isinstance(qp.body.elements[0].elements[7], MeasureWithCalibratedWeights)
        assert qp.body.elements[0].elements[7].weights == "weights"
        assert isinstance(qp.body.elements[0].elements[8], MeasureWithCalibratedWaveformWeights)
        assert qp.body.elements[0].elements[8].waveform == "readout"
        assert qp.body.elements[0].elements[8].weights == "weights"

        # Check that new_qp has no named operations
        assert new_qp.has_calibrated_waveforms_or_weights() is False
        assert isinstance(new_qp.body.elements[0].elements[0], Play)
        assert isinstance(new_qp.body.elements[0].elements[1], Play)
        assert isinstance(new_qp.body.elements[0].elements[2], Acquire)
        assert isinstance(new_qp.body.elements[0].elements[3], Measure)
        assert isinstance(new_qp.body.elements[0].elements[4], Measure)
        assert isinstance(new_qp.body.elements[0].elements[5], Measure)
        assert isinstance(new_qp.body.elements[0].elements[6], Measure)
        assert isinstance(new_qp.body.elements[0].elements[7], Measure)
        assert isinstance(new_qp.body.elements[0].elements[8], Measure)

    def test_average_method(self):
        """Test acquire_loop method"""
        qp = QProgram()
        with qp.average(shots=1000) as loop:
            # __enter__
            assert isinstance(loop, Average)
            assert loop.shots == 1000
            assert qp._active_block is loop
        # __exit__
        assert len(qp._body.elements) == 1
        assert qp._body.elements[0] is loop
        assert qp._active_block is qp._body

    def test_play_method(self):
        """Test play method"""
        one_wf = Square(amplitude=1.0, duration=40)
        zero_wf = Square(amplitude=0.0, duration=40)
        qp = QProgram()
        qp.play(bus="flux", waveform=one_wf)
        qp.play(bus="drive", waveform=IQPair(I=one_wf, Q=zero_wf))

        assert len(qp._active_block.elements) == 2
        assert len(qp._body.elements) == 2
        assert isinstance(qp._body.elements[0], Play)
        assert qp._body.elements[0].bus == "flux"
        assert np.equal(qp._body.elements[0].waveform, one_wf)
        assert isinstance(qp._body.elements[1], Play)
        assert qp._body.elements[1].bus == "drive"
        assert np.equal(qp._body.elements[1].waveform.I, one_wf)
        assert np.equal(qp._body.elements[1].waveform.Q, zero_wf)

    def test_wait_method(self):
        """Test wait method"""
        qp = QProgram()
        qp.wait(bus="drive", duration=100)

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], Wait)
        assert qp._body.elements[0].bus == "drive"
        assert qp._body.elements[0].duration == 100

    def test_measure_method(self):
        """Test measure method"""
        one_wf = Square(amplitude=1.0, duration=40)
        zero_wf = Square(amplitude=0.0, duration=40)
        qp = QProgram()
        qp.measure(bus="readout", waveform=IQPair(one_wf, zero_wf), weights=IQPair(one_wf, zero_wf))

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], Measure)
        assert qp._body.elements[0].bus == "readout"
        assert np.equal(qp._body.elements[0].waveform.I, one_wf)
        assert np.equal(qp._body.elements[0].waveform.Q, zero_wf)
        assert np.equal(qp._body.elements[0].weights.I, one_wf)
        assert np.equal(qp._body.elements[0].weights.Q, zero_wf)

    def test_acquire_method(self):
        """Test acquire method"""
        one_wf = Square(amplitude=1.0, duration=40)
        zero_wf = Square(amplitude=0.0, duration=40)
        qp = QProgram()
        qp.qblox.acquire(bus="readout", weights=IQPair(I=one_wf, Q=zero_wf))

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], Acquire)
        assert qp._body.elements[0].bus == "readout"
        assert np.equal(qp._body.elements[0].weights.I, one_wf)
        assert np.equal(qp._body.elements[0].weights.Q, zero_wf)

    def test_sync_method(self):
        """Test sync method"""
        qp = QProgram()
        qp.sync(buses=["drive", "flux"])

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], Sync)
        assert qp._body.elements[0].buses == ["drive", "flux"]

    def test_reset_phase(self):
        """Test reset_nco_phase method"""
        qp = QProgram()
        qp.reset_phase(bus="drive")

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], ResetPhase)
        assert qp._body.elements[0].bus == "drive"

    def test_set_phase(self):
        """Test set_nco_phase method"""
        qp = QProgram()
        qp.set_phase(bus="drive", phase=2 * np.pi)

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], SetPhase)
        assert qp._body.elements[0].bus == "drive"
        assert qp._body.elements[0].phase == 2 * np.pi

    def test_set_frequency(self):
        """Test set_nco_frequency method"""
        qp = QProgram()
        qp.set_frequency(bus="drive", frequency=1e6)

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], SetFrequency)
        assert qp._body.elements[0].bus == "drive"
        assert qp._body.elements[0].frequency == 1e6

    def test_set_gain(self):
        """Test set_awg_gain method"""
        qp = QProgram()
        qp.set_gain(bus="drive", gain=1.0)

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], SetGain)
        assert qp._body.elements[0].bus == "drive"
        assert qp._body.elements[0].gain == 1.0

    def test_set_offset(self):
        """Test set_awg_offset method"""
        qp = QProgram()
        qp.set_offset(bus="drive", offset_path0=1.0, offset_path1=0.0)

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], SetOffset)
        assert qp._body.elements[0].bus == "drive"
        assert qp._body.elements[0].offset_path0 == 1.0
        assert qp._body.elements[0].offset_path1 == 0.0

    def test_set_markers(self):
        qp = QProgram()
        qp.qblox.set_markers(bus="drive", mask="0111")

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], SetMarkers)
        assert qp._body.elements[0].bus == "drive"
        assert qp._body.elements[0].mask == "0111"

        with pytest.raises(AttributeError):
            qp.qblox.set_markers(bus="drive", mask="1234")

        with pytest.raises(AttributeError):
            qp.qblox.set_markers(bus="drive", mask="0111011")

    def test_operation_with_variable_of_wrong_domain_raises_error(self):
        """Test that any operation when used with a variable of wrong domain raises an error."""
        qp = QProgram()
        frequency = qp.variable(label="frequency", domain=Domain.Frequency)
        phase = qp.variable(label="phase", domain=Domain.Phase)
        voltage = qp.variable(label="gain", domain=Domain.Voltage)
        time = qp.variable(label="time", domain=Domain.Time)
        scalar = qp.variable(label="float_scalar", domain=Domain.Scalar, type=float)

        all_types = {frequency, phase, voltage, time, scalar}

        for var in all_types - {frequency}:
            with pytest.raises(ValueError):
                qp.set_frequency(bus="drive", frequency=var)

        for var in all_types - {phase}:
            with pytest.raises(ValueError):
                qp.set_phase(bus="drive", phase=var)

        for var in all_types - {voltage}:
            with pytest.raises(ValueError):
                qp.set_offset(bus="drive", offset_path0=var, offset_path1=var)

        for var in all_types - {voltage}:
            with pytest.raises(ValueError):
                qp.set_gain(bus="drive", gain=var)

        for var in all_types - {time}:
            with pytest.raises(ValueError):
                qp.wait(bus="drive", duration=var)

        for amplitude_var, duration_var in set(product(all_types, repeat=2)) - {(voltage, time)}:
            with pytest.raises(ValueError):
                _ = Square(amplitude=amplitude_var, duration=duration_var)

        for amplitude_var, duration_var, num_sigmas_var in set(product(all_types, repeat=3)) - {
            (voltage, time, scalar)
        }:
            with pytest.raises(ValueError):
                _ = Gaussian(amplitude=amplitude_var, duration=duration_var, num_sigmas=num_sigmas_var)

        for var in all_types - {scalar}:
            gaussian = Gaussian(amplitude=1.0, duration=40, num_sigmas=2.5)
            with pytest.raises(ValueError):
                _ = DragCorrection(drag_coefficient=var, waveform=gaussian)

        for amplitude_var, duration_var, num_sigmas_var, drag_coefficient_var in set(product(all_types, repeat=4)) - {
            (voltage, time, scalar, scalar)
        }:
            with pytest.raises(ValueError):
                _ = IQPair.DRAG(
                    amplitude=amplitude_var,
                    duration=duration_var,
                    num_sigmas=num_sigmas_var,
                    drag_coefficient=drag_coefficient_var,
                )

    def test_serialization_deserialization(self):
        """Test serialization and deserialization works."""
        file = "test_serialization_deserialization_qprogram.yml"
        qp = QProgram()
        gain = qp.variable(label="gain", domain=Domain.Voltage)
        with qp.for_loop(variable=gain, start=0.0, stop=1.0, step=0.1):
            qp.set_gain(bus="drive_bus", gain=gain)
            qp.play(bus="drive_bus", waveform=IQPair(I=Square(1.0, 200), Q=Square(1.0, 200)))

        serialized = serialize(qp)
        deserialized_qprogram = deserialize(serialized, QProgram)

        assert isinstance(deserialized_qprogram, QProgram)

        serialize_to(qp, file=file)
        deserialized_qprogram = deserialize_from(file, QProgram)

        assert isinstance(deserialized_qprogram, QProgram)

        os.remove(file)

    def test_measure_reset_method(self):
        """Test measure_reset method"""
        one_wf = Square(amplitude=1.0, duration=40)
        zero_wf = Square(amplitude=0.0, duration=40)
        qp = QProgram()
        qp.qblox.measure_reset(
            measure_bus="readout",
            waveform=IQPair(one_wf, zero_wf),
            weights=IQPair(one_wf, zero_wf),
            control_bus="control",
            reset_pulse=IQPair(one_wf, zero_wf)
        )

        # Should append a single MeasureReset operation
        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1

        op = qp._body.elements[0]
        assert isinstance(op, MeasureReset)
        # Check measurement settings
        assert op.measure_bus == "readout"
        assert np.equal(op.waveform.I, one_wf)
        assert np.equal(op.waveform.Q, zero_wf)
        assert np.equal(op.weights.I, one_wf)
        assert np.equal(op.weights.Q, zero_wf)
        # Check reset settings
        assert op.control_bus == "control"
        assert np.equal(op.reset_pulse.I, one_wf)
        assert np.equal(op.reset_pulse.Q, zero_wf)
        # Defaults for trigger and ADC saving
        assert op.trigger_address == 1
        assert not op.save_adc

        # Interface flags updated
        assert "control" in qp.qblox.latch_enabled
        assert qp.qblox.trigger_network_required["readout"] == 1

    def test_with_bus_mapping_measure_reset(self):
        """Test with_bus_mapping method"""
        qp = QProgram()
        square_wf = Square(1,200)
        drag = IQPair.DRAG(1, 40, 2, 2)
        with qp.average(1000):
                qp.qblox.measure_reset(
                    measure_bus=f"readout_bus",
                    waveform=square_wf,
                    weights=IQPair(I=square_wf, Q=square_wf),
                    control_bus=f"drive_bus",
                    reset_pulse=drag,
                )

        new_qp = qp.with_bus_mapping(bus_mapping={"drive_bus": "drive_q0_bus", "readout_bus": "readout_q0_bus"})
        assert len(new_qp.buses) == 2
        assert "drive_bus" not in new_qp.buses
        assert "readout_bus" not in new_qp.buses
        assert "drive_q0_bus" in new_qp.buses
        assert "readout_q0_bus" in new_qp.buses

        assert new_qp.body.elements[0].elements[0].measure_bus == "readout_q0_bus"
        assert new_qp.body.elements[0].elements[0].control_bus == "drive_q0_bus"

        self_mapping_qp = qp.with_bus_mapping(bus_mapping={"drive_bus": "drive_bus", "readout_bus": "readout_bus"})

        assert len(self_mapping_qp.buses) == 2
        assert "drive_bus" in self_mapping_qp.buses
        assert "readout_bus" in self_mapping_qp.buses

        assert self_mapping_qp.body.elements[0].elements[0].measure_bus == "readout_bus"
        assert self_mapping_qp.body.elements[0].elements[0].control_bus == "drive_bus"

        non_existant_mapping_qp = qp.with_bus_mapping(
            bus_mapping={"non_existant": "drive_bus", "non_existant_readout": "readout_bus"}
        )

        assert len(non_existant_mapping_qp.buses) == 2
        assert "drive_bus" in non_existant_mapping_qp.buses
        assert "readout_bus" in non_existant_mapping_qp.buses

        assert non_existant_mapping_qp.body.elements[0].elements[0].measure_bus == "readout_bus"
        assert non_existant_mapping_qp.body.elements[0].elements[0].control_bus == "drive_bus"
