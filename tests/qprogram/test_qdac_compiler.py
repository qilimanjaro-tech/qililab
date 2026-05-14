import logging
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from qililab.instruments import Instrument, Instruments
from qililab.instruments.qdevil.qdevil_qdac2 import QDevilQDac2
from qililab.platform import Bus
from qililab.qprogram import Calibration, QdacCompiler, QProgram
from qililab.qprogram.blocks.for_loop import ForLoop
from qililab.qprogram.blocks.loop import Loop
from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix, FluxVector
from qililab.qprogram.operations.play import Play
from qililab.qprogram.qdac_compiler import QdacCompilationOutput
from qililab.core.variables import Domain
from qililab.waveforms import Square
from qililab.waveforms.arbitrary import Arbitrary
from qililab.waveforms.iq_pair import IQPair


@pytest.fixture(name="qdac_instrument")
def mock_instrument() -> list[Instrument]:
    instrument1 = MagicMock(spec=QDevilQDac2)
    type(instrument1).alias = property(lambda self: "qdac")
    return [instrument1]


@pytest.fixture(name="calibration")
def fixture_calibration() -> Calibration:
    calibration = Calibration()
    calibration.add_waveform(bus="flux1", name="Xpi", waveform=Square(1.0, 100))

    return calibration


@pytest.fixture(name="flux1")
def fixture_bus_flux1(qdac_instrument) -> Bus:
    settings = {"alias": "flux1", "instruments": ["qdac"], "channels": [1]}
    return Bus(settings=settings, platform_instruments=Instruments(elements=qdac_instrument))


@pytest.fixture(name="flux2")
def fixture_bus_flux2(qdac_instrument) -> Bus:
    settings = {"alias": "flux2", "instruments": ["qdac"], "channels": [2]}
    return Bus(settings=settings, platform_instruments=Instruments(elements=qdac_instrument))


@pytest.fixture(name="flux_no_sync")
def fixture_bus_flux_no_sync(qdac_no_sync: QDevilQDac2) -> Bus:
    settings = {"alias": "flux_no_sync", "instruments": ["qdac_no_sync"], "channels": [1]}
    return Bus(settings=settings, platform_instruments=Instruments(elements=[qdac_no_sync]))


@pytest.fixture(name="flux_qdac1")
def fixture_bus_flux_qdac1(qdac: QDevilQDac2) -> Bus:
    settings = {"alias": "flux_qdac1", "instruments": ["qdac"], "channels": [1]}
    return Bus(settings=settings, platform_instruments=Instruments(elements=[qdac]))


@pytest.fixture(name="flux_qdac2")
def fixture_bus_flux_qdac2(qdac_2: QDevilQDac2) -> Bus:
    settings = {"alias": "flux_qdac2", "instruments": ["qdac_2"], "channels": [1]}
    return Bus(settings=settings, platform_instruments=Instruments(elements=[qdac_2]))


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
            "out_trigger": 1,
            "trigger_sync": True,
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
    qdac.set_out_external_trigger = MagicMock()
    qdac.set_parameter = MagicMock()

    return qdac


@pytest.fixture(name="qdac_no_sync")
def fixture_qdac_no_sync() -> QDevilQDac2:
    """Fixture that returns an instance of a dummy QDAC-II."""
    qdac_no_sync = QDevilQDac2(
        {
            "alias": "qdac_no_sync",
            "voltage": [0.5, 0.5, 0.5, 0.5],
            "span": ["low", "low", "low", "low"],
            "ramping_enabled": [True, True, True, False],
            "ramp_rate": [0.01, 0.01, 0.01, 0.01],
            "dacs": [1, 2, 3, 4],
            "low_pass_filter": ["dc", "dc", "dc", "dc"],
            "out_trigger": 1,
            "trigger_sync": False,
        }
    )
    qdac_no_sync.device = MagicMock()
    qdac_no_sync.set_end_marker_internal_trigger = MagicMock()
    qdac_no_sync.set_start_marker_internal_trigger = MagicMock()
    qdac_no_sync.set_end_marker_external_trigger = MagicMock()
    qdac_no_sync.set_start_marker_external_trigger = MagicMock()
    qdac_no_sync.set_in_external_trigger = MagicMock()
    qdac_no_sync.set_in_internal_trigger = MagicMock()
    qdac_no_sync.upload_voltage_list = MagicMock()
    qdac_no_sync.set_out_external_trigger = MagicMock()
    qdac_no_sync.set_parameter = MagicMock()

    return qdac_no_sync


@pytest.fixture(name="qdac_2")
def fixture_second_qdac() -> QDevilQDac2:
    """Fixture that returns an instance of a dummy QDAC-II."""
    qdac_2 = QDevilQDac2(
        {
            "alias": "qdac_2",
            "voltage": [0.5, 0.5, 0.5, 0.5],
            "span": ["low", "low", "low", "low"],
            "ramping_enabled": [True, True, True, False],
            "ramp_rate": [0.01, 0.01, 0.01, 0.01],
            "dacs": [1, 2, 3, 4],
            "low_pass_filter": ["dc", "dc", "dc", "dc"],
            "in_trigger": 1,
            "trigger_sync": False,
        }
    )
    qdac_2.device = MagicMock()
    qdac_2.device.name = "qdac_2"
    qdac_2.set_end_marker_internal_trigger = MagicMock()
    qdac_2.set_start_marker_internal_trigger = MagicMock()
    qdac_2.set_end_marker_external_trigger = MagicMock()
    qdac_2.set_start_marker_external_trigger = MagicMock()
    qdac_2.set_in_external_trigger = MagicMock()
    qdac_2.set_in_internal_trigger = MagicMock()
    qdac_2.upload_voltage_list = MagicMock()
    qdac_2.set_out_external_trigger = MagicMock()
    qdac_2._cache_dc = {"qdac_2_1": MagicMock()}
    qdac_2.set_parameter = MagicMock()

    return qdac_2


class TestQdacCompiler:
    def test_play_and_set_trigger(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """Test all possible combinations of play + set_trigger on the QDACII."""
        qdac_bus = flux1.instruments[0]

        pulse_wf = Square(1.0, 100)
        dwell_us = 2
        out_port = 1

        # Setting external trigger at the beginning of the iteration
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.set_trigger(bus="flux1", duration=10e-6, outputs=out_port, position="start")

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qprogram == qp
        assert compiler._qdacs == [qdac]
        assert compiler._trigger_position == "front"

        assert qdac_bus.set_start_marker_external_trigger.call_count == 1
        assert qdac_bus.upload_voltage_list.call_count == 2

        # Setting external trigger at the end of the iteration
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.set_trigger(bus="flux1", duration=10e-6, outputs=out_port, position="end")

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qprogram == qp
        assert compiler._qdacs == [qdac]
        assert compiler._trigger_position == "front"

        assert qdac_bus.set_end_marker_external_trigger.call_count == 1
        assert qdac_bus.upload_voltage_list.call_count == 4

        # Setting external trigger at the beginning of each step
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.set_trigger(bus="flux1", duration=10e-6, outputs=out_port, position="step")

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qprogram == qp
        assert compiler._qdacs == [qdac]
        assert compiler._trigger_position == "front"

        assert qdac_bus.set_start_marker_external_trigger.call_count == 2
        assert qdac_bus.upload_voltage_list.call_count == 6

        # Setting external trigger at the end of each step
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.set_trigger(bus="flux1", duration=10e-6, outputs=out_port, position="end_step")

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qprogram == qp
        assert compiler._qdacs == [qdac]
        assert compiler._trigger_position == "front"

        assert qdac_bus.set_end_marker_external_trigger.call_count == 2
        assert qdac_bus.upload_voltage_list.call_count == 8

        # Setting internal trigger at the beginning of the iteration
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.set_trigger(bus="flux1", duration=10e-6, position="start")

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qprogram == qp
        assert compiler._qdacs == [qdac]
        assert compiler._trigger_position == None

        assert qdac_bus.set_start_marker_internal_trigger.call_count == 1
        assert qdac_bus.upload_voltage_list.call_count == 10

        # Setting internal trigger at the end of the iteration
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.set_trigger(bus="flux1", duration=10e-6, position="end")

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qprogram == qp
        assert compiler._qdacs == [qdac]
        assert compiler._trigger_position == None

        assert qdac_bus.set_end_marker_internal_trigger.call_count == 1
        assert qdac_bus.upload_voltage_list.call_count == 12  # accumulative with last calls

        # Setting internal trigger at the beginning of each step
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.set_trigger(bus="flux1", duration=10e-6, position="step")

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qprogram == qp
        assert compiler._qdacs == [qdac]
        assert compiler._trigger_position == None

        assert qdac_bus.upload_voltage_list.call_count == 14
        assert qdac_bus.set_start_marker_internal_trigger.call_count == 2

        # Setting internal trigger at the end of each step
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.set_trigger(bus="flux1", duration=10e-6, position="end_step")

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qprogram == qp
        assert compiler._qdacs == [qdac]
        assert compiler._trigger_position == None

        assert qdac_bus.upload_voltage_list.call_count == 16
        assert qdac_bus.set_end_marker_internal_trigger.call_count == 2

    def test_set_trigger_on_non_trigger_bus_with_existing_dc_list(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """Test set_trigger on a non-trigger bus when a DC list already exists on the trigger bus."""
        qdac_bus = flux1.instruments[0]

        pulse_wf = Square(1.0, 100)
        dwell_us = 2
        out_port = 1

        # Simulate that flux1 (channel 1) already has a cached DC list on the instrument
        qdac.device.name = "qdac"
        qdac._cache_dc = {"qdac_1": MagicMock()}  # "qdac_1" = device.name + "_" + channel of flux1

        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        # set_trigger on flux2, which is NOT a trigger_sync bus
        qp.set_trigger(bus="flux2", duration=10e-6, outputs=out_port, position="start")

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._trigger_position == "front"
        assert qdac_bus.set_start_marker_external_trigger.call_count == 1

    def test_set_trigger_on_non_trigger_bus_no_dc_list_uses_play_params(self, qdac: QDevilQDac2, qdac_2: QDevilQDac2, flux_qdac1: Bus, flux_qdac2: Bus):
        """Test set_trigger on a non-trigger bus when no DC list exists; falls back to _play_params
        to synthesise a constant waveform on the trigger bus."""
        qdac_bus = flux_qdac1.instruments[0]

        pulse_wf = Square(1.0, 100)
        dwell_us = 2
        out_port = 1

        # No cached DC list — forces the fallback path
        qdac.device.name = "qdac"
        qdac._cache_dc = {}

        qp = QProgram()
        qp.qdac.play(bus="flux_qdac1", waveform=pulse_wf, dwell=dwell_us)
        # set_trigger on flux2, which is NOT a trigger_sync bus, and no DC list exists
        qp.set_trigger(bus="flux_qdac2", duration=10e-6, outputs=out_port, position="start")

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac, qdac_2], qdac_buses=[flux_qdac1, flux_qdac2], qdac_offsets=[0, 0], out_instrument=qdac)

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._trigger_position == "front"
        # Once for the original play on flux1 + once for the synthetic constant waveform created by the fallback
        assert qdac_bus.upload_voltage_list.call_count == 2
        assert qdac_bus.set_start_marker_external_trigger.call_count == 1

    def test_set_trigger_on_non_trigger_bus_no_dc_list_no_play_raises_error(
        self, qdac: QDevilQDac2, qdac_2: QDevilQDac2, flux_qdac1: Bus, flux_qdac2: Bus
    ):
        """Test set_trigger on a non-trigger bus with no DC list and no prior play raises ValueError."""
        qdac.device.name = "qdac"
        qdac._cache_dc = {}

        out_port = 1

        # No play at all before set_trigger, so _play_params is never populated
        qp = QProgram()
        qp.set_trigger(bus="flux_qdac2", duration=10e-6, outputs=out_port, position="start")

        compiler = QdacCompiler()
        with pytest.raises(
            ValueError,
            match="No DC list with the given channel ID, first create a DC list using qprogram.play.",
        ):
            compiler.compile(qprogram=qp, qdacs=[qdac, qdac_2], qdac_buses=[flux_qdac1, flux_qdac2], qdac_offsets=[0, 0])

    def test_simultaneous_qdacs(self, qdac: QDevilQDac2, qdac_2: QDevilQDac2, flux_qdac1: Bus, flux_qdac2: Bus):
        """test the behavior of _handle_simultaneous_qdacs for 2 different QDACII."""
        pulse_wf = Square(1.0, 100)
        dwell_us = 2

        qp = QProgram()
        qp.qdac.play(bus="flux_qdac1", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.play(bus="flux_qdac2", waveform=pulse_wf, dwell=dwell_us)

        compiler = QdacCompiler()
        output = compiler.compile(
            qprogram=qp,
            qdacs=[qdac, qdac_2],
            qdac_buses=[flux_qdac1, flux_qdac2],
            qdac_offsets=[0, 0],
            out_instrument=qdac,
        )

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qprogram == qp
        assert compiler._qdacs == [qdac_2, qdac]
        assert compiler._trigger_position == None

        assert qdac.set_out_external_trigger.call_count == 1
        assert qdac_2.set_in_external_trigger.call_count == 1

    def test_crosstalk_compensation(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """Test all possible combinations of play + set_trigger on the QDACII."""
        qdac_bus = flux1.instruments[0]

        crosstalk = CrosstalkMatrix.from_buses(
            buses={"flux1": {"flux1": 1.0, "flux2": 0.5}, "flux2": {"flux1": 0.1, "flux2": 1.0}}
        )
        flux_wf = Arbitrary(samples=np.array([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.4, 0.3, 0.2, 0.1, 0]))
        qp = QProgram()

        freq = qp.variable(label="frequency", domain=Domain.Frequency)

        with qp.average(10):
            qp.set_offset(bus="flux2", offset_path0=0.3)
            with qp.for_loop(variable=freq, start=10e6, stop=100e6, step=10e6):
                qp.qdac.play(bus="flux1", waveform=flux_wf, dwell=2)
                qp.set_offset(bus="flux2", offset_path0=-0.2)
                qp.set_trigger(bus="flux1", duration=10e-6, outputs=1, position="start")

        compiler = QdacCompiler()
        output = compiler.compile(
            qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0], crosstalk=crosstalk
        )

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qdacs == [qdac]

        assert qdac_bus.upload_voltage_list.call_count == 2
        assert qdac_bus.set_parameter.call_count == 0

    def test_crosstalk_compensation_offset(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """Test all possible combinations of play + set_trigger on the QDACII."""
        qdac_bus = flux1.instruments[0]

        crosstalk = CrosstalkMatrix.from_buses(
            buses={"flux1": {"flux1": 1.0, "flux2": 0.5}, "flux2": {"flux1": 0.1, "flux2": 1.0}}
        )
        qp = QProgram()

        freq = qp.variable(label="frequency", domain=Domain.Frequency)

        with qp.average(10):
            qp.set_offset(bus="flux2", offset_path0=0.3)
            with qp.for_loop(variable=freq, start=10e6, stop=100e6, step=10e6):
                qp.set_trigger(bus="flux1", duration=10e-6, outputs=1, position="start")

        compiler = QdacCompiler()
        output = compiler.compile(
            qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0], crosstalk=crosstalk
        )

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qdacs == [qdac]

        assert qdac_bus.upload_voltage_list.call_count == 0
        assert qdac_bus.set_parameter.call_count == 2

    def test_crosstalk_compensation_calibration(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """Test all possible combinations of play + set_trigger on the QDACII."""
        qdac_bus = flux1.instruments[0]

        crosstalk = CrosstalkMatrix.from_buses(
            buses={"flux1": {"flux1": 1.0, "flux2": 0.5}, "flux2": {"flux1": 0.1, "flux2": 1.0}}
        )
        calibration = Calibration()
        calibration.crosstalk_matrix = crosstalk

        flux_wf = Arbitrary(samples=np.array([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.4, 0.3, 0.2, 0.1, 0]))
        qp = QProgram()

        freq = qp.variable(label="frequency", domain=Domain.Frequency)

        with qp.average(10):
            qp.set_offset(bus="flux2", offset_path0=0.3)
            with qp.for_loop(variable=freq, start=10e6, stop=100e6, step=10e6):
                qp.qdac.play(bus="flux1", waveform=flux_wf, dwell=2)
                qp.set_offset(bus="flux2", offset_path0=-0.2)
                qp.set_trigger(bus="flux1", duration=10e-6, outputs=1, position="start")

        compiler = QdacCompiler()
        output = compiler.compile(
            qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0], calibration=calibration
        )

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qdacs == [qdac]

        assert qdac_bus.upload_voltage_list.call_count == 2
        assert qdac_bus.set_parameter.call_count == 0

    def test_crosstalk_no_trigger_buses_raises_error(self, qdac_no_sync: QDevilQDac2, flux_no_sync: Bus):
        """Test error raised when no trigger_sync is added in the runcard."""
        flux_wf = Arbitrary(samples=np.array([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.4, 0.3, 0.2, 0.1, 0]))
        qp = QProgram()

        freq = qp.variable(label="frequency", domain=Domain.Frequency)

        with qp.average(10):
            with qp.for_loop(variable=freq, start=10e6, stop=100e6, step=10e6):
                qp.qdac.play(bus="flux_no_sync", waveform=flux_wf, dwell=2)
                qp.set_trigger(bus="flux_no_sync", duration=10e-6, outputs=1, position="start")

        compiler = QdacCompiler()
        with pytest.raises(
            ValueError,
            match="Cannot set Trigger without instrument set as trigger_sync = True. Modify the runcard and add trigger_sync to a QDAC II instrument.",
        ):
            compiler.compile(
                qprogram=qp,
                qdacs=[qdac_no_sync],
                qdac_buses=[flux_no_sync],
                qdac_offsets=[0],
            )

    def test_crosstalk_compensation_IQPair(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """Test all possible combinations of play + set_trigger on the QDACII."""
        qdac_bus = flux1.instruments[0]

        crosstalk = CrosstalkMatrix.from_buses(
            buses={"flux1": {"flux1": 1.0, "flux2": 0.5}, "flux2": {"flux1": 0.1, "flux2": 1.0}}
        )
        flux_wf = IQPair(
            Arbitrary(samples=np.array([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.4, 0.3, 0.2, 0.1, 0])),
            Arbitrary(samples=np.array([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.4, 0.3, 0.2, 0.1, 0])),
        )
        qp = QProgram()

        freq = qp.variable(label="frequency", domain=Domain.Frequency)

        with qp.average(10):
            qp.set_offset(bus="flux2", offset_path0=0.3)
            with qp.for_loop(variable=freq, start=10e6, stop=100e6, step=10e6):
                qp.qdac.play(bus="flux1", waveform=flux_wf, dwell=2)
                qp.set_offset(bus="flux2", offset_path0=-0.2)
                qp.set_trigger(bus="flux1", duration=10e-6, outputs=1, position="start")

        compiler = QdacCompiler()
        output = compiler.compile(
            qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0], crosstalk=crosstalk
        )

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qdacs == [qdac]

        assert qdac_bus.upload_voltage_list.call_count == 2
        assert qdac_bus.set_parameter.call_count == 0

    def test_different_size_plays_raises_error(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """Test all possible combinations of play + set_trigger on the QDACII."""

        crosstalk = CrosstalkMatrix.from_buses(
            buses={"flux1": {"flux1": 1.0, "flux2": 0.5}, "flux2": {"flux1": 0.1, "flux2": 1.0}}
        )
        flux_wf = Arbitrary(samples=np.array([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.4, 0.3, 0.2, 0.1, 0]))
        flux_wf_wrong = Arbitrary(samples=np.array([0.1, 0]))
        qp = QProgram()

        qp.qdac.play(bus="flux1", waveform=flux_wf, dwell=2)
        qp.qdac.play(bus="flux2", waveform=flux_wf_wrong, dwell=2)
        qp.set_trigger(bus="flux1", duration=10e-6, outputs=1, position="start")

        compiler = QdacCompiler()

        with pytest.raises(
            ValueError,
            match="qp.play elements must have the same size.",
        ):
            compiler.compile(
                qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0], crosstalk=crosstalk
            )

    def test_play_bus_map(self, qdac: QDevilQDac2, flux1: Bus):
        """Test all possible combinations of play + set_trigger on the QDACII."""
        qdac_bus = flux1.instruments[0]

        pulse_wf = Square(1.0, 100)
        dwell_us = 2

        # Setting external trigger at the beginning of the iteration
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)

        compiler = QdacCompiler()
        compiler.compile(
            qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0], bus_mapping={"flux1": "flux1"}
        )

        assert qdac_bus.upload_voltage_list.call_count == 1

    def test_play_named_operation_in_calibration(self, calibration: Calibration, qdac: QDevilQDac2, flux1: Bus):
        qdac_bus = flux1.instruments[0]

        qp = QProgram()
        qp.play(bus="flux1", waveform="Xpi")

        compiler = QdacCompiler()
        compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], calibration=calibration, qdac_offsets=[0])

        qdac_bus.upload_voltage_list.assert_called_with(
            waveform=calibration.get_waveform(bus="flux1", name="Xpi"),
            channel_id=1,
            dwell_us=2,
            sync_delay_s=0,
            repetitions=1,
            stepped=False,
        )

    def test_play_incorrect_named_operation_raises_error(self, qdac: QDevilQDac2, flux1: Bus):
        calibration = Calibration()
        qp = QProgram()
        qp.play(bus="flux1", waveform="Xpi")

        compiler = QdacCompiler()
        with pytest.raises(RuntimeError):
            _ = compiler.compile(
                qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0], calibration=calibration
            )

    def test_play_repetitions(self, qdac: QDevilQDac2, flux1: Bus):
        """Test all possible combinations of play repetitions as a manual input."""
        qdac_bus = flux1.instruments[0]

        wf = Square(1.0, 100)
        dwell = 2
        # default repetitions, without loops is 1
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=wf, dwell=dwell)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

        assert isinstance(output, QdacCompilationOutput)
        qdac_bus.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell, sync_delay_s=0, repetitions=1, stepped=False
        )

        # 100 repetitions
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=wf, dwell=dwell, repetitions=100)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

        assert isinstance(output, QdacCompilationOutput)
        qdac_bus.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell, sync_delay_s=0, repetitions=100, stepped=False
        )

        # Infinite repetitions (repetitions = -1)
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=wf, dwell=dwell, repetitions=-1)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

        assert isinstance(output, QdacCompilationOutput)
        qdac_bus.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell, sync_delay_s=0, repetitions=-1, stepped=False
        )

    def test_play_and_set_trigger_no_position_raises_trigger(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """Test all possible combinations of play + set_trigger on the QDACII."""
        pulse_wf = Square(1.0, 100)
        dwell_us = 2
        out_port = 1

        wrong_position = "right"

        # Setting external trigger at the beginning of the iteration
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.set_trigger(bus="flux1", duration=10e-6, outputs=out_port, position=wrong_position)

        compiler = QdacCompiler()
        with pytest.raises(
            NotImplementedError,
            match=f"position must be set as 'end', 'start', 'step' or 'end_step'. {wrong_position} is not recognized",
        ):
            compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

    def test_play_operation_with_variable_in_waveform(self, caplog, qdac: QDevilQDac2, flux1: Bus):

        qp = QProgram()
        amplitude = qp.variable(label="amplitude", domain=Domain.Voltage)
        qp.qdac.play(bus="flux1", waveform=Square(amplitude, 100), dwell=2)

        compiler = QdacCompiler()
        with caplog.at_level(logging.ERROR):
            _ = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

        assert "Variables in waveforms are not supported in Qdac." in caplog.text

    def test_loops_repetitions(self, qdac: QDevilQDac2, flux1: Bus):
        """Test all possible combinations of play repetitions as a manual input."""
        qdac_bus = flux1.instruments[0]

        wf = Square(1.0, 100)
        dwell = 2

        # Average loop
        qp = QProgram()
        with qp.average(5):
            qp.qdac.play(bus="flux1", waveform=wf, dwell=dwell)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

        assert isinstance(output, QdacCompilationOutput)
        qdac_bus.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell, sync_delay_s=0, repetitions=6, stepped=False
        )

        # For loop
        qp = QProgram()
        loop_variable = qp.variable("test", Domain.Time)
        with qp.for_loop(loop_variable, 0, 10, 1):
            qp.qdac.play(bus="flux1", waveform=wf, dwell=dwell)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

        # For loop decimals
        qp = QProgram()
        loop_variable = qp.variable("test", Domain.Voltage)
        with qp.for_loop(loop_variable, 0, 0.1, 0.011):
            qp.qdac.play(bus="flux1", waveform=wf, dwell=dwell)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

        assert isinstance(output, QdacCompilationOutput)
        qdac_bus.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell, sync_delay_s=0, repetitions=11, stepped=False
        )

        # Arbitrary loop
        qp = QProgram()
        loop_variable = qp.variable("test", Domain.Time)
        with qp.loop(loop_variable, np.array([1, 2, 3])):
            qp.qdac.play(bus="flux1", waveform=wf, dwell=dwell)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

        assert isinstance(output, QdacCompilationOutput)
        qdac_bus.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell, sync_delay_s=0, repetitions=4, stepped=False
        )

        # Parallel loop
        qp = QProgram()
        loop_variable = qp.variable("test", Domain.Time)
        loop_variable_2 = qp.variable("test2", Domain.Time)
        with qp.parallel([Loop(loop_variable, np.array([1, 2])), ForLoop(loop_variable_2, 0, 1, 1)]):
            qp.qdac.play(bus="flux1", waveform=wf, dwell=dwell)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

        assert isinstance(output, QdacCompilationOutput)
        qdac_bus.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell, sync_delay_s=0, repetitions=3, stepped=False
        )

        # Combining loops

        # Average loop
        qp = QProgram()
        loop_variable = qp.variable("test", Domain.Time)
        loop_variable_2 = qp.variable("test2", Domain.Time)
        loop_variable_3 = qp.variable("test3", Domain.Time)
        with qp.average(5):
            with qp.loop(loop_variable, np.array([1, 2, 3])):
                with qp.for_loop(loop_variable_3, 0, 10, 1):
                    qp.qdac.play(bus="flux1", waveform=wf, dwell=dwell)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

        assert isinstance(output, QdacCompilationOutput)
        qdac_bus.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell, sync_delay_s=0, repetitions=288, stepped=False
        )

        # Infinite loop
        qp = QProgram()
        with qp.infinite_loop():
            qp.qdac.play(bus="flux1", waveform=wf, dwell=dwell)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

        assert isinstance(output, QdacCompilationOutput)
        qdac_bus.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell, sync_delay_s=0, repetitions=-1, stepped=False
        )

        # Infinite loop with other loops is still infinite
        qp = QProgram()
        loop_variable = qp.variable("test", Domain.Time)
        with qp.infinite_loop():
            with qp.for_loop(loop_variable, 0, 10, 1):
                qp.qdac.play(bus="flux1", waveform=wf, dwell=dwell)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

        assert isinstance(output, QdacCompilationOutput)
        qdac_bus.upload_voltage_list.assert_called_with(
            waveform=wf, channel_id=1, dwell_us=dwell, sync_delay_s=0, repetitions=-1, stepped=False
        )

    def test_for_loops_with_no_iterations_raises_error(self, qdac: QDevilQDac2, flux1: Bus):
        """Test all possible combinations of play repetitions as a manual input."""
        wf = Square(1.0, 100)
        dwell = 2
        # Linspace loop
        qp = QProgram()
        loop_variable = qp.variable("test", Domain.Time)
        with qp.for_loop(loop_variable, 0, 10, 0):
            qp.qdac.play(bus="flux1", waveform=wf, dwell=dwell)

        compiler = QdacCompiler()
        with pytest.raises(ValueError, match="Step value cannot be zero"):
            compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

    def test_play_wait_trigger(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """Test all possible combinations of play + set_trigger on the QDACII."""
        qdac_bus = flux1.instruments[0]

        pulse_wf = Square(1.0, 100)
        dwell_us = 2
        in_port = 1

        # Setting wait trigger at external
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.wait_trigger(bus="flux1", duration=10e-6, port=in_port)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qprogram == qp
        assert compiler._qdacs == [qdac]
        assert compiler._trigger_position == "back"

        qdac_bus.set_in_external_trigger.assert_called_once()
        assert qdac_bus.upload_voltage_list.call_count == 2

        # Setting external trigger at the end of the iteration
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.set_trigger(bus="flux1", duration=10e-6, position="start")
        qp.wait_trigger(bus="flux1", duration=10e-6)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qprogram == qp
        assert compiler._qdacs == [qdac]
        assert compiler._trigger_position == None

        qdac_bus.set_in_internal_trigger.assert_called_once()
        qdac_bus.set_start_marker_internal_trigger.assert_called_once()
        assert qdac_bus.upload_voltage_list.call_count == 4

    def test_block_operation(self, qdac: QDevilQDac2, flux1: Bus):
        """Test all possible combinations of play + set_trigger on the QDACII."""
        qdac_bus = flux1.instruments[0]

        pulse_wf = Square(1.0, 100)
        dwell_us = 2

        # Setting external trigger at the beginning of the iteration
        qp = QProgram()
        with qp.block():
            qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)

        compiler = QdacCompiler()
        compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

        assert qdac_bus.upload_voltage_list.call_count == 1

    def test_sync_raises_error(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """Test all possible combinations of play + set_trigger on the QDACII."""
        pulse_wf = Square(1.0, 100)
        dwell_us = 2

        # Setting external trigger at the beginning of the iteration
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.sync(buses=["flux1", "flux2"])

        compiler = QdacCompiler()
        with pytest.raises(
            NotImplementedError, match=f"<class 'qililab.qprogram.operations.sync.Sync'> is not supported in QDACII."
        ):
            compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

    def test_handle_unknown_crosstalk(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """Test all possible combinations of play + set_trigger on the QDACII."""
        pulse_wf = Square(1.0, 100)
        dwell_us = 2
        crosstalk = CrosstalkMatrix.from_buses(
            buses={"flux1": {"flux1": 1.0, "flux2": 0.5}, "flux2": {"flux1": 0.1, "flux2": 1.0}}
        )

        # Setting external trigger at the beginning of the iteration
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.sync(buses=["flux1", "flux2"])

        compiler = QdacCompiler()
        with pytest.raises(
            NotImplementedError, match=f"<class 'qililab.qprogram.operations.sync.Sync'> is not supported in QDACII."
        ):
            compiler.compile(
                qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0], crosstalk=crosstalk
            )
