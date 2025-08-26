import logging
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from qililab.platform import Bus
from qililab.qprogram.blocks.for_loop import ForLoop
from qililab.qprogram.blocks.loop import Loop
from qililab.qprogram.qdac_compiler import QdacCompilationOutput
from qililab.qprogram.variable import Domain
from qililab.waveforms import Square
from qililab.instruments import Instrument, Instruments
from qililab.instruments.qdevil.qdevil_qdac2 import QDevilQDac2
from qililab.qprogram import QProgram, Calibration, QdacCompiler


@pytest.fixture(name="qdac_instrument")
def mock_instrument() -> list[Instrument]:
    instrument1 = MagicMock(spec=QDevilQDac2)
    type(instrument1).alias = property(lambda self: "qdac")
    return [instrument1]


@pytest.fixture(name="flux1")
def fixture_bus_flux1(qdac_instrument) -> Bus:
    settings = {"alias": "flux1", "instruments": ["qdac"], "channels": [1]}
    return Bus(settings=settings, platform_instruments=Instruments(elements=qdac_instrument))


@pytest.fixture(name="flux2")
def fixture_bus_flux2(qdac_instrument) -> Bus:
    settings = {"alias": "flux2", "instruments": ["qdac"], "channels": [2]}
    return Bus(settings=settings, platform_instruments=Instruments(elements=qdac_instrument))


@pytest.fixture(name="qdac")
def fixture_qdac() -> QDevilQDac2:
    """Fixture that returns an instance of a dummy QDAC-II."""
    qdac = QDevilQDac2(
        {
            "alias": "qdac",
            "voltage": [0.5, 0.5, 0.5, 0.5],
            "span": ["low", "low", "low", "low"],
            "ramping_enabled": [True, True, True, False],
            "ramp_rate": [0.01, 0.01, 0.01, 0.01],
            "dacs": [1, 2, 3, 4],
            "low_pass_filter": ["dc", "dc", "dc", "dc"],
        }
    )
    qdac.device = MagicMock()
    qdac.set_end_marker_internal_trigger = MagicMock()
    qdac.set_start_marker_internal_trigger = MagicMock()
    qdac.set_end_marker_external_trigger = MagicMock()
    qdac.set_start_marker_external_trigger = MagicMock()
    qdac.set_in_external_trigger = MagicMock()
    qdac.set_in_internal_trigger = MagicMock()
    qdac.upload_voltage_list = MagicMock()

    return qdac


@pytest.fixture(name="calibration")
def fixture_calibration() -> Calibration:
    calibration = Calibration()
    calibration.add_waveform(bus="flux1", name="calibrated_square", waveform=Square(1.0, 100))

    return calibration


@pytest.fixture(name="calibrated_execution")
def fixture_calibrated_execution() -> QProgram:
    qp = QProgram()
    qp.play(bus="flux1", waveform="calibrated_square")
    return qp


class TestQdacCompiler:
    def test_play_and_set_trigger(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """Test all possible combinations of play + set_trigger on the QDACII."""
        pulse_wf = Square(1.0, 100)
        dwell_us = 2
        out_port = 1

        # Setting external trigger at the beginning of the iteration
        qp = QProgram()
        qp.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.set_trigger(bus="flux1", duration=10e-6, outputs=out_port, position="start")

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdac=qdac, qdac_buses=[flux1, flux2])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qprogram == qp
        assert compiler._qdac == qdac
        assert compiler._trigger_position == "front"

        qdac.set_start_marker_external_trigger.assert_called_once()
        assert qdac.upload_voltage_list.call_count == 2

        # Setting external trigger at the end of the iteration
        qp = QProgram()
        qp.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.set_trigger(bus="flux1", duration=10e-6, outputs=out_port, position="end")

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdac=qdac, qdac_buses=[flux1, flux2])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qprogram == qp
        assert compiler._qdac == qdac
        assert compiler._trigger_position == "front"

        qdac.set_end_marker_external_trigger.assert_called_once()
        assert qdac.upload_voltage_list.call_count == 4

        # Setting internal trigger at the beginning of the iteration
        qp = QProgram()
        qp.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.set_trigger(bus="flux1", duration=10e-6, position="start")

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdac=qdac, qdac_buses=[flux1, flux2])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qprogram == qp
        assert compiler._qdac == qdac
        assert compiler._trigger_position == None

        qdac.set_start_marker_internal_trigger.assert_called_once()
        assert qdac.upload_voltage_list.call_count == 6

        # Setting internal trigger at the end of the iteration
        qp = QProgram()
        qp.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.set_trigger(bus="flux1", duration=10e-6, position="end")

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdac=qdac, qdac_buses=[flux1, flux2])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qprogram == qp
        assert compiler._qdac == qdac
        assert compiler._trigger_position == None

        qdac.set_end_marker_internal_trigger.assert_called_once()
        assert qdac.upload_voltage_list.call_count == 8  # accumulative with last calls

    def test_play_repetitions(self, qdac: QDevilQDac2, flux1: Bus):
        """Test all possible combinations of play repetitions as a manual input."""
        wf = Square(1.0, 100)
        dwell = 2
        # default repetitions, without loops is 1
        qp = QProgram()
        qp.play(bus="flux1", waveform=wf, dwell=dwell)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdac=qdac, qdac_buses=[flux1])

        assert isinstance(output, QdacCompilationOutput)
        qdac.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell * 1e-6, sync_delay_s=0, repetitions=1
        )

        # 100 repetitions
        qp = QProgram()
        qp.play(bus="flux1", waveform=wf, dwell=dwell, repetitions=100)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdac=qdac, qdac_buses=[flux1])

        assert isinstance(output, QdacCompilationOutput)
        qdac.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell * 1e-6, sync_delay_s=0, repetitions=100
        )

        # Infinite repetitions (repetitions = -1)
        qp = QProgram()
        qp.play(bus="flux1", waveform=wf, dwell=dwell, repetitions=-1)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdac=qdac, qdac_buses=[flux1])

        assert isinstance(output, QdacCompilationOutput)
        qdac.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell * 1e-6, sync_delay_s=0, repetitions=-1
        )

    def test_play_and_set_trigger_no_position_raises_trigger(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """Test all possible combinations of play + set_trigger on the QDACII."""
        pulse_wf = Square(1.0, 100)
        dwell_us = 2
        out_port = 1

        wrong_position = "right"

        # Setting external trigger at the beginning of the iteration
        qp = QProgram()
        qp.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.set_trigger(bus="flux1", duration=10e-6, outputs=out_port, position=wrong_position)

        compiler = QdacCompiler()
        with pytest.raises(
            NotImplementedError, match=f"position must be set as 'end' or 'start', {wrong_position} is not recognized"
        ):
            compiler.compile(qprogram=qp, qdac=qdac, qdac_buses=[flux1, flux2])

    def test_play_operation_with_variable_in_waveform(self, caplog, qdac: QDevilQDac2, flux1: Bus):

        qp = QProgram()
        amplitude = qp.variable(label="amplitude", domain=Domain.Voltage)
        qp.play(bus="flux1", waveform=Square(amplitude, 100), dwell=2)

        compiler = QdacCompiler()
        with caplog.at_level(logging.ERROR):
            _ = compiler.compile(qprogram=qp, qdac=qdac, qdac_buses=[flux1])

        assert "Variables in waveforms are not supported in Qdac." in caplog.text

    def test_loops_repetitions(self, qdac: QDevilQDac2, flux1: Bus):
        """Test all possible combinations of play repetitions as a manual input."""
        wf = Square(1.0, 100)
        dwell = 2

        # Average loop
        qp = QProgram()
        with qp.average(5):
            qp.play(bus="flux1", waveform=wf, dwell=dwell)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdac=qdac, qdac_buses=[flux1])

        assert isinstance(output, QdacCompilationOutput)
        qdac.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell * 1e-6, sync_delay_s=0, repetitions=6
        )

        # For loop
        qp = QProgram()
        loop_variable = qp.variable("test", Domain.Time)
        with qp.for_loop(loop_variable, 0, 10, 1):
            qp.play(bus="flux1", waveform=wf, dwell=dwell)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdac=qdac, qdac_buses=[flux1])

        assert isinstance(output, QdacCompilationOutput)
        qdac.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell * 1e-6, sync_delay_s=0, repetitions=12
        )

        # Linspace loop
        qp = QProgram()
        loop_variable = qp.variable("test", Domain.Time)
        with qp.linspace_loop(loop_variable, 0, 10, 10):
            qp.play(bus="flux1", waveform=wf, dwell=dwell)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdac=qdac, qdac_buses=[flux1])

        assert isinstance(output, QdacCompilationOutput)
        qdac.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell * 1e-6, sync_delay_s=0, repetitions=11
        )

        # Arbitrary loop
        qp = QProgram()
        loop_variable = qp.variable("test", Domain.Time)
        with qp.loop(loop_variable, np.array([1, 2, 3])):
            qp.play(bus="flux1", waveform=wf, dwell=dwell)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdac=qdac, qdac_buses=[flux1])

        assert isinstance(output, QdacCompilationOutput)
        qdac.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell * 1e-6, sync_delay_s=0, repetitions=4
        )

        # Parallel loop
        qp = QProgram()
        loop_variable = qp.variable("test", Domain.Time)
        loop_variable_2 = qp.variable("test2", Domain.Time)
        with qp.parallel([Loop(loop_variable, np.array([1, 2])), ForLoop(loop_variable_2, 0, 1, 1)]):
            qp.play(bus="flux1", waveform=wf, dwell=dwell)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdac=qdac, qdac_buses=[flux1])

        assert isinstance(output, QdacCompilationOutput)
        qdac.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell * 1e-6, sync_delay_s=0, repetitions=3
        )

        # Combining loops

        # Average loop
        qp = QProgram()
        loop_variable = qp.variable("test", Domain.Time)
        loop_variable_2 = qp.variable("test2", Domain.Time)
        loop_variable_3 = qp.variable("test3", Domain.Time)
        with qp.average(5):
            with qp.loop(loop_variable, np.array([1, 2, 3])):
                with qp.linspace_loop(loop_variable_2, 0, 10, 10):
                    with qp.for_loop(loop_variable_3, 0, 10, 1):
                        qp.play(bus="flux1", waveform=wf, dwell=dwell)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdac=qdac, qdac_buses=[flux1])

        assert isinstance(output, QdacCompilationOutput)
        qdac.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell * 1e-6, sync_delay_s=0, repetitions=3168
        )

        # Infinite loop
        qp = QProgram()
        with qp.infinite_loop():
            qp.play(bus="flux1", waveform=wf, dwell=dwell)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdac=qdac, qdac_buses=[flux1])

        assert isinstance(output, QdacCompilationOutput)
        qdac.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell * 1e-6, sync_delay_s=0, repetitions=-1
        )

        # Infinite loop with other loops is still infinite
        qp = QProgram()
        loop_variable = qp.variable("test", Domain.Time)
        with qp.infinite_loop():
            with qp.for_loop(loop_variable, 0, 10, 1):
                qp.play(bus="flux1", waveform=wf, dwell=dwell)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdac=qdac, qdac_buses=[flux1])

        assert isinstance(output, QdacCompilationOutput)
        qdac.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell * 1e-6, sync_delay_s=0, repetitions=-1
        )
