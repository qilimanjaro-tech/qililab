import os
from collections import deque
from itertools import product

import numpy as np
import pytest

from qililab import Arbitrary, Domain, DragCorrection, Gaussian, IQPair, QProgram, Square
from qililab.qprogram.blocks import Average, Block, ForLoop, InfiniteLoop, Loop, Parallel
from qililab.qprogram.calibration import Calibration
from qililab.qprogram.operations import (
    Acquire,
    AcquireWithCalibratedWeights,
    Measure,
    MeasureWithCalibratedWaveform,
    MeasureWithCalibratedWaveformWeights,
    MeasureWithCalibratedWeights,
    Play,
    PlayWithCalibratedWaveform,
    ResetPhase,
    SetFrequency,
    SetGain,
    SetOffset,
    SetPhase,
    Sync,
    Wait,
)
from qililab.qprogram.variable import FloatVariable, IntVariable
from qililab.utils.serialization import deserialize, deserialize_from, serialize, serialize_to


# pylint: disable=maybe-no-member, protected-access
class TestQProgram:
    """Unit tests checking the QProgram attributes and methods"""

    def test_init(self):
        """Test init method"""
        qp = QProgram()
        assert isinstance(qp._body, Block)
        assert len(qp._body.elements) == 0
        assert isinstance(qp._block_stack, deque)
        assert len(qp._block_stack) == 1
        assert isinstance(qp._variables, list)
        assert len(qp._variables) == 0

    def test_active_block_property(self):
        """Test _active_block property"""
        qp = QProgram()
        assert isinstance(qp._active_block, Block)
        assert qp._active_block is qp._body

    def test_block_method(self):
        """Test block method"""
        qp = QProgram()
        with qp.block() as block:
            # __enter__
            assert isinstance(block, Block)
            assert qp._active_block is block
        # __exit__
        assert len(qp._body.elements) == 1
        assert qp._body.elements[0] is block

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

    def test_infinite_loop_method(self):
        """Test infinite_loop method"""

        qp = QProgram()
        with qp.infinite_loop() as loop:
            # __enter__
            assert isinstance(loop, InfiniteLoop)
            assert qp._active_block is loop
        # __exit__
        assert len(qp._body.elements) == 1
        assert qp._body.elements[0] is loop
        assert qp._active_block is qp._body

    def test_parallel_method(self):
        """Test parallel method"""
        qp = QProgram()
        var1 = qp.variable(Domain.Scalar, int)
        var2 = qp.variable(Domain.Scalar, float)
        with qp.parallel(
            loops=[
                ForLoop(variable=var1, start=0, stop=10, step=1),
                ForLoop(variable=var2, start=0.0, stop=1.0, step=0.1),
            ]
        ) as loop:
            # __enter__
            assert isinstance(loop, Parallel)
            assert len(loop.loops) == 2
            assert qp._active_block is loop
        # __exit__
        assert len(qp._body.elements) == 1
        assert qp._body.elements[0] is loop
        assert qp._active_block is qp._body

    def test_for_loop_method(self):
        """Test loop method"""
        qp = QProgram()
        variable = qp.variable(Domain.Scalar, int)
        start, stop, step = 0, 100, 5
        with qp.for_loop(variable=variable, start=start, stop=stop, step=step) as loop:
            # __enter__
            assert isinstance(loop, ForLoop)
            assert loop.variable == variable
            assert loop.start == start
            assert loop.stop == stop
            assert loop.step == step
            assert qp._active_block is loop
        # __exit__
        assert len(qp._body.elements) == 1
        assert qp._body.elements[0] is loop
        assert qp._active_block is qp._body

    def test_loop_method(self):
        """Test loop method"""
        qp = QProgram()
        variable = qp.variable(Domain.Scalar, int)
        values = np.ones(10, dtype=int)
        with qp.loop(variable=variable, values=values) as loop:
            # __enter__
            assert isinstance(loop, Loop)
            assert loop.variable == variable
            assert np.array_equal(loop.values, values)
            assert qp._active_block is loop
        # __exit__
        assert len(qp._body.elements) == 1
        assert qp._body.elements[0] is loop
        assert qp._active_block is qp._body

    def test_acquire_loop_method(self):
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

    def test_variable_method(self):
        """Test variable method"""
        qp = QProgram()
        frequency_variable = qp.variable(Domain.Frequency)
        phase_variable = qp.variable(Domain.Phase)
        voltage_variable = qp.variable(Domain.Voltage)
        time_variable = qp.variable(Domain.Time)
        int_scalar_variable = qp.variable(Domain.Scalar, int)
        float_scalar_variable = qp.variable(Domain.Scalar, float)

        # Test instantiation
        assert isinstance(frequency_variable, float)
        assert isinstance(frequency_variable, FloatVariable)
        assert frequency_variable.domain is Domain.Frequency
        assert frequency_variable.value is None

        assert isinstance(phase_variable, float)
        assert isinstance(phase_variable, FloatVariable)
        assert phase_variable.domain is Domain.Phase
        assert phase_variable.value is None

        assert isinstance(voltage_variable, float)
        assert isinstance(voltage_variable, FloatVariable)
        assert voltage_variable.domain is Domain.Voltage
        assert voltage_variable.value is None

        assert isinstance(time_variable, int)
        assert isinstance(time_variable, IntVariable)
        assert time_variable.domain is Domain.Time
        assert time_variable.value is None

        assert isinstance(int_scalar_variable, int)
        assert isinstance(int_scalar_variable, IntVariable)
        assert int_scalar_variable.domain is Domain.Scalar
        assert int_scalar_variable.value is None

        assert isinstance(float_scalar_variable, float)
        assert isinstance(float_scalar_variable, FloatVariable)
        assert float_scalar_variable.domain is Domain.Scalar
        assert float_scalar_variable.value is None

        # Test storing in QProgram's _variables
        assert len(qp._variables) == 6

    def test_variable_method_raises_error_if_domain_is_scalar_and_type_is_none(self):
        """Test variable method"""
        qp = QProgram()
        with pytest.raises(ValueError, match="You must specify a type in a scalar variable."):
            qp.variable(Domain.Scalar)

    def test_variable_method_raises_error_if_domain_is_not_scalar_and_type_is_set(self):
        """Test variable method"""
        qp = QProgram()
        with pytest.raises(
            ValueError, match="When declaring a variable of a specific domain, its type is inferred by its domain."
        ):
            qp.variable(Domain.Frequency, int)

    def test_operation_with_variable_of_wrong_domain_raises_error(self):
        """Test that any operation when used with a variable of wrong domain raises an error."""
        qp = QProgram()
        frequency = qp.variable(Domain.Frequency)
        phase = qp.variable(Domain.Phase)
        voltage = qp.variable(Domain.Voltage)
        time = qp.variable(Domain.Time)
        scalar = qp.variable(Domain.Scalar, float)

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
        qp = QProgram()
        gain = qp.variable(domain=Domain.Voltage)
        with qp.for_loop(variable=gain, start=0.0, stop=1.0, step=0.1):
            qp.set_gain(bus="drive_bus", gain=gain)
            qp.play(bus="drive_bus", waveform=IQPair(I=Square(1.0, 200), Q=Square(1.0, 200)))

        serialized = serialize(qp)
        deserialized_qprogram = deserialize(serialized, QProgram)

        assert isinstance(deserialized_qprogram, QProgram)

        serialize_to(qp, file="qprogram.yml")
        deserialized_qprogram = deserialize_from("qprogram.yml", QProgram)

        assert isinstance(deserialized_qprogram, QProgram)

        os.remove("qprogram.yml")
