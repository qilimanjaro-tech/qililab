import contextlib
import re
from unittest.mock import ANY, MagicMock, call

import numpy as np
import pytest
from qprogram import ValidationError
from qprogram.blocks import Block
from qprogram_qdac import Play as QdacPlay

from qililab import Arbitrary, IQPair, Square
from qililab.instruments import Instrument, Instruments
from qililab.instruments.qdevil.qdevil_qdac2 import QDevilQDac2
from qililab.platform import Bus
from qililab.qprogram import Calibration, QdacCompiler, QProgram
from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix, NonLinearCrosstalkMatrix
from qililab.qprogram.qdac_compiler import QdacCompilationOutput
from qililab.typings.enums import Parameter

def _collect_plays(block: Block) -> dict:
    """Collect the (last) QDAC play per bus from a possibly nested compiled QProgram block."""
    plays: dict = {}

    def _walk(blk: Block) -> None:
        for element in blk.elements:
            if isinstance(element, QdacPlay):
                plays[element.bus] = element
            if isinstance(element, Block):
                _walk(element)

    _walk(block)
    return plays


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
        """Test all possible combinations of play + external set_trigger on the QDACII."""
        qdac_bus = flux1.instruments[0]

        pulse_wf = Square(1.0, 100)
        dwell_us = 2
        out_port = 1

        # Setting external trigger at the beginning of the iteration
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.set_trigger(bus="flux1", duration=10e-6, outputs=[out_port], position="start")

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qdacs == [qdac]
        assert compiler._trigger_position == "front"

        assert qdac_bus.set_start_marker_external_trigger.call_count == 1
        assert qdac_bus.upload_voltage_list.call_count == 2

        # Setting external trigger at the end of the iteration
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.set_trigger(bus="flux1", duration=10e-6, outputs=[out_port], position="end")

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qdacs == [qdac]
        assert compiler._trigger_position == "front"

        assert qdac_bus.set_end_marker_external_trigger.call_count == 1
        assert qdac_bus.upload_voltage_list.call_count == 4

        # Setting external trigger at the beginning of each step
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.set_trigger(bus="flux1", duration=10e-6, outputs=[out_port], position="step")

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qdacs == [qdac]
        assert compiler._trigger_position == "front"

        assert qdac_bus.set_start_marker_external_trigger.call_count == 2
        assert qdac_bus.upload_voltage_list.call_count == 6

        # Setting external trigger at the end of each step
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.set_trigger(bus="flux1", duration=10e-6, outputs=[out_port], position="end_step")

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qdacs == [qdac]
        assert compiler._trigger_position == "front"

        assert qdac_bus.set_end_marker_external_trigger.call_count == 2
        assert qdac_bus.upload_voltage_list.call_count == 8


    def test_set_trigger_on_non_trigger_bus_with_existing_dc_list(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """Test set_trigger on a non-trigger bus when a DC list already exists on the trigger bus."""
        qdac_bus = flux1.instruments[0]

        pulse_wf = Square(1.0, 100)
        dwell_us = 2
        out_port = 1

        # Simulate that flux1 (channel 1) already has a cached DC list on the instrument
        qdac.device.name = "qdac"
        # "qdac_1" = device.name + "_" + channel of flux1
        qdac._cache_dc = {"qdac_1": MagicMock()}

        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        # set_trigger on flux2, which is NOT a trigger_sync bus
        qp.qdac.set_trigger(bus="flux2", duration=10e-6, outputs=[out_port], position="start")

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
        qp.qdac.set_trigger(bus="flux_qdac2", duration=10e-6, outputs=[out_port], position="start")

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
        qp.qdac.set_trigger(bus="flux_qdac2", duration=10e-6, outputs=[out_port], position="start")

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
        qp.qdac.set_offset(bus="flux2", offset=0.3)
        qp.qdac.play(bus="flux1", waveform=flux_wf, dwell=2)
        qp.qdac.set_offset(bus="flux2", offset=-0.2)
        qp.qdac.set_trigger(bus="flux1", duration=10e-6, outputs=[1], position="start")

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
        qp.qdac.set_offset(bus="flux2", offset=0.3)
        qp.qdac.set_trigger(bus="flux1", duration=10e-6, outputs=[1], position="start")

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
        qp.qdac.set_offset(bus="flux2", offset=0.3)
        qp.qdac.play(bus="flux1", waveform=flux_wf, dwell=2)
        qp.qdac.set_offset(bus="flux2", offset=-0.2)
        qp.qdac.set_trigger(bus="flux1", duration=10e-6, outputs=[1], position="start")

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
        qp.qdac.play(bus="flux_no_sync", waveform=flux_wf, dwell=2)
        qp.qdac.set_trigger(bus="flux_no_sync", duration=10e-6, outputs=[1], position="start")

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

    def test_play_iq_pair_raises_error(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """A QDAC play takes a single waveform: an IQPair fails validation (it used to play its I waveform)."""
        crosstalk = CrosstalkMatrix.from_buses(
            buses={"flux1": {"flux1": 1.0, "flux2": 0.5}, "flux2": {"flux1": 0.1, "flux2": 1.0}}
        )
        flux_wf = Arbitrary(samples=np.array([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.4, 0.3, 0.2, 0.1, 0]))
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=IQPair(flux_wf, flux_wf), dwell=2)
        qp.qdac.set_trigger(bus="flux1", duration=10e-6, outputs=[1], position="start")

        compiler = QdacCompiler()
        with pytest.raises(ValidationError, match=re.escape("'Play' requires capability 'waveform.iq_pair'")):
            compiler.compile(
                qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0], crosstalk=crosstalk
            )

    def test_crosstalk_compensation_target_fluxes(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """Regression (QDAC-ramp double-count): the compiler seeds the parked point from
        ``target_fluxes`` (not by inverting the hardware bias), so a non-swept bus's compensated
        play equals the forward flux_to_bias of its true target — the nonlinear correction applied
        exactly once. ``flux2`` is parked ONLY via target_fluxes (no operation in the program)."""
        crosstalk = CrosstalkMatrix.from_array(["flux1", "flux2"], np.linalg.inv([[1, 0.5], [0.5, 1]]))
        nonlinear = NonLinearCrosstalkMatrix.from_linear(crosstalk)
        nonlinear.set_non_linear_params("flux2", "flux1", junction_asym=0.2)

        ramp = np.array([0.0, 0.1, 0.2, 0.3, 0.2, 0.1, 0.0])
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=Arbitrary(ramp), dwell=2)  # swept bus
        qp.qdac.set_trigger(bus="flux1", duration=10e-6, outputs=[1], position="start")

        compiler = QdacCompiler()
        output = compiler.compile(
            qprogram=qp,
            qdacs=[qdac],
            qdac_buses=[flux1, flux2],
            qdac_offsets=[0, 0],
            crosstalk=nonlinear,
            target_fluxes={"flux1": 0.0, "flux2": 0.1},
        )

        plays = _collect_plays(output.qprogram.body)
        assert {"flux1", "flux2"} <= set(plays)
        got2 = np.asarray(plays["flux2"].waveform.envelope(), dtype=float)
        for i, v in enumerate(ramp):
            ref = nonlinear.flux_to_bias({"flux1": float(v), "flux2": 0.1})  # flux2 held at its target
            assert got2[i] == pytest.approx(float(ref["flux2"]), rel=1e-9, abs=1e-12)

    def test_crosstalk_compensation_target_fluxes_fallback_to_voltage(
        self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus
    ):
        """When no target flux is given, the compiler recovers the parked flux from the hardware
        bias voltage (qdac_offsets) via the linear inversion (original behaviour)."""
        crosstalk = CrosstalkMatrix.from_array(["flux1", "flux2"], np.linalg.inv([[1, 0.5], [0.5, 1]]))
        # flux2 parked at 0.1 -> its bias voltage; qdac_offsets is ordered like qdac_buses [flux1, flux2]
        bias = crosstalk.flux_to_bias({"flux1": 0.0, "flux2": 0.1})
        qdac_offsets = [float(bias["flux1"]), float(bias["flux2"])]

        ramp = np.array([0.0, 0.1, 0.2, 0.3, 0.2, 0.1, 0.0])
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=Arbitrary(ramp), dwell=2)  # swept bus
        qp.qdac.set_trigger(bus="flux1", duration=10e-6, outputs=[1], position="start")

        compiler = QdacCompiler()
        output = compiler.compile(
            qprogram=qp,
            qdacs=[qdac],
            qdac_buses=[flux1, flux2],
            qdac_offsets=qdac_offsets,
            crosstalk=crosstalk,
        )  # no target_fluxes -> fallback to voltage recovery

        plays = _collect_plays(output.qprogram.body)
        got2 = np.asarray(plays["flux2"].waveform.envelope(), dtype=float)
        for i, v in enumerate(ramp):
            ref = crosstalk.flux_to_bias({"flux1": float(v), "flux2": 0.1})  # flux2 recovered as 0.1 from its bias
            assert got2[i] == pytest.approx(float(ref["flux2"]), rel=1e-9, abs=1e-12)

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
        qp.qdac.set_trigger(bus="flux1", duration=10e-6, outputs=[1], position="start")

        compiler = QdacCompiler()

        with pytest.raises(
            ValueError,
            match="QProgram.play elements must have the same size.",
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

    def test_disable_autosync_is_ignored(self, qdac: QDevilQDac2, flux1: Bus):
        """qp.qblox.disable_autosync only concerns the Qblox compiler."""
        qdac_bus = flux1.instruments[0]
        qp = QProgram()
        qp.qblox.disable_autosync = True
        qp.qdac.play(bus="flux1", waveform=Square(1.0, 100), dwell=2)

        QdacCompiler().compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

        assert qdac_bus.upload_voltage_list.call_count == 1

    def test_play_named_operation_in_calibration(self, calibration: Calibration, qdac: QDevilQDac2, flux1: Bus):
        qdac_bus = flux1.instruments[0]

        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform="Xpi", dwell=2)

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
        qp.qdac.play(bus="flux1", waveform="Xpi", dwell=2)

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
        qp.qdac.set_trigger(bus="flux1", duration=10e-6, outputs=[out_port], position=wrong_position)

        compiler = QdacCompiler()
        with pytest.raises(
            NotImplementedError,
            match=f"position must be set as 'end', 'start', 'step' or 'end_step'. {wrong_position} is not recognized",
        ):
            compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

    def test_play_operation_with_variable_in_waveform_raises_error(self, qdac: QDevilQDac2, flux1: Bus):
        """A variable in a waveform fails validation (it used to only log an error)."""
        qp = QProgram()
        amplitude = qp.variable("amplitude")
        qp.qdac.play(bus="flux1", waveform=Square(amplitude, 100), dwell=2)

        compiler = QdacCompiler()
        with pytest.raises(ValidationError, match=re.escape("qililab.variable-in-waveform")):
            compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

    @pytest.mark.parametrize("loop", ["average", "sweep", "for_loop", "parallel", "infinite_loop"])
    def test_qdac_operation_inside_loop_raises_error(self, qdac: QDevilQDac2, flux1: Bus, loop: str):
        """QDAC operations run on the PC before the run, so one inside a (real-time) loop fails validation. Their
        repetitions are no longer derived from the loops they are in: pass `repetitions` instead."""
        qp = QProgram()
        x = qp.variable("x")
        y = qp.variable("y")
        contexts = {
            "average": lambda: qp.average(5),
            "sweep": lambda: qp.sweep(x).from_range(0, 10, 1),
            "for_loop": lambda: qp.for_loop(x, 0, 0.1, 0.011),
            "parallel": lambda: qp.sweep(x).from_range(0, 1, 1) | qp.sweep(y).from_range(0, 1, 1),
            "infinite_loop": qp.infinite_loop,
        }
        with pytest.warns(FutureWarning) if loop == "for_loop" else contextlib.nullcontext():
            with contexts[loop]():
                qp.qdac.play(bus="flux1", waveform=Square(1.0, 100), dwell=2)

        compiler = QdacCompiler()
        with pytest.raises(ValidationError, match="empty-domain"):
            compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

    def test_for_loops_with_no_iterations_raises_error(self):
        """A loop with a zero step raises when it is built."""
        qp = QProgram()
        loop_variable = qp.variable("test")
        with pytest.raises(ValidationError, match="Range step must be non-zero"):
            with pytest.warns(FutureWarning):
                qp.for_loop(loop_variable, 0, 10, 0)

    def test_play_wait_trigger(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """Test play + wait_trigger on an external port on the QDACII."""
        qdac_bus = flux1.instruments[0]

        pulse_wf = Square(1.0, 100)
        dwell_us = 2
        in_port = 1

        # Setting wait trigger at external
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.play(bus="flux2", waveform=pulse_wf, dwell=dwell_us)
        qp.qdac.wait_trigger(bus="flux1", port=in_port)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

        assert isinstance(output, QdacCompilationOutput)
        assert compiler._qdacs == [qdac]
        assert compiler._trigger_position == "back"

        qdac_bus.set_in_external_trigger.assert_called_once()
        assert qdac_bus.upload_voltage_list.call_count == 2


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

    def test_conditional_qdac_op_inside_if_trigger_raises_error(self, qdac: QDevilQDac2, flux1: Bus):
        """A QDAC-bus operation cannot be placed inside qp.if_trigger(): QDAC generates the external trigger
        and has no way to conditionally gate on whether that same trigger was received on the Qblox side. It
        now fails validation, as a QDAC operation inside any real-time block does."""
        qp = QProgram()
        with qp.if_trigger(expected_wait_time_ns=1000):
            qp.qdac.play(bus="flux1", waveform=Square(1.0, 100))

        compiler = QdacCompiler()
        with pytest.raises(ValidationError, match=re.escape("empty-domain: Block 'IfTrigger' has no executable domain")):
            compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

    def test_bare_sync_inside_if_trigger_is_allowed(self, qdac: QDevilQDac2, flux1: Bus):
        """A qp.sync() without buses inside qp.if_trigger() doesn't target any QDAC bus, so it must not raise."""
        qdac_bus = flux1.instruments[0]

        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=Square(1.0, 100), dwell=2)
        with qp.if_trigger(expected_wait_time_ns=1000):
            qp.qblox.acquire(bus="readout", weights=IQPair(I=Square(1.0, 100), Q=Square(0.0, 100)))
            qp.sync()

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
            NotImplementedError, match=re.escape("<class 'qprogram.operations.sync.Sync'> is not supported in QDACII.")
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
            NotImplementedError, match=re.escape("<class 'qprogram.operations.sync.Sync'> is not supported in QDACII.")
        ):
            compiler.compile(
                qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0], crosstalk=crosstalk
            )

    @pytest.mark.parametrize(
        "position, outputs, method, kwargs, trigger_position",
        [
            ("start", 1, "set_start_marker_external_trigger", {"out_port": 1, "trigger": "trigger_flux1_1_start", "width_s": 10e-6}, "front"),
            ("end", 1, "set_end_marker_external_trigger", {"out_port": 1, "trigger": "trigger_flux1_1_end", "width_s": 10e-6}, "front"),
            ("step", 1, "set_start_marker_external_trigger", {"out_port": 1, "trigger": "trigger_flux1_1_step", "width_s": 10e-6, "step": True}, "front"),
            ("end_step", 1, "set_end_marker_external_trigger", {"out_port": 1, "trigger": "trigger_flux1_1_end_step", "width_s": 10e-6, "step": True}, "front"),
        ],
    )
    def test_play_and_set_trigger_call_arguments(
        self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus, position, outputs, method, kwargs, trigger_position
    ):
        """The arguments of the voltage lists and of the trigger set-up, for every set_trigger position."""
        qdac_bus = flux1.instruments[0]
        pulse_wf = Square(1.0, 100)
        ramp_wf = Arbitrary(samples=np.array([0.0, 0.1, 0.2, 0.3, 0.2, 0.1, 0.0]))
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=2)
        qp.qdac.play(bus="flux2", waveform=ramp_wf, dwell=4, delay=1e-6, stepped=True)
        qp.qdac.set_trigger(bus="flux1", duration=10e-6, outputs=[] if outputs is None else [outputs], position=position)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

        assert output.trigger_position == trigger_position
        assert qdac_bus.upload_voltage_list.call_args_list == [
            call(waveform=pulse_wf, channel_id=1, dwell_us=2, sync_delay_s=0, repetitions=1, stepped=False),
            call(waveform=ramp_wf, channel_id=2, dwell_us=4, sync_delay_s=1e-6, repetitions=1, stepped=True),
        ]
        getattr(qdac_bus, method).assert_called_once_with(channel_id=1, **kwargs)

    def test_set_trigger_without_outputs_raises_error(self, qdac: QDevilQDac2, flux1: Bus):
        """The QDAC's internal triggers are not set up any more: a set_trigger needs outputs."""
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=Square(1.0, 100), dwell=2)
        qp.qdac.set_trigger(bus="flux1", duration=10e-6, position="start")

        compiler = QdacCompiler()
        with pytest.raises(ValidationError, match="qdac.empty-trigger-outputs"):
            compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

    def test_set_offset_and_wait_trigger_call_arguments(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """The voltage set by set_offset, and wait_trigger on an external port."""
        qdac_bus = flux1.instruments[0]
        pulse_wf = Square(1.0, 100)
        qp = QProgram()
        qp.qdac.set_offset(bus="flux2", offset=0.3)
        qp.qdac.play(bus="flux1", waveform=pulse_wf, dwell=2)
        qp.qdac.wait_trigger(bus="flux1", port=1)

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0])

        assert output.trigger_position == "back"
        qdac_bus.set_parameter.assert_called_once_with(parameter=Parameter.VOLTAGE, value=0.3, channel_id=2)
        qdac_bus.set_in_external_trigger.assert_called_once_with(channel_id=1, in_port=1)


    def test_crosstalk_compensation_voltages(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """The compensated voltage lists, and which matrix is used: an explicit one, the calibration's DC matrix,
        an explicit one over the calibration's, and none for a calibration with only an AC matrix."""
        qdac_bus = flux1.instruments[0]
        flux_wf = Arbitrary(samples=np.array([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.4, 0.3, 0.2, 0.1, 0]))
        crosstalk = CrosstalkMatrix.from_buses(
            buses={"flux1": {"flux1": 1.0, "flux2": 0.5}, "flux2": {"flux1": 0.1, "flux2": 1.0}}
        )
        other_crosstalk = CrosstalkMatrix.from_buses(
            buses={"flux1": {"flux1": 1.0, "flux2": -0.3}, "flux2": {"flux1": 0.2, "flux2": 1.0}}
        )
        dc_calibration = Calibration()
        dc_calibration.crosstalk_matrix = crosstalk
        ac_calibration = Calibration()
        ac_calibration.crosstalk_matrix_ac = crosstalk

        def compile_program(**kwargs) -> list[np.ndarray]:
            qp = QProgram()
            qp.qdac.set_offset(bus="flux2", offset=0.3)
            qp.qdac.play(bus="flux1", waveform=flux_wf, dwell=2, repetitions=121)
            qp.qdac.set_offset(bus="flux2", offset=-0.2)
            qp.qdac.set_trigger(bus="flux1", duration=10e-6, outputs=[1], position="start")

            qdac_bus.upload_voltage_list.reset_mock()
            qdac_bus.set_parameter.reset_mock()
            QdacCompiler().compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0], **kwargs)
            return [upload.kwargs["waveform"].envelope() for upload in qdac_bus.upload_voltage_list.call_args_list]

        compensated_flux1 = [
            0.10526315789473684, 0.21052631578947367, 0.3157894736842105, 0.42105263157894735, 0.5263157894736842,
            0.631578947368421, 0.5263157894736842, 0.42105263157894735, 0.3157894736842105, 0.21052631578947367,
            0.10526315789473684,
        ]
        compensated_flux2 = [
            -0.21052631578947367, -0.22105263157894736, -0.23157894736842105, -0.24210526315789474,
            -0.25263157894736843, -0.2631578947368421, -0.25263157894736843, -0.24210526315789474,
            -0.23157894736842105, -0.22105263157894736, -0.21052631578947367,
        ]
        uploads = [
            call(waveform=ANY, channel_id=2, dwell_us=2, sync_delay_s=0, repetitions=121, stepped=False),
            call(waveform=ANY, channel_id=1, dwell_us=2, sync_delay_s=0, repetitions=121, stepped=False),
        ]

        for kwargs in ({"crosstalk": crosstalk}, {"calibration": dc_calibration}):
            flux2_voltages, flux1_voltages = compile_program(**kwargs)
            assert qdac_bus.upload_voltage_list.call_args_list == uploads
            assert flux1_voltages == pytest.approx(compensated_flux1, rel=1e-9, abs=1e-12)
            assert flux2_voltages == pytest.approx(compensated_flux2, rel=1e-9, abs=1e-12)
            assert qdac_bus.set_parameter.call_count == 0

        flux2_voltages, flux1_voltages = compile_program(calibration=dc_calibration, crosstalk=other_crosstalk)
        assert qdac_bus.upload_voltage_list.call_args_list == uploads
        assert flux1_voltages == pytest.approx(
            [
                -0.05660377358490565, 0.03773584905660379, 0.13207547169811323, 0.22641509433962265,
                0.3207547169811321, 0.41509433962264153, 0.3207547169811321, 0.22641509433962265,
                0.13207547169811323, 0.03773584905660379, -0.05660377358490565,
            ],
            rel=1e-9,
            abs=1e-12,
        )
        assert flux2_voltages == pytest.approx(
            [
                -0.18867924528301885, -0.20754716981132074, -0.22641509433962262, -0.2452830188679245,
                -0.2641509433962264, -0.2830188679245283, -0.2641509433962264, -0.2452830188679245,
                -0.22641509433962262, -0.20754716981132074, -0.18867924528301885,
            ],
            rel=1e-9,
            abs=1e-12,
        )

        (flux1_voltages,) = compile_program(calibration=ac_calibration)
        assert qdac_bus.upload_voltage_list.call_args_list == [uploads[1]]
        assert flux1_voltages == pytest.approx(flux_wf.envelope(), rel=1e-9, abs=1e-12)
        assert qdac_bus.set_parameter.call_args_list == [
            call(parameter=Parameter.VOLTAGE, value=0.3, channel_id=2),
            call(parameter=Parameter.VOLTAGE, value=-0.2, channel_id=2),
        ]

    def test_play_bus_mapping_and_calibration_call_arguments(self, calibration: Calibration, qdac: QDevilQDac2, flux1: Bus):
        """A named waveform resolved through a bus mapping and then a calibration."""
        qdac_bus = flux1.instruments[0]
        qp = QProgram()
        qp.qdac.play(bus="flux", waveform="Xpi", dwell=2, repetitions=5)

        compiler = QdacCompiler()
        compiler.compile(
            qprogram=qp,
            qdacs=[qdac],
            qdac_buses=[flux1],
            qdac_offsets=[0],
            bus_mapping={"flux": "flux1"},
            calibration=calibration,
        )

        qdac_bus.upload_voltage_list.assert_called_once_with(
            waveform=ANY, channel_id=1, dwell_us=2, sync_delay_s=0, repetitions=5, stepped=False
        )
        np.testing.assert_array_equal(
            qdac_bus.upload_voltage_list.call_args.kwargs["waveform"].envelope(),
            calibration.get_waveform(bus="flux1", name="Xpi").envelope(),
        )

    def test_two_qdacs_call_arguments(
        self, qdac: QDevilQDac2, qdac_2: QDevilQDac2, flux_qdac1: Bus, flux_qdac2: Bus
    ):
        """With two QDACs, a set_trigger on a bus of the second one synthesises a constant voltage list (at the
        runcard voltage) on the trigger bus, and the output QDAC triggers the other one."""
        ramp_wf = Arbitrary(samples=np.array([0.0, 0.1, 0.2, 0.3, 0.2, 0.1, 0.0]))
        qdac.device.name = "qdac"
        qdac._cache_dc = {}

        qp = QProgram()
        qp.qdac.play(bus="flux_qdac2", waveform=ramp_wf, dwell=3, repetitions=2)
        qp.qdac.set_trigger(bus="flux_qdac2", duration=10e-6, outputs=[1], position="start")

        compiler = QdacCompiler()
        output = compiler.compile(
            qprogram=qp,
            qdacs=[qdac, qdac_2],
            qdac_buses=[flux_qdac1, flux_qdac2],
            qdac_offsets=[0, 0],
            out_instrument=qdac,
        )

        assert output.qdacs == [qdac_2, qdac]
        assert output.trigger_position == "front"
        qdac_2.upload_voltage_list.assert_called_once_with(
            waveform=ramp_wf, channel_id=1, dwell_us=3, sync_delay_s=0, repetitions=2, stepped=False
        )
        qdac.upload_voltage_list.assert_called_once_with(
            waveform=ANY, channel_id=1, dwell_us=3, sync_delay_s=0, repetitions=2, stepped=False
        )
        np.testing.assert_array_equal(qdac.upload_voltage_list.call_args.kwargs["waveform"].envelope(), np.full(7, 0.5))
        qdac.set_start_marker_external_trigger.assert_called_once_with(
            channel_id=1, out_port=1, trigger="trigger_flux_qdac2_1_start", width_s=10e-6
        )
        qdac.set_out_external_trigger.assert_called_once_with(channel_id=1, out_port=1, trigger="qdac_external_trigger")
        qdac_2.set_in_external_trigger.assert_called_once_with(channel_id=1, in_port=1)

    def test_if_trigger_program_call_arguments(self, qdac: QDevilQDac2, flux1: Bus):
        """The QDAC side of a program where the QDAC triggers a Qblox qp.if_trigger() once per voltage step."""
        qdac_bus = flux1.instruments[0]
        ramp_wf = Arbitrary(samples=np.array([0.0, 0.1, 0.2, 0.3, 0.2, 0.1, 0.0]))
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=ramp_wf, dwell=3)
        qp.qdac.set_trigger(bus="flux1", duration=100e-6, outputs=[1], position="step")
        with qp.if_trigger():
            with qp.average(shots=10):
                qp.qblox.acquire(bus="readout", weights=IQPair(I=Square(1.0, 100), Q=Square(0.0, 100)))

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

        assert output.trigger_position == "front"
        # The output QProgram only holds the QDAC operations: the Qblox acquire is left out, its blocks are kept
        assert output.qprogram.buses == {"flux1"}
        assert output.qprogram.body.elements[2].elements[0].elements == []
        qdac_bus.upload_voltage_list.assert_called_once_with(
            waveform=ramp_wf, channel_id=1, dwell_us=3, sync_delay_s=0, repetitions=1, stepped=False
        )
        qdac_bus.set_start_marker_external_trigger.assert_called_once_with(
            channel_id=1, out_port=1, trigger="trigger_flux1_1_step", width_s=100e-6, step=True
        )

    def test_loop_without_qdac_operation_does_not_multiply_the_next_qdac_play_repetitions(
        self, qdac: QDevilQDac2, flux1: Bus
    ):
        """A loop with no QDAC operation before a QDAC play no longer multiplies its repetitions: a QDAC play
        repeats `repetitions` times, 1 by default."""
        qdac_bus = flux1.instruments[0]
        ramp_wf = Arbitrary(samples=np.array([0.0, 0.1, 0.2]))
        qp = QProgram()
        with qp.average(shots=10):
            qp.qblox.acquire(bus="readout", weights=IQPair(I=Square(1.0, 100), Q=Square(0.0, 100)))
        qp.qdac.play(bus="flux1", waveform=ramp_wf, dwell=3)

        compiler = QdacCompiler()
        compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

        qdac_bus.upload_voltage_list.assert_called_once_with(
            waveform=ramp_wf, channel_id=1, dwell_us=3, sync_delay_s=0, repetitions=1, stepped=False
        )

    def test_qblox_operation_on_qdac_bus_raises_error(self, qdac: QDevilQDac2, flux1: Bus):
        """A Qblox-only operation such as qp.wait() on a QDAC bus raises an error."""
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=Square(1.0, 100), dwell=2)
        qp.wait(bus="flux1", duration=100)

        compiler = QdacCompiler()
        with pytest.raises(
            NotImplementedError, match=re.escape("<class 'qprogram.operations.wait.Wait'> is not supported in QDACII.")
        ):
            compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

    @pytest.mark.parametrize(
        "add_operation, message",
        [
            (
                lambda qp: qp.play(bus="flux1", waveform=Square(1.0, 100)),
                "<class 'qprogram.operations.play.Play'> is not supported in QDACII. Use qp.qdac.play() on a QDAC bus.",
            ),
            (
                lambda qp: qp.set_offset(bus="flux1", offset_path0=0.1),
                "<class 'qprogram.operations.set_offset.SetOffset'> is not supported in QDACII. Use qp.qdac.set_offset() "
                "on a QDAC bus.",
            ),
        ],
    )
    def test_core_play_or_set_offset_on_qdac_bus_raises_error(
        self, qdac: QDevilQDac2, flux1: Bus, add_operation, message: str
    ):
        """qp.play and qp.set_offset are Qblox operations: on a QDAC bus they raise, pointing to the QDAC ones."""
        qp = QProgram()
        add_operation(qp)

        compiler = QdacCompiler()
        with pytest.raises(NotImplementedError, match=re.escape(message)):
            compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

    def test_unmapped_named_operation_with_crosstalk_raises_error(self, qdac: QDevilQDac2, flux1: Bus, flux2: Bus):
        """With a crosstalk matrix, a named waveform missing from the calibration still raises the unmapped
        operations error."""
        crosstalk = CrosstalkMatrix.from_buses(
            buses={"flux1": {"flux1": 1.0, "flux2": 0.5}, "flux2": {"flux1": 0.1, "flux2": 1.0}}
        )
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform="Xpi", dwell=2)

        compiler = QdacCompiler()
        with pytest.raises(RuntimeError, match="contains named operations that are not mapped"):
            compiler.compile(
                qprogram=qp, qdacs=[qdac], qdac_buses=[flux1, flux2], qdac_offsets=[0, 0], crosstalk=crosstalk
            )

    def test_compile_does_not_modify_qprogram(self, qdac: QDevilQDac2, flux1: Bus):
        """The play arguments are sent to the QDAC, and the compiler works on a copy: the play operation of the
        caller's QProgram is left as it is."""
        qdac_bus = flux1.instruments[0]
        wf = Square(1.0, 100)
        qp = QProgram()
        qp.qdac.play(bus="flux1", waveform=wf, dwell=2, repetitions=4)
        play = qp.body.elements[0]

        compiler = QdacCompiler()
        output = compiler.compile(qprogram=qp, qdacs=[qdac], qdac_buses=[flux1], qdac_offsets=[0])

        qdac_bus.upload_voltage_list.assert_called_once_with(
            waveform=wf, channel_id=1, dwell_us=2, sync_delay_s=0, repetitions=4, stepped=False
        )
        assert output.qprogram.body.elements[0] is not play
        assert (play.dwell, play.delay, play.stepped, play.repetitions) == (2, 0, False, 4)
        assert type(play.delay) is int

