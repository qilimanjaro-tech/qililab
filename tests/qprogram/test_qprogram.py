import math
import re
from collections import deque

import numpy as np
import pytest
from qprogram import BinaryOp, InvalidVariableIdError, MeasurementHandle, Range, ValidationError, Values, Variable
from qprogram.blocks import Average, Block, Parallel, Sweep
from qprogram.operations import Measure, Play, ResetPhase, SetFrequency, SetGain, SetOffset, SetPhase, Sync, Wait
from qprogram_qblox import Acquire, Scope, SetMarkers
from qprogram_qblox import SetTrigger as QbloxSetTrigger
from qprogram_qblox import WaitTrigger as QbloxWaitTrigger
from qprogram_qdac import Play as QdacPlay
from qprogram_qdac import SetOffset as QdacSetOffset
from qprogram_qdac import SetTrigger as QdacSetTrigger
from qprogram_qdac import WaitTrigger as QdacWaitTrigger

import qililab as ql
from qililab import Arbitrary, Experiment, Gaussian, IQDrag, IQPair, QProgram, Square
from qililab.exceptions import VariableAllocated
from qililab.pulse_distortion import ExponentialCorrection
from qililab.qprogram.blocks import ForLoop, IfTrigger, InfiniteLoop, for_loop_iterations
from qililab.qprogram.calibration import Calibration
from qililab.qprogram.compilers.qblox_compiler import QbloxCompiler
from qililab.qprogram.crosstalk.crosstalk_matrix import CrosstalkMatrix, NonLinearCrosstalkMatrix
from qililab.qprogram.formats.legacy import qdac_operations
from qililab.qprogram.operations import DisableAutosync, MeasureReset, QbloxPlay
from qililab.qprogram.variable_ids import unique_variable_id

# The crosstalk tests below keep qp.for_loop where its step does not divide stop - start: they rely on its rounding.
ignore_for_loop_deprecation = pytest.mark.filterwarnings("ignore:qp.for_loop is deprecated:FutureWarning")

# A QProgram saved as YAML by qililab before it moved to qprogram (written by the former code).
LEGACY_QPROGRAM_YAML = """&id012 !QProgram
_block_stack: !deque
- &id009 !Block
  _uuid: !UUID {int: 339889595465859303959856124955226199094}
  elements:
  - !Play
    _uuid: !UUID {int: 234111067693401617127372325895317094101}
    bus: flux
    delay: null
    dwell: 2
    repetitions: 3
    stepped: null
    wait_time: null
    waveform: !Arbitrary
      samples: !ndarray
        data: [0.0, 0.1, 0.2]
        dtype: float64
        shape: !!python/tuple [3]
  - !SetTrigger
    _uuid: !UUID {int: 7208834455776119881674277993318678860}
    bus: flux
    duration: 1e-05
    outputs: 1
    position: step
  - !SetOffset
    _uuid: !UUID {int: 21527942768652248910942762136757958701}
    bus: drive
    offset_path0: 0.1
    offset_path1: 0.2
  - !Average
    _uuid: !UUID {int: 86816649077598598722483279882979440861}
    elements:
    - !ForLoop
      _uuid: !UUID {int: 4599912654906890836467881642333413523}
      elements:
      - !Parallel
        _uuid: !UUID {int: 295618926443859700724232070327689904312}
        elements:
        - !WaitTrigger
          _uuid: !UUID {int: 75574043758735645007126817010141435376}
          bus: readout
          duration: 4
          port: null
        - !SetGain
          _uuid: !UUID {int: 54917653930616157890077867920301724327}
          bus: drive
          gain: !FloatVariable
            _domain: &id006 !Domain Voltage-4
            _label: gain
            _uuid: &id007 !UUID {int: 75827260651747105141903344703822724480}
        - !SetFrequency
          _uuid: !UUID {int: 69850255070117816421913321241769717838}
          bus: drive
          frequency: !FloatVariable
            _domain: &id004 !Domain Frequency-2
            _label: frequency of drive
            _uuid: &id005 !UUID {int: 69423403749405325421873478219594478060}
        - !Wait
          _uuid: !UUID {int: 308272415704786942197123744374056447687}
          bus: drive
          duration: !VariableExpression
            _domain: &id001 !Domain Time-1
            _label: ''
            _uuid: !UUID {int: 207549869194234022304864097985862441770}
            components:
            - !IntVariable
              _domain: *id001
              _label: wait
              _uuid: &id002 !UUID {int: 236826777703383271129913655010863859146}
            - 4
            constant: 4
            left: !IntVariable
              _domain: *id001
              _label: wait
              _uuid: *id002
            operator: +
            right: 4
            variables:
            - !IntVariable
              _domain: *id001
              _label: wait
              _uuid: *id002
        - !Play
          _uuid: !UUID {int: 9204312563412720730661703141052569102}
          bus: drive
          delay: null
          dwell: null
          repetitions: null
          stepped: null
          wait_time: null
          waveform: &id003 !IQPair
            I: !Square {amplitude: 1.0, duration: 40}
            Q: !Square {amplitude: 0.0, duration: 40}
        - !Play
          _uuid: !UUID {int: 120696340680356569370188106051882665699}
          bus: drive
          delay: null
          dwell: null
          repetitions: null
          stepped: null
          wait_time: 8
          waveform: *id003
        - !Sync
          _uuid: !UUID {int: 88017987221282795589294105038810683209}
          buses: [drive, readout]
        - !Measure
          _uuid: !UUID {int: 133719575796880086393340760501469889067}
          bus: readout
          demodulation: true
          rotation: null
          save_adc: true
          waveform: *id003
          weights: &id008 !IQPair
            I: !Square {amplitude: 1.0, duration: 400}
            Q: !Square {amplitude: 1.0, duration: 400}
        - !AcquireWithCalibratedWeights
          _uuid: !UUID {int: 2733370339320372336105920436696378062}
          bus: readout
          save_adc: false
          weights: weights_name
        - !SetMarkers
          _uuid: !UUID {int: 239401395950024634251697346873818450508}
          bus: drive
          mask: '0001'
        - !ResetPhase
          _uuid: !UUID {int: 6605939274646573725447562881022676315}
          bus: drive
        - !SetPhase
          _uuid: !UUID {int: 319134433418095013797310836792266048248}
          bus: drive
          phase: 0.5
        loops:
        - !ForLoop
          _uuid: !UUID {int: 124241138431343579745983217878836863593}
          elements: []
          start: 1000000.0
          step: 1000000.0
          stop: 3000000.0
          variable: !FloatVariable
            _domain: *id004
            _label: frequency of drive
            _uuid: *id005
        - !ForLoop
          _uuid: !UUID {int: 79224065027989522975406109353124912356}
          elements: []
          start: 100
          step: 100
          stop: 300
          variable: !IntVariable
            _domain: *id001
            _label: wait
            _uuid: *id002
      start: 0.0
      step: 0.5
      stop: 1.0
      variable: !FloatVariable
        _domain: *id006
        _label: gain
        _uuid: *id007
    - !Loop
      _uuid: !UUID {int: 232208703777656257521868413772224116472}
      elements:
      - !PlayWithCalibratedWaveform
        _uuid: !UUID {int: 3784355382759441876922214775401992634}
        bus: drive
        delay: null
        dwell: null
        repetitions: null
        stepped: null
        wait_time: null
        waveform: pi
      values: !ndarray
        data: [1, 2, 3]
        dtype: int64
        shape: !!python/tuple [3]
      variable: !IntVariable
        _domain: &id010 !Domain Scalar-0
        _label: index
        _uuid: &id011 !UUID {int: 115090632961437209829188123929329059010}
    shots: 100
  - !MeasureReset
    _uuid: !UUID {int: 329744893229747572315641025991279536223}
    bus: readout
    control_bus: drive
    reset_pulse: *id003
    save_adc: false
    trigger_address: 2
    waveform: *id003
    weights: *id008
_body: *id009
_buses: !!set {drive: null, flux: null, readout: null}
_trigger_mode: measure_reset
_variables:
  ? !FloatVariable
    _domain: *id006
    _label: gain
    _uuid: *id007
  : !VariableInfo {allocated_by: null, is_allocated: false}
  ? !FloatVariable
    _domain: *id004
    _label: frequency of drive
    _uuid: *id005
  : !VariableInfo {allocated_by: null, is_allocated: false}
  ? !IntVariable
    _domain: *id001
    _label: wait
    _uuid: *id002
  : !VariableInfo {allocated_by: null, is_allocated: false}
  ? !IntVariable
    _domain: *id010
    _label: index
    _uuid: *id011
  : !VariableInfo {allocated_by: null, is_allocated: false}
qblox: !_QbloxInterface
  _weight_duration:
    readout: [400, weights_name, 400]
  disable_autosync: true
  qprogram: *id012
qdac: !_QdacInterface
  qprogram: *id012
quantum_machines: !_QuantumMachinesInterface
  qprogram: *id012
"""

# The same program, read through ql.deserialize and written as .qp.
LEGACY_QPROGRAM_QP = """#!QProgram 0.3

require qblox 0.2
require qdac 0.2
require qililab 0.1

body:
  var gain label="gain"
  var frequency_of_drive label="frequency of drive"
  var wait label="wait"
  var index label="index"

  qililab.disable_autosync
  qdac.play "flux" Arbitrary(samples=[0.0, 0.1, 0.2]) dwell=2 repetitions=3
  qdac.set_trigger "flux" 1e-05 position="step" outputs=[1]
  set_offset "drive" 0.1 offset_path1=0.2
  average 100:
    for gain in Range(start=0.0, stop=1.0, step=0.5):
      for frequency_of_drive in Range(start=1000000.0, stop=3000000.0, step=1000000.0) | for wait in Range(start=100.0, stop=300.0, step=100.0):
        qblox.wait_trigger "readout" 4
        set_gain "drive" gain
        set_frequency "drive" frequency_of_drive
        wait "drive" (wait + 4)
        play "drive" IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        qililab.qblox_play "drive" IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40)) 8
        sync "drive" "readout"
        measure "readout" IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40)) IQPair(I=Square(amplitude=1.0, duration=400), Q=Square(amplitude=1.0, duration=400)) name="m0"
        qblox.acquire "readout" "weights_name" name="m1"
        qblox.set_markers "drive" "0001"
        reset_phase "drive"
        set_phase "drive" 0.5
    for index in [1.0, 2.0, 3.0]:
      play "drive" "pi"
  qililab.measure_reset "readout" IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40)) IQPair(I=Square(amplitude=1.0, duration=400), Q=Square(amplitude=1.0, duration=400)) "drive" IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40)) name="m2" trigger_address=2
"""

# A QProgram with an infinite loop and an if_trigger, saved as YAML by the former code.
LEGACY_IF_TRIGGER_YAML = """&id002 !QProgram
_block_stack: !deque
- &id001 !Block
  _uuid: !UUID {int: 249934206781270308625068218294771357272}
  elements:
  - !InfiniteLoop
    _uuid: !UUID {int: 117695191550470694566691638871972241603}
    elements:
    - !Conditional
      _uuid: !UUID {int: 85439863952484290965676806837739158359}
      elements:
      - !Play
        _uuid: !UUID {int: 134614337120317825448900723091501563122}
        bus: readout
        delay: null
        dwell: null
        repetitions: null
        stepped: null
        wait_time: null
        waveform: !IQPair
          I: !Square {amplitude: 1.0, duration: 40}
          Q: !Square {amplitude: 0.0, duration: 40}
      expected_wait_time_ns: 10000
      trigger_padding_ns: null
_body: *id001
_buses: !!set {readout: null}
_trigger_mode: if_trigger
_variables: {}
qblox: !_QbloxInterface
  _weight_duration: {}
  disable_autosync: false
  qprogram: *id002
qdac: !_QdacInterface
  qprogram: *id002
quantum_machines: !_QuantumMachinesInterface
  qprogram: *id002
"""


def load_legacy_qprogram() -> QProgram:
    """Read LEGACY_QPROGRAM_YAML, which warns about its measurement with save_adc=True."""
    with pytest.warns(UserWarning, match="had save_adc=True, which no longer exists"):
        return ql.deserialize(LEGACY_QPROGRAM_YAML)


class TestQProgram:
    """Unit tests checking the QProgram attributes and methods"""

    def test_init(self):
        """Test init method"""
        qp = QProgram()
        assert isinstance(qp._body, Block)
        assert len(qp._body.elements) == 0
        assert isinstance(qp._block_stack, deque)
        assert len(qp._block_stack) == 1
        assert qp.variables == []

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
        assert qp._active_block is qp._body

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

    def test_variable_method(self):
        """Variables are named by an id, unique per program, and compare by id."""
        qp = QProgram()
        frequency = qp.variable("frequency", label="Frequency (Hz)")

        assert isinstance(frequency, Variable)
        assert frequency.id == "frequency"
        assert frequency.label == "Frequency (Hz)"
        assert qp.variables == [frequency]
        assert frequency == Variable("frequency")

    @pytest.mark.parametrize("variable_id", ["1abc", "Frequency (Hz)", "for", "var", "in", "if"])
    def test_variable_with_invalid_id_raises_error(self, variable_id):
        """A variable id must match [A-Za-z_][A-Za-z0-9_]* and cannot be a reserved word: use the label instead."""
        qp = QProgram()
        with pytest.raises(InvalidVariableIdError):
            qp.variable(variable_id)

    @pytest.mark.parametrize(
        ("text", "taken", "expected"),
        [
            ("frequency of drive", set(), "frequency_of_drive"),
            ("1abc", set(), "_1abc"),
            ("fréquence", set(), "fr_quence"),
            ("", set(), "variable"),
            ("for", set(), "for_2"),
            ("wait", {"wait", "wait_2"}, "wait_3"),
        ],
    )
    def test_unique_variable_id(self, text, taken, expected):
        """Any text gives a variable id qprogram accepts, with ``_2``, ``_3``, ... appended until it is free."""
        variable_id = unique_variable_id(text, taken)

        assert variable_id == expected
        assert QProgram().variable(variable_id).id == expected

    def test_variable_declared_twice_raises_error(self):
        qp = QProgram()
        qp.variable("gain")
        with pytest.raises(ValidationError, match="Variable 'gain' is already declared on this QProgram"):
            qp.variable("gain")

    def test_sweep_method(self):
        """Test sweep method, which replaces for_loop"""
        qp = QProgram()
        variable = qp.variable("int_scalar")
        with qp.sweep(variable).from_range(0, 100, 5) as loop:
            # __enter__
            assert isinstance(loop, Sweep)
            assert loop.variable == variable
            assert isinstance(loop.source, Range)
            assert (loop.source.start, loop.source.stop, loop.source.step) == (0, 100, 5)
            assert loop.num_iterations() == 21
            assert qp._active_block is loop
        # __exit__
        assert len(qp._body.elements) == 1
        assert qp._body.elements[0] is loop
        assert qp._active_block is qp._body

    def test_for_loop_method_is_deprecated_alias_of_sweep(self):
        """qp.for_loop warns and opens a sweep over the same points."""
        qp = QProgram()
        variable = qp.variable("int_scalar")
        with pytest.warns(FutureWarning, match="qp.for_loop is deprecated"):
            context = qp.for_loop(variable=variable, start=0, stop=100, step=5)
        with context as loop:
            assert isinstance(loop, Sweep)
            assert qp._active_block is loop
        assert loop.variable == variable
        assert (loop.source.start, loop.source.stop, loop.source.step) == (0, 100, 5)
        np.testing.assert_allclose(loop.source.values(), np.arange(0, 101, 5))
        assert qp._body.elements[0] is loop
        assert qp._active_block is qp._body

    @pytest.mark.parametrize("start, stop, step", [(0.0, 1.0, 0.3), (1.0, 0.0, -0.3), (0, 0.1, 0.08), (1, 2.05, 0.1)])
    def test_for_loop_with_step_not_dividing_range_keeps_point_count(self, start, stop, step):
        """qp.for_loop keeps its point count, rounded down, spread from start to stop."""
        qp = QProgram()
        variable = qp.variable("x")
        with pytest.warns(FutureWarning, match="qp.for_loop is deprecated"):
            with qp.for_loop(variable=variable, start=start, stop=stop, step=step) as loop:
                pass

        points = for_loop_iterations(start, stop, step)
        assert loop.num_iterations() == points
        np.testing.assert_allclose(loop.source.values(), np.linspace(start, stop, points))

    def test_for_loop_with_step_pointing_away_from_stop_raises_error(self):
        qp = QProgram()
        variable = qp.variable("x")
        with pytest.warns(FutureWarning), pytest.raises(ValidationError, match="moves away from stop"):
            qp.for_loop(variable=variable, start=0, stop=1, step=-2)

    def test_parallel_method(self):
        """Sweeps combined with | run in lockstep, in a Parallel block."""
        qp = QProgram()
        var1 = qp.variable("int_scalar")
        var2 = qp.variable("float_scalar")
        with qp.sweep(var1).from_range(0, 10, 1) | qp.sweep(var2).from_range(0.0, 1.0, 0.1) as loop:
            # __enter__
            assert isinstance(loop, Parallel)
            assert len(loop.loops) == 2
            assert all(isinstance(sweep, Sweep) for sweep in loop.loops)
            assert [sweep.variable for sweep in loop.loops] == [var1, var2]
            assert qp._active_block is loop
        # __exit__
        assert len(qp._body.elements) == 1
        assert qp._body.elements[0] is loop
        assert qp._active_block is qp._body

    def test_parallel_alias_is_removed(self):
        """qp.parallel(loops=[...]) is gone: sweeps combined with | run in lockstep instead."""
        assert not hasattr(QProgram(), "parallel")
        assert not hasattr(Experiment(label="experiment"), "parallel")

    def test_loop_over_a_variable_an_enclosing_loop_sweeps_raises_error(self):
        """Sweeping a variable an enclosing loop already sweeps raises VariableAllocated when the inner loop opens."""

        def nested(outer_parallel: bool, inner_parallel: bool) -> QProgram:
            qp = QProgram()
            variable = qp.variable("x")
            other = qp.variable("y")

            def loop(parallel: bool, start: int):
                sweep = qp.sweep(variable).from_range(start, start + 10, 1)
                return sweep | qp.sweep(other).from_range(start, start + 10, 1) if parallel else sweep

            with loop(outer_parallel, 0):
                with loop(inner_parallel, 100):
                    qp.wait(bus="drive", duration=100)
            return qp

        for outer_parallel, inner_parallel in [(False, False), (False, True), (True, False), (True, True)]:
            with pytest.raises(VariableAllocated):
                nested(outer_parallel, inner_parallel)

    def test_str_returns_qp_text(self):
        """str(qp) is the program written as .qp text."""
        qp = QProgram()
        gain = qp.variable("gain", label="Gain")
        readout = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        with qp.average(10):
            with qp.sweep(gain).from_range(0.0, 1.0, 0.5):
                qp.set_gain(bus="drive", gain=gain)
                qp.measure(bus="readout", waveform=readout, weights=readout)

        assert str(qp) == (
            "#!QProgram 0.3\n"
            "\n"
            "body:\n"
            '  var gain label="Gain"\n'
            "\n"
            "  average 10:\n"
            "    for gain in Range(start=0.0, stop=1.0, step=0.5):\n"
            '      set_gain "drive" gain\n'
            '      measure "readout" IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))'
            ' IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40)) name="m0"\n'
        )

    def test_from_qp_round_trip(self):
        """QProgram.from_qp reads back str(qp), qililab's operations and blocks included, as a qililab QProgram."""
        readout = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        qp = QProgram()
        gain = qp.variable("gain", label="Gain")
        wait = qp.variable("wait")
        qp.qdac.play(bus="flux", waveform=Arbitrary(np.array([0.0, 0.1, 0.2])), dwell=2, repetitions=3)
        qp.qdac.set_trigger(bus="flux", duration=10e-6, position="step", outputs=[1])
        with qp.average(10):
            with qp.sweep(gain).from_range(0.0, 1.0, 0.5) | qp.sweep(wait).from_range(100, 300, 100):
                qp.set_gain(bus="drive", gain=gain)
                qp.wait(bus="drive", duration=wait + 4)
                qp.qblox.play(bus="drive", waveform="xgate", wait_time=8)
                qp.sync(buses=["drive", "readout"])
                qp.measure(bus="readout", waveform=readout, weights=readout)
                qp.qblox.acquire(bus="readout", weights="weights", name="acquisition")
                qp.qblox.measure_reset(
                    bus="readout",
                    waveform=readout,
                    weights=readout,
                    control_bus="drive",
                    reset_pulse=readout,
                    trigger_address=2,
                )
                qp.qblox.set_markers(bus="drive", mask="0001")
        with qp.infinite_loop():
            qp.qblox.wait_trigger(bus="readout", duration=4)

        text = str(qp)
        loaded = QProgram.from_qp(text)

        assert isinstance(loaded, QProgram)
        assert loaded.body == qp.body
        assert str(loaded) == text
        assert loaded.variables == [gain, wait]
        assert [handle.name for handle in loaded.measurement_handles()] == ["m0", "acquisition", "m1"]
        assert loaded.qblox.weight_duration == {"readout": [40, "weights", 40]}

    def test_disable_autosync_is_part_of_the_program(self):
        """qp.qblox.disable_autosync is a DisableAutosync at the top of the body, so copies and .qp files keep it."""
        qp = QProgram()
        qp.wait(bus="drive", duration=100)
        qp.qblox.disable_autosync = True
        qp.qblox.disable_autosync = True

        assert str(qp) == (
            '#!QProgram 0.3\n\nrequire qililab 0.1\n\nbody:\n  qililab.disable_autosync\n  wait "drive" 100\n'
        )
        assert QProgram.from_qp(str(qp)).qblox.disable_autosync is True
        assert qp.with_bus_mapping(bus_mapping={"drive": "drive_q0"}).qblox.disable_autosync is True

        qp.qblox.disable_autosync = False

        assert qp.qblox.disable_autosync is False
        assert qp.body.elements == [Wait(bus="drive", duration=100)]

    def test_insert_block_leaves_out_disable_autosync(self):
        """The setting belongs to the program it was set on, not to the programs its body is inserted in."""
        other = QProgram()
        other.qblox.disable_autosync = True
        other.wait(bus="drive", duration=100)

        qp = QProgram()
        with qp.average(10):
            qp.insert_block(other.body)

        assert qp.qblox.disable_autosync is False
        (average,) = qp.body.elements
        assert average.elements == [Wait(bus="drive", duration=100)]

    def test_from_qp_round_trip_keeps_if_trigger_parameters(self):
        qp = QProgram()
        with qp.if_trigger(trigger_padding_ns=300, expected_wait_time_ns=2252):
            qp.wait(bus="readout", duration=100)

        loaded = QProgram.from_qp(str(qp))

        if_trigger = loaded.body.elements[0]
        assert isinstance(if_trigger, IfTrigger)
        assert if_trigger.trigger_padding_ns == 300
        assert if_trigger.expected_wait_time_ns == 2252

    def test_deserialize_legacy_yaml_qprogram(self):
        """A QProgram saved as YAML by the former code loads into the qprogram nodes doing the same thing."""
        qp = load_legacy_qprogram()

        assert isinstance(qp, QProgram)
        assert str(qp) == LEGACY_QPROGRAM_QP
        assert [(variable.id, variable.label) for variable in qp.variables] == [
            ("gain", "gain"),
            ("frequency_of_drive", "frequency of drive"),
            ("wait", "wait"),
            ("index", "index"),
        ]
        assert qp.buses == {"flux", "drive", "readout"}
        assert qp.qblox.disable_autosync is True
        assert qp.qblox.weight_duration == {"readout": [400, "weights_name", 400]}
        assert qp.has_calibrated_waveforms_or_weights() is True

        disable_autosync, qdac_play, qdac_set_trigger, set_offset, average, measure_reset = qp.body.elements
        assert isinstance(disable_autosync, DisableAutosync)
        assert isinstance(qdac_play, QdacPlay)
        assert (qdac_play.dwell, qdac_play.repetitions) == (2, 3)
        assert isinstance(qdac_set_trigger, QdacSetTrigger)
        assert (qdac_set_trigger.duration, qdac_set_trigger.position, qdac_set_trigger.outputs) == (1e-05, "step", (1,))
        assert isinstance(set_offset, SetOffset)
        assert isinstance(average, Average)
        assert average.shots == 100
        assert isinstance(measure_reset, MeasureReset)
        assert (measure_reset.control_bus, measure_reset.trigger_address) == ("drive", 2)

        gain_loop, index_loop = average.elements
        assert isinstance(gain_loop, Sweep)
        assert (gain_loop.source.start, gain_loop.source.stop, gain_loop.source.step) == (0.0, 1.0, 0.5)
        (parallel,) = gain_loop.elements
        assert isinstance(parallel, Parallel)
        assert [loop.num_iterations() for loop in parallel.loops] == [3, 3]
        assert [type(element) for element in parallel.elements] == [
            QbloxWaitTrigger,
            SetGain,
            SetFrequency,
            Wait,
            Play,
            QbloxPlay,
            Sync,
            Measure,
            Acquire,
            SetMarkers,
            ResetPhase,
            SetPhase,
        ]
        wait = parallel.elements[3]
        assert isinstance(wait.duration, BinaryOp)
        assert parallel.elements[5].wait_time == 8
        assert parallel.elements[6].targets == ["drive", "readout"]
        assert isinstance(index_loop, Sweep)
        assert isinstance(index_loop.source, Values)
        np.testing.assert_array_equal(index_loop.source.values(), [1, 2, 3])
        (calibrated_play,) = index_loop.elements
        assert isinstance(calibrated_play, Play)
        assert calibrated_play.waveform == "pi"

    def test_deserialize_legacy_yaml_qprogram_with_two_variables_sharing_a_label(self):
        """Former variables were told apart by UUID, so two could share a label: the second one gets ``_2``."""
        with pytest.warns(UserWarning, match="had save_adc=True, which no longer exists"):
            qp = ql.deserialize(LEGACY_QPROGRAM_YAML.replace("_label: index", "_label: wait"))

        assert [(variable.id, variable.label) for variable in qp.variables] == [
            ("gain", "gain"),
            ("frequency_of_drive", "frequency of drive"),
            ("wait", "wait"),
            ("wait_2", "wait"),
        ]
        assert "for wait_2 in [1.0, 2.0, 3.0]:" in str(qp)

    def test_deserialize_legacy_yaml_qprogram_twice_keeps_the_variables_of_each_file(self):
        """Two files sharing variable UUIDs, such as two saves of one program, each get the variables they hold."""
        with pytest.warns(UserWarning, match="had save_adc=True, which no longer exists"):
            relabelled = ql.deserialize(LEGACY_QPROGRAM_YAML.replace("_label: index", "_label: wait"))
        original = load_legacy_qprogram()

        assert [variable.id for variable in relabelled.variables] == ["gain", "frequency_of_drive", "wait", "wait_2"]
        assert [variable.id for variable in original.variables] == ["gain", "frequency_of_drive", "wait", "index"]
        assert not set(map(id, relabelled.variables)) & set(map(id, original.variables))

    def test_deserialize_legacy_yaml_qprogram_with_if_trigger(self):
        """The former Conditional becomes an IfTrigger with the same parameters, the InfiniteLoop qililab's."""
        qp = ql.deserialize(LEGACY_IF_TRIGGER_YAML)

        assert isinstance(qp, QProgram)
        (infinite_loop,) = qp.body.elements
        assert isinstance(infinite_loop, InfiniteLoop)
        (if_trigger,) = infinite_loop.elements
        assert isinstance(if_trigger, IfTrigger)
        assert if_trigger.expected_wait_time_ns == 10000
        assert if_trigger.trigger_padding_ns is None
        (play,) = if_trigger.elements
        assert isinstance(play, Play)
        assert play.bus == "readout"
        assert qp.qblox.disable_autosync is False

    def test_qdac_operations_converts_legacy_operations_on_qdac_buses(self):
        """The former play, set_offset, set_trigger and wait_trigger did not say they were for the QDAC:
        qdac_operations makes them QDAC ones on the QDAC buses, and leaves the program it is given unchanged."""
        qp = QProgram()
        qp.play(bus="flux", waveform=IQPair(I=Square(amplitude=0.5, duration=10), Q=Square(amplitude=0.0, duration=10)))
        qp.set_offset(bus="flux", offset_path0=0.3)
        qp.qblox.set_trigger(bus="flux", duration=100, outputs=1, position="start")
        qp.qblox.wait_trigger(bus="flux", duration=4, port=2)
        qp.play(bus="drive", waveform=Square(amplitude=1.0, duration=10))

        converted = qdac_operations(qp, {"flux"})

        play, set_offset, set_trigger, wait_trigger, drive_play = converted.body.elements
        assert isinstance(play, QdacPlay)
        assert play.waveform == Square(amplitude=0.5, duration=10)
        assert isinstance(set_offset, QdacSetOffset)
        assert set_offset.offset == 0.3
        assert isinstance(set_trigger, QdacSetTrigger)
        assert (set_trigger.duration, set_trigger.position, set_trigger.outputs) == (100, "start", (1,))
        assert isinstance(wait_trigger, QdacWaitTrigger)
        assert wait_trigger.port == 2
        assert type(drive_play) is Play
        assert [type(element) for element in qp.body.elements] == [
            Play,
            SetOffset,
            QbloxSetTrigger,
            QbloxWaitTrigger,
            Play,
        ]

    def test_qdac_operations_wait_trigger_without_port_raises_error(self):
        qp = QProgram()
        qp.qblox.wait_trigger(bus="flux", duration=4)

        with pytest.raises(
            ValueError, match=re.escape("The wait_trigger on QDAC bus 'flux' has no port, which the QDAC requires.")
        ):
            qdac_operations(qp, {"flux"})

    def test_with_bus_mapping_remaps_weight_duration_keys(self):
        """with_bus_mapping must remap qblox.weight_duration keys, otherwise threshold programming
        can never find the duration for a mapped bus."""
        weights_wf = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        qp = QProgram()
        qp.qblox.acquire(bus="readout", weights=weights_wf)

        mapped_qp = qp.with_bus_mapping(bus_mapping={"readout": "readout_q0_bus"})

        assert mapped_qp.qblox.weight_duration == {"readout_q0_bus": [120]}

    def test_with_bus_mapping_merges_weight_duration_on_target_collision(self):
        """When two source buses map onto the same target bus (e.g. multiplexed readout), their
        weight_duration entries must both survive, not have one silently overwrite the other."""
        weights_q0 = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        weights_q1 = IQPair(I=Square(amplitude=1.0, duration=300), Q=Square(amplitude=0.0, duration=300))
        qp = QProgram()
        qp.qblox.acquire(bus="readout_q0", weights=weights_q0)
        qp.qblox.acquire(bus="readout_q1", weights=weights_q1)

        mapped_qp = qp.with_bus_mapping(bus_mapping={"readout_q0": "feedline_bus", "readout_q1": "feedline_bus"})

        assert mapped_qp.qblox.weight_duration == {"feedline_bus": [120, 300]}

    def test_resolve_weight_duration_integers(self):
        """Integer durations need no calibration."""
        weights_wf = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        qp = QProgram()
        qp.qblox.acquire(bus="readout", weights=weights_wf)
        assert qp.qblox.weight_duration == {"readout": [120]}

    def test_resolve_weight_duration_does_not_mutate_the_original_qprogram(self):
        """The original QProgram must be left untouched -- callers may reuse it across multiple
        execute_qprogram calls (e.g. with different Calibration instances), and resolving weight_duration
        in place would silently poison later calls."""
        weights_wf = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        qp = QProgram()
        qp.qblox.acquire(bus="readout", weights="optimal_weights")
        calibration = Calibration()
        calibration.add_weights(bus="readout", name="optimal_weights", weights=weights_wf)
        resolved = qp.with_calibration(calibration=calibration)
        assert qp.qblox.weight_duration == {"readout": ["optimal_weights"]}
        assert resolved.qblox.weight_duration == {"readout": [120]}
        assert resolved is not qp

    def test_resolve_weight_duration_with_calibrated_weights(self):
        """String weight names are resolved to their integer duration from calibration."""
        calibration = Calibration()
        calibration.add_weights(
            bus="feedline_input_output_bus",
            name="optimal_weights",
            weights=IQPair(I=Square(amplitude=1.0, duration=300), Q=Square(amplitude=0.0, duration=300)),
        )
        qp = QProgram()
        qp.qblox.acquire(bus="feedline_input_output_bus", weights="optimal_weights")
        resolved = qp.with_calibration(calibration=calibration)
        assert resolved.qblox.weight_duration == {"feedline_input_output_bus": [300]}

    def test_resolve_weight_duration_scopes_lookup_to_the_entrys_own_bus(self):
        """When two buses register a weight under the same name with different durations, resolving
        must use the duration registered for the entry's own bus, not whichever bus is found first."""
        calibration = Calibration()
        calibration.add_weights(
            bus="feedline_input_output_bus",
            name="optimal_weights",
            weights=IQPair(I=Square(amplitude=1.0, duration=300), Q=Square(amplitude=0.0, duration=300)),
        )
        calibration.add_weights(
            bus="feedline_input_output_bus_2",
            name="optimal_weights",
            weights=IQPair(I=Square(amplitude=1.0, duration=999), Q=Square(amplitude=0.0, duration=999)),
        )
        qp = QProgram()
        qp.qblox.acquire(bus="feedline_input_output_bus_2", weights="optimal_weights")
        resolved = qp.with_calibration(calibration=calibration)
        assert resolved.qblox.weight_duration == {"feedline_input_output_bus_2": [999]}

    def test_resolve_weight_duration_uses_the_mapped_bus_for_calibration_lookup(self):
        """With a bus mapping, the calibration is looked up under the mapped (physical) bus, as the compile
        pipeline does: the mapping is applied first, then the calibration."""
        calibration = Calibration()
        calibration.add_weights(
            bus="feedline_input_output_bus",
            name="optimal_weights",
            weights=IQPair(I=Square(amplitude=1.0, duration=300), Q=Square(amplitude=0.0, duration=300)),
        )
        qp = QProgram()
        qp.qblox.acquire(bus="readout", weights="optimal_weights")
        resolved = qp.with_bus_mapping(bus_mapping={"readout": "feedline_input_output_bus"}).with_calibration(
            calibration=calibration
        )
        # weight_duration is read from the program, so it is keyed by the mapped bus
        assert resolved.qblox.weight_duration == {"feedline_input_output_bus": [300]}

    def test_resolve_weight_duration_calibration_none_raises(self):
        """A calibrated weight name without a calibration stays a name, and compiling raises."""
        qp = QProgram()
        qp.qblox.acquire(bus="readout", weights="optimal_weights")
        assert qp.qblox.weight_duration == {"readout": ["optimal_weights"]}
        with pytest.raises(RuntimeError, match="contains named operations that are not mapped"):
            QbloxCompiler().compile(qprogram=qp, calibration=None)

    def test_resolve_weight_duration_weight_not_found_raises(self):
        """A calibrated weight name absent from the calibration stays a name, and compiling raises."""
        calibration = Calibration()
        calibration.add_weights(
            bus="feedline_input_output_bus",
            name="other_weights",
            weights=IQPair(I=Square(amplitude=1.0, duration=300), Q=Square(amplitude=0.0, duration=300)),
        )
        qp = QProgram()
        qp.qblox.acquire(bus="feedline_input_output_bus", weights="optimal_weights")
        assert qp.with_calibration(calibration=calibration).qblox.weight_duration == {
            "feedline_input_output_bus": ["optimal_weights"]
        }
        with pytest.raises(RuntimeError, match="contains named operations that are not mapped"):
            QbloxCompiler().compile(qprogram=qp, calibration=calibration)

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
        assert new_qp.body.elements[0].elements[1].targets[0] == "drive_q0_bus"
        assert new_qp.body.elements[0].elements[1].targets[1] == "readout_q0_bus"
        assert new_qp.body.elements[0].elements[2].bus == "drive_q0_bus"

        self_mapping_qp = qp.with_bus_mapping(bus_mapping={"drive_bus": "drive_bus", "readout_bus": "readout_bus"})

        assert len(self_mapping_qp.buses) == 2
        assert "drive_bus" in self_mapping_qp.buses
        assert "readout_bus" in self_mapping_qp.buses

        assert self_mapping_qp.body.elements[0].elements[0].bus == "drive_bus"
        assert self_mapping_qp.body.elements[0].elements[1].targets[0] == "drive_bus"
        assert self_mapping_qp.body.elements[0].elements[1].targets[1] == "readout_bus"
        assert self_mapping_qp.body.elements[0].elements[2].bus == "drive_bus"

        non_existant_mapping_qp = qp.with_bus_mapping(
            bus_mapping={"non_existant": "drive_bus", "non_existant_readout": "readout_bus"}
        )

        assert len(non_existant_mapping_qp.buses) == 2
        assert "drive_bus" in non_existant_mapping_qp.buses
        assert "readout_bus" in non_existant_mapping_qp.buses

        assert non_existant_mapping_qp.body.elements[0].elements[0].bus == "drive_bus"
        assert non_existant_mapping_qp.body.elements[0].elements[1].targets[0] == "drive_bus"
        assert non_existant_mapping_qp.body.elements[0].elements[1].targets[1] == "readout_bus"
        assert non_existant_mapping_qp.body.elements[0].elements[2].bus == "drive_bus"

    def test_with_distortions_method(self):
        """Test with_distortions applies distortions to the right buses and waveforms."""
        distortion = ExponentialCorrection(tau_exponential=1.0, amp=0.5)

        flux_wf_0 = Square(amplitude=1.0, duration=100)
        flux_wf_1 = Square(amplitude=0.5, duration=100)
        drive_wf = IQDrag(amplitude=1.0, duration=100, num_sigmas=4, drag_coefficient=0.1)
        readout_wf = IQPair(I=Square(amplitude=1.0, duration=100), Q=Square(amplitude=0.0, duration=100))
        weights = IQPair(I=Square(amplitude=1.0, duration=100), Q=Square(amplitude=1.0, duration=100))

        qp = QProgram()
        with qp.average(1000):
            qp.play(bus="flux_q0", waveform=flux_wf_0)
            qp.play(bus="flux_q1", waveform=flux_wf_1)
            qp.play(bus="drive_q0", waveform=drive_wf)
            qp.measure(bus="readout", waveform=readout_wf, weights=weights)

        new_qp = qp.with_distortions(
            bus_distortions={"flux_q0": [distortion], "flux_q1": [distortion], "drive_q0": [distortion]}
        )

        play_flux_0, play_flux_1, play_drive, measure = new_qp.body.elements[0].elements

        # A real (single) waveform becomes an Arbitrary holding the distorted envelope.
        assert isinstance(play_flux_0.waveform, Arbitrary)
        np.testing.assert_allclose(play_flux_0.waveform.envelope(), distortion.apply(flux_wf_0.envelope()))

        # Every distorted bus is handled, not just the last one (regression: dict built inside the bus loop).
        assert isinstance(play_flux_1.waveform, Arbitrary)
        np.testing.assert_allclose(play_flux_1.waveform.envelope(), distortion.apply(flux_wf_1.envelope()))

        # An IQ waveform that is not an IQPair (IQDrag) is handled without raising (regression: UnboundLocalError).
        assert isinstance(play_drive.waveform, IQPair)
        assert isinstance(play_drive.waveform.I, Arbitrary)
        assert isinstance(play_drive.waveform.Q, Arbitrary)
        np.testing.assert_allclose(play_drive.waveform.I.envelope(), distortion.apply(drive_wf.get_I().envelope()))
        np.testing.assert_allclose(play_drive.waveform.Q.envelope(), distortion.apply(drive_wf.get_Q().envelope()))

        # A bus that is not in the mapping is left untouched.
        assert isinstance(measure.waveform, IQPair)
        assert isinstance(measure.waveform.I, Square)

        # The original QProgram is left unchanged.
        orig_flux_0, orig_flux_1, orig_drive, orig_measure = qp.body.elements[0].elements
        assert isinstance(orig_flux_0.waveform, Square)
        assert isinstance(orig_flux_1.waveform, Square)
        assert isinstance(orig_drive.waveform, IQDrag)
        assert isinstance(orig_measure.waveform, IQPair)

    def test_with_distortions_applies_multiple_distortions_in_order(self):
        """Test with_distortions chains multiple distortions on the same bus in order."""
        first = ExponentialCorrection(tau_exponential=1.0, amp=0.5)
        second = ExponentialCorrection(tau_exponential=2.0, amp=0.3)

        flux_wf = Square(amplitude=1.0, duration=100)

        qp = QProgram()
        qp.play(bus="flux_q0", waveform=flux_wf)

        new_qp = qp.with_distortions(bus_distortions={"flux_q0": [first, second]})

        expected = second.apply(first.apply(flux_wf.envelope()))
        assert isinstance(new_qp.body.elements[0].waveform, Arbitrary)
        np.testing.assert_allclose(new_qp.body.elements[0].waveform.envelope(), expected)

    def test_with_distortions_applies_to_qblox_and_qdac_plays(self):
        """qp.qblox.play and qp.qdac.play are distorted like qp.play."""
        distortion = ExponentialCorrection(tau_exponential=1.0, amp=0.5)
        flux_wf = Square(amplitude=1.0, duration=100)

        qp = QProgram()
        qp.qblox.play(bus="flux_q0", waveform=flux_wf, wait_time=40)
        qp.qdac.play(bus="flux_q1", waveform=flux_wf, dwell=2)

        qblox_play, qdac_play = qp.with_distortions(
            bus_distortions={"flux_q0": [distortion], "flux_q1": [distortion]}
        ).body.elements

        for play in (qblox_play, qdac_play):
            assert isinstance(play.waveform, Arbitrary)
            np.testing.assert_allclose(play.waveform.envelope(), distortion.apply(flux_wf.envelope()))
        assert qblox_play.wait_time == 40
        assert qdac_play.dwell == 2

    def test_with_distortions_raises_for_measure_reset_control_bus(self):
        """Test with_distortions raises when a MeasureReset's control_bus has distortions configured.

        The reset_pulse of a MeasureReset is played on control_bus at compile time, outside of the
        QProgram tree with_distortions traverses, so it cannot be distorted here.
        """
        distortion = ExponentialCorrection(tau_exponential=1.0, amp=0.5)
        square_wf = Square(amplitude=1.0, duration=100)

        qp = QProgram()
        with qp.average(1000):
            qp.qblox.measure_reset(
                bus="readout_bus",
                waveform=IQPair(square_wf, square_wf),
                weights=IQPair(I=square_wf, Q=square_wf),
                control_bus="drive_bus",
                reset_pulse=IQPair(square_wf, square_wf),
            )

        with pytest.raises(
            NotImplementedError,
            match=re.escape(
                "Applying pulse distortions to the control bus of a `MeasureReset` (active reset) "
                "operation is not supported, but bus 'drive_bus' has distortions configured."
            ),
        ):
            qp.with_distortions(bus_distortions={"drive_bus": [distortion]})

        # Distortions on the readout bus (the MeasureReset's main `waveform`) are unaffected.
        new_qp = qp.with_distortions(bus_distortions={"readout_bus": [distortion]})
        measure_reset = new_qp.body.elements[0].elements[0]
        assert isinstance(measure_reset.waveform, IQPair)
        assert isinstance(measure_reset.waveform.I, Arbitrary)

    def test_with_calibration_method(self):
        """Test with_calibration method"""
        xgate = IQDrag(amplitude=1.0, duration=40, num_sigmas=4.5, drag_coefficient=-4.5)
        drag_reset = IQDrag(amplitude=0.5, duration=40, num_sigmas=4.5, drag_coefficient=-4.5)
        readout = IQPair(I=Square(1.0, 200), Q=Square(1.0, 200))
        weights = IQPair(I=Square(1.0, 2000), Q=Square(1.0, 2000))

        calibration = Calibration()
        calibration.add_waveform(bus="drive_q0_bus", name="xgate", waveform=xgate)
        calibration.add_waveform(bus="readout_q0_bus", name="readout", waveform=readout)
        calibration.add_weights(bus="readout_q0_bus", name="weights", weights=weights)
        calibration.add_waveform(bus="drive_q0_bus", name="drag_reset", waveform=drag_reset)

        qp = QProgram()
        with qp.average(1000):
            qp.play(bus="drive_q0_bus", waveform="xgate")
            qp.qblox.play(bus="drive_q0_bus", waveform="xgate", wait_time=100)
            qp.qblox.acquire(bus="readout_q0_bus", weights="weights")
            qp.measure(bus="readout_q0_bus", waveform="readout", weights=weights)
            qp.measure(bus="readout_q0_bus", waveform=readout, weights="weights")
            qp.measure(bus="readout_q0_bus", waveform="readout", weights="weights")
            qp.qblox.measure_reset(
                bus="readout_q0_bus",
                waveform="readout",
                weights="weights",
                control_bus="drive_q0_bus",
                reset_pulse="drag_reset",
            )

        def assert_named_operations(program: QProgram) -> None:
            elements = program.body.elements[0].elements
            assert program.has_calibrated_waveforms_or_weights() is True
            assert type(elements[0]) is Play
            assert elements[0].waveform == "xgate"
            assert isinstance(elements[1], QbloxPlay)
            assert elements[1].waveform == "xgate"
            assert isinstance(elements[2], Acquire)
            assert elements[2].weights == "weights"
            assert isinstance(elements[3], Measure)
            assert elements[3].waveform == "readout"
            assert isinstance(elements[4], Measure)
            assert elements[4].weights == "weights"
            assert isinstance(elements[5], Measure)
            assert elements[5].waveform == "readout"
            assert elements[5].weights == "weights"
            assert isinstance(elements[6], MeasureReset)
            assert elements[6].waveform == "readout"
            assert elements[6].weights == "weights"
            assert elements[6].control_bus == "drive_q0_bus"
            assert elements[6].reset_pulse == "drag_reset"

        # Check that qp has named operations
        assert_named_operations(qp)

        new_qp = qp.with_calibration(calibration=calibration)

        # Check that qp remain unchanged
        assert_named_operations(qp)

        # Check that new_qp has no named operations
        assert new_qp.has_calibrated_waveforms_or_weights() is False
        elements = new_qp.body.elements[0].elements
        assert type(elements[0]) is Play
        assert elements[0].waveform == xgate
        assert isinstance(elements[1], QbloxPlay)
        assert elements[1].waveform == xgate
        assert elements[1].wait_time == 100
        assert isinstance(elements[2], Acquire)
        assert elements[2].weights == weights
        assert isinstance(elements[3], Measure)
        assert (elements[3].waveform, elements[3].weights) == (readout, weights)
        assert isinstance(elements[4], Measure)
        assert (elements[4].waveform, elements[4].weights) == (readout, weights)
        assert isinstance(elements[5], Measure)
        assert (elements[5].waveform, elements[5].weights) == (readout, weights)
        assert isinstance(elements[6], MeasureReset)
        assert (elements[6].waveform, elements[6].weights, elements[6].reset_pulse) == (readout, weights, drag_reset)

    def test_with_calibration_method_block(self):
        """Test with_calibration block method"""
        drag_reset = IQDrag(amplitude=0.5, duration=40, num_sigmas=4.5, drag_coefficient=-4.5)
        readout = IQPair(I=Square(1.0, 200), Q=Square(1.0, 200))
        weights = IQPair(I=Square(1.0, 2000), Q=Square(1.0, 2000))

        calibration = Calibration()
        calibration.add_waveform(bus="readout", name="readout", waveform=readout)
        calibration.add_weights(bus="readout", name="weights", weights=weights)
        calibration.add_waveform(bus="drive", name="drag_reset", waveform=drag_reset)

        measure_qp_block = QProgram()
        measure_qp_block.qblox.measure_reset(
            bus="readout", waveform="readout", weights="weights", control_bus="drive", reset_pulse="drag_reset"
        )
        calibration.add_block("reset", measure_qp_block.body)
        reset_block = calibration.get_block(name="reset")

        qp = QProgram()
        with qp.average(1000):
            qp.insert_block(reset_block)

        assert qp.has_calibrated_waveforms_or_weights() is True
        assert isinstance(qp.body.elements[0].elements[0], MeasureReset)
        assert qp.body.elements[0].elements[0].waveform == "readout"
        assert qp.body.elements[0].elements[0].weights == "weights"
        assert qp.body.elements[0].elements[0].control_bus == "drive"
        assert qp.body.elements[0].elements[0].reset_pulse == "drag_reset"

        new_qp = qp.with_calibration(calibration=calibration)

        assert isinstance(new_qp.body.elements[0].elements[0], MeasureReset)
        assert new_qp.has_calibrated_waveforms_or_weights() is False

    def test_insert_block_names_each_measurement(self):
        """A block can be inserted several times: each copy of a measurement gets a new name."""
        weights = IQPair(I=Square(1.0, 100), Q=Square(0.0, 100))
        block_qp = QProgram()
        block_qp.qblox.acquire(bus="readout", weights=weights)

        qp = QProgram()
        first = qp.measure(bus="readout", waveform=weights, weights=weights)
        qp.insert_block(block_qp.body)
        qp.insert_block(block_qp.body)

        assert first.name == "m0"
        assert [element.handle.name for element in qp.body.elements] == ["m0", "m1", "m2"]
        assert block_qp.body.elements[0].handle.name == "m0"

    def test_average_method(self):
        """Test average method"""
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
        assert qp._body.elements[0].waveform == one_wf
        assert isinstance(qp._body.elements[1], Play)
        assert qp._body.elements[1].bus == "drive"
        assert qp._body.elements[1].waveform.I == one_wf
        assert qp._body.elements[1].waveform.Q == zero_wf

    def test_qblox_play_method(self):
        """qp.qblox.play overwrites the wait time of the Q1ASM play instruction."""
        one_wf = Square(amplitude=1.0, duration=40)
        qp = QProgram()
        qp.qblox.play(bus="drive", waveform=one_wf, wait_time=8)

        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], QbloxPlay)
        assert qp._body.elements[0].bus == "drive"
        assert qp._body.elements[0].waveform == one_wf
        assert qp._body.elements[0].wait_time == 8

    def test_qblox_play_method_without_wait_time_is_a_play(self):
        """qp.qblox.play with wait_time=None is a plain play, which waits the waveform's duration."""
        one_wf = Square(amplitude=1.0, duration=40)
        qp = QProgram()
        qp.qblox.play(bus="drive", waveform=one_wf, wait_time=None)

        assert len(qp._body.elements) == 1
        assert type(qp._body.elements[0]) is Play
        assert qp._body.elements[0].bus == "drive"
        assert qp._body.elements[0].waveform == one_wf

    def test_wait_method(self):
        """Test wait method"""
        qp = QProgram()
        qp.wait(bus="drive", duration=100)

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], Wait)
        assert qp._body.elements[0].bus == "drive"
        assert qp._body.elements[0].duration == 100

    def test_wait_trigger_method(self):
        """Test wait trigger method"""
        qp = QProgram()
        qp.qblox.wait_trigger(bus="flux_1", duration=100)
        qp.qblox.wait_trigger(bus="flux_2", duration=100, port=1)
        qp.qdac.wait_trigger(bus="flux_3", port=2)

        assert len(qp._active_block.elements) == 3
        assert len(qp._body.elements) == 3
        assert isinstance(qp._body.elements[0], QbloxWaitTrigger)
        assert qp._body.elements[0].bus == "flux_1"
        assert qp._body.elements[0].duration == 100
        assert qp._body.elements[0].port is None

        assert isinstance(qp._body.elements[1], QbloxWaitTrigger)
        assert qp._body.elements[1].bus == "flux_2"
        assert qp._body.elements[1].duration == 100
        assert qp._body.elements[1].port == 1

        assert isinstance(qp._body.elements[2], QdacWaitTrigger)
        assert qp._body.elements[2].bus == "flux_3"
        assert qp._body.elements[2].port == 2

    def test_wait_trigger_method_with_bus_mapping(self):
        """Test wait trigger method with bus mapping remaps the wait_trigger buses."""
        qp = QProgram()
        qp.qblox.wait_trigger(bus="flux_1", duration=100)
        qp.qblox.wait_trigger(bus="flux_2", duration=100, port=1)

        new_qp = qp.with_bus_mapping(bus_mapping={"flux_1": "flux_x", "flux_2": "flux_z"})
        assert len(new_qp._active_block.elements) == 2
        assert len(new_qp._body.elements) == 2
        assert isinstance(new_qp._body.elements[0], QbloxWaitTrigger)
        assert new_qp._body.elements[0].bus == "flux_x"
        assert new_qp._body.elements[0].duration == 100
        assert new_qp._body.elements[0].port is None

        assert isinstance(new_qp._body.elements[1], QbloxWaitTrigger)
        assert new_qp._body.elements[1].bus == "flux_z"
        assert new_qp._body.elements[1].duration == 100
        assert new_qp._body.elements[1].port == 1

    def test_set_trigger_method(self):
        """qp.qblox.set_trigger takes a duration in ns, qp.qdac.set_trigger one in seconds."""
        qp = QProgram()
        qp.qblox.set_trigger(bus="drive", duration=100, outputs=1, position="start")
        qp.qdac.set_trigger(bus="flux", duration=10e-6, position="step", outputs=[1, 2])

        qblox_trigger, qdac_trigger = qp.body.elements
        assert isinstance(qblox_trigger, QbloxSetTrigger)
        assert (qblox_trigger.bus, qblox_trigger.duration, qblox_trigger.outputs, qblox_trigger.position) == (
            "drive",
            100,
            1,
            "start",
        )
        assert isinstance(qdac_trigger, QdacSetTrigger)
        assert (qdac_trigger.bus, qdac_trigger.duration, qdac_trigger.outputs, qdac_trigger.position) == (
            "flux",
            10e-6,
            (1, 2),
            "step",
        )

    def test_measure_method(self):
        """Test measure method"""
        one_wf = Square(amplitude=1.0, duration=40)
        zero_wf = Square(amplitude=0.0, duration=40)
        qp = QProgram()
        handle = qp.measure(bus="readout", waveform=IQPair(one_wf, zero_wf), weights=IQPair(one_wf, zero_wf))

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], Measure)
        assert qp._body.elements[0].bus == "readout"
        assert qp._body.elements[0].waveform.I == one_wf
        assert qp._body.elements[0].waveform.Q == zero_wf
        assert qp._body.elements[0].weights.I == one_wf
        assert qp._body.elements[0].weights.Q == zero_wf
        assert qp._body.elements[0].handle == handle
        assert qp.qblox.weight_duration == {"readout": [40]}

    def test_acquire_method(self):
        """Test acquire method"""
        one_wf = Square(amplitude=1.0, duration=40)
        zero_wf = Square(amplitude=0.0, duration=40)
        qp = QProgram()
        handle = qp.qblox.acquire(bus="readout", weights=IQPair(I=one_wf, Q=zero_wf))

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], Acquire)
        assert qp._body.elements[0].bus == "readout"
        assert qp._body.elements[0].weights.I == one_wf
        assert qp._body.elements[0].weights.Q == zero_wf
        assert qp._body.elements[0].handle == handle

    def test_measurements_are_named_in_declaration_order(self):
        """measure, acquire and measure_reset share one counter, m0, m1, ...; name= overrides it; scopes are named
        scope0, ..."""
        wf = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        qp = QProgram()
        measure = qp.measure(bus="readout", waveform=wf, weights=wf)
        acquire = qp.qblox.acquire(bus="readout", weights=wf)
        named = qp.qblox.acquire(bus="readout", weights=wf, name="resonator")
        measure_reset = qp.qblox.measure_reset(
            bus="readout", waveform=wf, weights=wf, control_bus="drive", reset_pulse=wf
        )
        scope = qp.qblox.scope(bus="readout")

        assert all(isinstance(handle, MeasurementHandle) for handle in (measure, acquire, named, measure_reset, scope))
        assert [measure.name, acquire.name, named.name, measure_reset.name] == ["m0", "m1", "resonator", "m2"]
        assert scope.name == "scope0"
        assert isinstance(qp.body.elements[-1], Scope)
        assert qp.qblox.weight_duration == {"readout": [40, 40, 40, 40]}

    def test_weight_duration_single_acquisition(self):
        """A single acquire populates the bus list with one entry."""
        weights_wf = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        qp = QProgram()
        qp.qblox.acquire(bus="readout", weights=weights_wf)
        assert qp.qblox.weight_duration == {"readout": [120]}

    def test_weight_duration_multiple_acquisitions_same_bus(self):
        """Multiple acquires on the same bus append to the list in order."""
        w1 = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        w2 = IQPair(I=Square(amplitude=1.0, duration=200), Q=Square(amplitude=0.0, duration=200))
        qp = QProgram()
        qp.qblox.acquire(bus="readout", weights=w1)
        qp.qblox.acquire(bus="readout", weights=w2)
        assert qp.qblox.weight_duration == {"readout": [120, 200]}

    def test_weight_duration_multiple_buses(self):
        """Different buses have independent lists."""
        w1 = IQPair(I=Square(amplitude=1.0, duration=120), Q=Square(amplitude=0.0, duration=120))
        w2 = IQPair(I=Square(amplitude=1.0, duration=200), Q=Square(amplitude=0.0, duration=200))
        qp = QProgram()
        qp.qblox.acquire(bus="readout_a", weights=w1)
        qp.qblox.acquire(bus="readout_b", weights=w2)
        assert qp.qblox.weight_duration == {"readout_a": [120], "readout_b": [200]}

    def test_qdac_methods(self):
        """Test the qp.qdac operations"""
        one_wf = Square(amplitude=1.0, duration=40)
        qp = QProgram()
        qp.qdac.play(bus="flux", waveform=one_wf, dwell=2, delay=0, repetitions=100)
        qp.qdac.set_offset(bus="flux", offset=0.3)

        assert len(qp._active_block.elements) == 2
        assert len(qp._body.elements) == 2
        assert isinstance(qp._body.elements[0], QdacPlay)
        assert qp._body.elements[0].bus == "flux"
        assert qp._body.elements[0].waveform == one_wf
        assert (qp._body.elements[0].dwell, qp._body.elements[0].delay) == (2, 0)
        assert qp._body.elements[0].repetitions == 100
        assert isinstance(qp._body.elements[1], QdacSetOffset)
        assert qp._body.elements[1].offset == 0.3

    def test_sync_method(self):
        """Test sync method"""
        qp = QProgram()
        qp.sync(buses=["drive", "flux"])

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], Sync)
        assert qp._body.elements[0].targets == ["drive", "flux"]

    def test_reset_phase(self):
        """Test reset_phase method"""
        qp = QProgram()
        qp.reset_phase(bus="drive")

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], ResetPhase)
        assert qp._body.elements[0].bus == "drive"

    def test_set_phase(self):
        """Test set_phase method"""
        qp = QProgram()
        qp.set_phase(bus="drive", phase=2 * np.pi)

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], SetPhase)
        assert qp._body.elements[0].bus == "drive"
        assert qp._body.elements[0].phase == 2 * np.pi

    def test_set_frequency(self):
        """Test set_frequency method"""
        qp = QProgram()
        qp.set_frequency(bus="drive", frequency=1e6)

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], SetFrequency)
        assert qp._body.elements[0].bus == "drive"
        assert qp._body.elements[0].frequency == 1e6

    def test_set_gain(self):
        """Test set_gain method"""
        qp = QProgram()
        qp.set_gain(bus="drive", gain=1.0)

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], SetGain)
        assert qp._body.elements[0].bus == "drive"
        assert qp._body.elements[0].gain == 1.0

    def test_set_offset(self):
        """Test set_offset method"""
        qp = QProgram()
        qp.set_offset(bus="drive", offset_path0=1.0, offset_path1=0.0)

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], SetOffset)
        assert qp._body.elements[0].bus == "drive"
        assert qp._body.elements[0].offset_path0 == 1.0
        assert qp._body.elements[0].offset_path1 == 0.0

    def test_with_crosstalk_multi_variable_offset(self):
        """Test with_crosstalk_qblox covers the multi-variable branch in handle_offset
        and handle_gain when len(variable_list) > 1."""
        # Build a 2x2 crosstalk matrix between flux_bus_0 and flux_bus_1
        inverse_xtalk_array = np.linalg.inv([[1, 0.5], [0.5, 1]])
        crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], inverse_xtalk_array)

        # Test handle_offset
        qp = QProgram()
        offset_0 = qp.variable("offset_0")
        offset_1 = qp.variable("offset_1")

        # Nested loops
        with qp.sweep(offset_0).from_range(0.0, 0.5, 0.1):
            with qp.sweep(offset_1).from_range(0.0, 0.5, 0.1):
                qp.set_offset(bus="flux_bus_0", offset_path0=offset_0, offset_path1=0.0)
                qp.set_offset(bus="flux_bus_1", offset_path0=offset_1, offset_path1=0.0)

        new_qp = qp.with_crosstalk_qblox(crosstalk)
        assert new_qp is not None

        # Test handle_gain
        qp2 = QProgram()
        gain_0 = qp2.variable("gain_0")
        gain_1 = qp2.variable("gain_1")

        with qp2.sweep(gain_0).from_range(0.0, 0.5, 0.1):
            with qp2.sweep(gain_1).from_range(0.0, 0.5, 0.1):
                qp2.set_gain(bus="flux_bus_0", gain=gain_0)
                qp2.set_gain(bus="flux_bus_1", gain=gain_1)

        new_qp2 = qp2.with_crosstalk_qblox(crosstalk)
        assert new_qp2 is not None

    @ignore_for_loop_deprecation
    def test_with_crosstalk_non_linear(self):
        """Test with_crosstalk_qblox covers the non-linear implementation."""
        # Build a 2x2 crosstalk matrix between flux_bus_0 and flux_bus_1
        inverse_xtalk_array = np.linalg.inv([[1, 0.5], [0.5, 1]])
        crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], inverse_xtalk_array)
        non_linear_crosstalk = NonLinearCrosstalkMatrix.from_linear(crosstalk)
        non_linear_crosstalk.set_non_linear_params("flux2", "flux1", beta_c=0.8, amplitude=0.5)

        square_wf = Square(amplitude=0.1, duration=50)
        square_iq = IQPair(I=square_wf, Q=square_wf)
        qp = QProgram()
        offset = qp.variable("offset")
        with qp.for_loop(variable=offset, start=0, stop=0.1, step=0.08):
            qp.set_offset(bus="flux1", offset_path0=offset)
            qp.wait(bus="drive", duration=10)
            qp.wait(bus="flux1", duration=10)
            qp.wait(bus="flux2", duration=10)
            qp.set_gain(bus="flux2", gain=0.05)
            qp.play(bus="flux1", waveform=square_wf)
            qp.play(bus="drive", waveform=square_iq)
            qp.sync(["drive", "readout"])
            qp.measure(bus="readout", waveform=square_iq, weights=square_iq)

        new_qp = qp.with_crosstalk_qblox(non_linear_crosstalk)
        assert new_qp is not None

        assert isinstance(new_qp.body.elements[0], SetOffset)
        assert math.isclose(new_qp.body.elements[0].offset_path0, 0.0)
        assert new_qp.body.elements[0].bus == "flux1"
        assert isinstance(new_qp.body.elements[1], SetOffset)
        assert math.isclose(new_qp.body.elements[1].offset_path0, 0.0)
        assert new_qp.body.elements[1].bus == "flux2"
        assert isinstance(new_qp.body.elements[2], Wait)
        assert new_qp.body.elements[2].bus == "drive"
        assert isinstance(new_qp.body.elements[3], Wait)
        assert new_qp.body.elements[3].bus == "flux1"
        assert isinstance(new_qp.body.elements[4], Wait)
        assert new_qp.body.elements[4].bus == "flux2"
        assert isinstance(new_qp.body.elements[5], SetGain)
        assert math.isclose(new_qp.body.elements[5].gain, 0.3471177904070214)
        assert new_qp.body.elements[5].bus == "flux1"
        assert isinstance(new_qp.body.elements[6], Play)
        assert isinstance(new_qp.body.elements[6].waveform, Square)
        assert new_qp.body.elements[6].bus == "flux1"
        # Check that Square pulses are normalized
        assert math.isclose(new_qp.body.elements[6].waveform.amplitude, 1.0)
        assert isinstance(new_qp.body.elements[7], SetGain)
        assert new_qp.body.elements[7].bus == "flux2"
        assert math.isclose(new_qp.body.elements[7].gain, 0.5442355808140428)
        assert isinstance(new_qp.body.elements[8], Play)
        assert isinstance(new_qp.body.elements[8].waveform, Square)
        assert new_qp.body.elements[8].bus == "flux2"
        assert isinstance(new_qp.body.elements[9], Play)
        assert new_qp.body.elements[9].bus == "drive"
        assert isinstance(new_qp.body.elements[10], Sync)
        assert new_qp.body.elements[10].targets == ["drive", "readout"]
        assert isinstance(new_qp.body.elements[11], Measure)
        assert new_qp.body.elements[11].bus == "readout"
        assert isinstance(new_qp.body.elements[12], Sync)
        # Repeat loop for second iteration
        assert isinstance(new_qp.body.elements[13], SetOffset)
        assert math.isclose(new_qp.body.elements[13].offset_path0, 0.3471177904070214)
        assert new_qp.body.elements[13].bus == "flux1"
        assert isinstance(new_qp.body.elements[14], SetOffset)
        assert math.isclose(new_qp.body.elements[14].offset_path0, 0.5442355808140428)
        assert new_qp.body.elements[14].bus == "flux2"
        assert isinstance(new_qp.body.elements[15], Wait)
        assert new_qp.body.elements[15].bus == "drive"
        assert isinstance(new_qp.body.elements[16], Wait)
        assert new_qp.body.elements[16].bus == "flux1"
        assert isinstance(new_qp.body.elements[17], Wait)
        assert new_qp.body.elements[17].bus == "flux2"
        assert isinstance(new_qp.body.elements[18], SetGain)
        assert math.isclose(new_qp.body.elements[18].gain, 0.08143146795214351)
        assert new_qp.body.elements[18].bus == "flux1"
        assert isinstance(new_qp.body.elements[19], Play)
        assert isinstance(new_qp.body.elements[19].waveform, Square)
        assert new_qp.body.elements[19].bus == "flux1"
        # Check that Square pulses are normalized
        assert math.isclose(new_qp.body.elements[19].waveform.amplitude, 1.0)
        assert isinstance(new_qp.body.elements[20], SetGain)
        assert new_qp.body.elements[20].bus == "flux2"
        assert math.isclose(new_qp.body.elements[20].gain, 0.012862935904286998)
        assert isinstance(new_qp.body.elements[21], Play)
        assert isinstance(new_qp.body.elements[21].waveform, Square)
        assert new_qp.body.elements[21].bus == "flux2"
        assert isinstance(new_qp.body.elements[22], Play)
        assert new_qp.body.elements[22].bus == "drive"
        assert isinstance(new_qp.body.elements[23], Sync)
        assert new_qp.body.elements[23].targets == ["drive", "readout"]
        assert isinstance(new_qp.body.elements[24], Measure)
        assert new_qp.body.elements[24].bus == "readout"
        assert isinstance(new_qp.body.elements[25], Sync)

    def test_with_crosstalk_non_linear_set_offset_after_loop(self):
        """Test with_crosstalk_qblox covers the non-linear implementation repeating consecutive offsets and plays."""
        # Build a 2x2 crosstalk matrix between flux_bus_0 and flux_bus_1
        inverse_xtalk_array = np.linalg.inv([[1, 0.5], [0.5, 1]])
        crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], inverse_xtalk_array)
        non_linear_crosstalk = NonLinearCrosstalkMatrix.from_linear(crosstalk)
        non_linear_crosstalk.set_non_linear_params("flux2", "flux1", beta_c=0.8, amplitude=0.5)

        square_wf = Square(amplitude=0.1, duration=50)
        square_iq = IQPair(I=square_wf, Q=square_wf)
        qp = QProgram()
        offset = qp.variable("offset")
        with qp.sweep(offset).from_range(0, 0.9, 0.1):
            qp.set_offset(bus="flux1", offset_path0=offset)
            qp.set_offset(bus="flux2", offset_path0=0.1)
            qp.play(bus="drive", waveform=square_iq)
            qp.sync(["drive", "readout"])
            qp.measure(bus="readout", waveform=square_iq, weights=square_iq)
        qp.set_offset(bus="flux1", offset_path0=0)
        qp.set_offset(bus="flux2", offset_path0=0)

        new_qp = qp.with_crosstalk_qblox(non_linear_crosstalk)
        assert new_qp is not None
        # FIRST ITERATION
        assert isinstance(new_qp.body.elements[0], SetOffset)
        assert math.isclose(new_qp.body.elements[0].offset_path0, 0.05)
        assert new_qp.body.elements[0].bus == "flux1"
        assert isinstance(new_qp.body.elements[1], SetOffset)
        assert math.isclose(new_qp.body.elements[1].offset_path0, 0.1)
        assert new_qp.body.elements[1].bus == "flux2"
        assert isinstance(new_qp.body.elements[2], Play)
        assert new_qp.body.elements[2].bus == "drive"
        assert isinstance(new_qp.body.elements[3], Sync)
        assert new_qp.body.elements[3].targets == ["drive", "readout"]
        assert isinstance(new_qp.body.elements[4], Measure)
        assert new_qp.body.elements[4].bus == "readout"
        assert isinstance(new_qp.body.elements[5], Sync)
        # LAST ITERATION
        assert isinstance(new_qp.body.elements[54], SetOffset)
        assert math.isclose(new_qp.body.elements[54].offset_path0, 0.7028822095929785)
        assert new_qp.body.elements[54].bus == "flux1"
        assert isinstance(new_qp.body.elements[55], SetOffset)
        assert math.isclose(new_qp.body.elements[55].offset_path0, 0.05576441918595704)
        assert new_qp.body.elements[55].bus == "flux2"
        assert isinstance(new_qp.body.elements[56], Play)
        assert new_qp.body.elements[56].bus == "drive"
        assert isinstance(new_qp.body.elements[57], Sync)
        assert new_qp.body.elements[57].targets == ["drive", "readout"]
        assert isinstance(new_qp.body.elements[58], Measure)
        assert new_qp.body.elements[58].bus == "readout"
        assert isinstance(new_qp.body.elements[59], Sync)
        # FINISHING OFFSETS TO 0
        assert isinstance(new_qp.body.elements[60], SetOffset)
        assert math.isclose(new_qp.body.elements[60].offset_path0, 0.0)
        assert new_qp.body.elements[60].bus == "flux1"
        assert isinstance(new_qp.body.elements[61], SetOffset)
        assert math.isclose(new_qp.body.elements[61].offset_path0, 0.0)
        assert new_qp.body.elements[61].bus == "flux2"

    def test_with_crosstalk_non_linear_offset_loop_after_offset_loop(self):
        """Test with_crosstalk_qblox covers the non-linear implementation repeating consecutive offsets and plays."""
        # Build a 2x2 crosstalk matrix between flux_bus_0 and flux_bus_1
        inverse_xtalk_array = np.linalg.inv([[1, 0.5], [0.5, 1]])
        crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], inverse_xtalk_array)
        non_linear_crosstalk = NonLinearCrosstalkMatrix.from_linear(crosstalk)
        non_linear_crosstalk.set_non_linear_params("flux2", "flux1", beta_c=0.8, amplitude=0.5)

        square_wf = Square(amplitude=0.1, duration=50)
        square_iq = IQPair(I=square_wf, Q=square_wf)
        qp = QProgram()
        offset = qp.variable("offset")
        with qp.sweep(offset).from_range(0, 0.9, 0.1):
            qp.set_offset(bus="flux1", offset_path0=offset)
            qp.set_offset(bus="flux2", offset_path0=0.1)
            qp.play(bus="drive", waveform=square_iq)
            qp.sync(["drive", "readout"])
            qp.measure(bus="readout", waveform=square_iq, weights=square_iq)
        with qp.sweep(offset).from_range(0.9, 0, -0.1):
            qp.set_offset(bus="flux1", offset_path0=offset)
            qp.set_offset(bus="flux2", offset_path0=0.1)
            qp.play(bus="drive", waveform=square_iq)
            qp.sync(["drive", "readout"])
            qp.measure(bus="readout", waveform=square_iq, weights=square_iq)

        new_qp = qp.with_crosstalk_qblox(non_linear_crosstalk)
        assert new_qp is not None
        # FIRST ITERATION FIRST LOOP
        assert isinstance(new_qp.body.elements[0], SetOffset)
        assert math.isclose(new_qp.body.elements[0].offset_path0, 0.05)
        assert new_qp.body.elements[0].bus == "flux1"
        assert isinstance(new_qp.body.elements[1], SetOffset)
        assert math.isclose(new_qp.body.elements[1].offset_path0, 0.1)
        assert new_qp.body.elements[1].bus == "flux2"
        assert isinstance(new_qp.body.elements[2], Play)
        assert new_qp.body.elements[2].bus == "drive"
        assert isinstance(new_qp.body.elements[3], Sync)
        assert new_qp.body.elements[3].targets == ["drive", "readout"]
        assert isinstance(new_qp.body.elements[4], Measure)
        assert new_qp.body.elements[4].bus == "readout"
        assert isinstance(new_qp.body.elements[5], Sync)
        # LAST ITERATION FIRST LOOP
        assert isinstance(new_qp.body.elements[54], SetOffset)
        assert math.isclose(new_qp.body.elements[54].offset_path0, 0.7028822095929785)
        assert new_qp.body.elements[54].bus == "flux1"
        assert isinstance(new_qp.body.elements[55], SetOffset)
        assert math.isclose(new_qp.body.elements[55].offset_path0, 0.05576441918595704)
        assert new_qp.body.elements[55].bus == "flux2"
        assert isinstance(new_qp.body.elements[56], Play)
        assert new_qp.body.elements[56].bus == "drive"
        assert isinstance(new_qp.body.elements[57], Sync)
        assert new_qp.body.elements[57].targets == ["drive", "readout"]
        assert isinstance(new_qp.body.elements[58], Measure)
        assert new_qp.body.elements[58].bus == "readout"
        assert isinstance(new_qp.body.elements[59], Sync)
        # FIRST ITERATION SECOND LOOP
        assert isinstance(new_qp.body.elements[60], SetOffset)
        assert math.isclose(new_qp.body.elements[60].offset_path0, 0.7028822095929785)
        assert new_qp.body.elements[60].bus == "flux1"
        assert isinstance(new_qp.body.elements[61], SetOffset)
        assert math.isclose(new_qp.body.elements[61].offset_path0, 0.05576441918595704)
        assert new_qp.body.elements[61].bus == "flux2"
        assert isinstance(new_qp.body.elements[62], Play)
        assert new_qp.body.elements[62].bus == "drive"
        assert isinstance(new_qp.body.elements[63], Sync)
        assert new_qp.body.elements[63].targets == ["drive", "readout"]
        assert isinstance(new_qp.body.elements[64], Measure)
        assert new_qp.body.elements[64].bus == "readout"
        assert isinstance(new_qp.body.elements[65], Sync)
        # LAST ITERATION SECOND LOOP
        assert isinstance(new_qp.body.elements[114], SetOffset)
        assert math.isclose(new_qp.body.elements[114].offset_path0, 0.05)
        assert new_qp.body.elements[114].bus == "flux1"
        assert isinstance(new_qp.body.elements[115], SetOffset)
        assert math.isclose(new_qp.body.elements[115].offset_path0, 0.1)
        assert new_qp.body.elements[115].bus == "flux2"
        assert isinstance(new_qp.body.elements[116], Play)
        assert new_qp.body.elements[116].bus == "drive"
        assert isinstance(new_qp.body.elements[117], Sync)
        assert new_qp.body.elements[117].targets == ["drive", "readout"]
        assert isinstance(new_qp.body.elements[118], Measure)
        assert new_qp.body.elements[118].bus == "readout"
        assert isinstance(new_qp.body.elements[119], Sync)

    @ignore_for_loop_deprecation
    def test_with_crosstalk_non_linear_repeat_offset_play(self):
        """Test with_crosstalk_qblox covers the non-linear implementation repeating consecutive offsets and plays."""
        # Build a 2x2 crosstalk matrix between flux_bus_0 and flux_bus_1
        inverse_xtalk_array = np.linalg.inv([[1, 0.5], [0.5, 1]])
        crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], inverse_xtalk_array)
        non_linear_crosstalk = NonLinearCrosstalkMatrix.from_linear(crosstalk)
        non_linear_crosstalk.set_non_linear_params("flux2", "flux1", beta_c=0.8, amplitude=0.5)

        square_wf = Square(amplitude=0.1, duration=50)
        square_iq = IQPair(I=square_wf, Q=square_wf)
        qp = QProgram()
        offset = qp.variable("offset")
        with qp.for_loop(variable=offset, start=0, stop=0.1, step=0.08):
            qp.set_offset(bus="flux1", offset_path0=offset)
            qp.wait(bus="drive", duration=10)
            qp.wait(bus="flux1", duration=10)
            qp.wait(bus="flux2", duration=10)
            qp.set_offset(bus="flux1", offset_path0=0.1)
            qp.wait(bus="drive", duration=10)
            qp.wait(bus="flux1", duration=10)
            qp.wait(bus="flux2", duration=10)
            qp.play(bus="flux1", waveform=square_wf)
            qp.play(bus="flux1", waveform=square_wf)
            qp.play(bus="drive", waveform=square_iq)
            qp.sync(["drive", "readout"])
            qp.measure(bus="readout", waveform=square_iq, weights=square_iq)

        new_qp = qp.with_crosstalk_qblox(non_linear_crosstalk)
        assert new_qp is not None

        assert isinstance(new_qp.body.elements[0], SetOffset)
        assert math.isclose(new_qp.body.elements[0].offset_path0, 0.0)
        assert new_qp.body.elements[0].bus == "flux1"
        assert isinstance(new_qp.body.elements[1], SetOffset)
        assert math.isclose(new_qp.body.elements[1].offset_path0, 0.0)
        assert new_qp.body.elements[1].bus == "flux2"
        assert isinstance(new_qp.body.elements[2], Wait)
        assert new_qp.body.elements[2].bus == "drive"
        assert isinstance(new_qp.body.elements[3], Wait)
        assert new_qp.body.elements[3].bus == "flux1"
        assert isinstance(new_qp.body.elements[4], Wait)
        assert new_qp.body.elements[4].bus == "flux2"
        # New offsets are called after waits
        assert isinstance(new_qp.body.elements[5], SetOffset)
        assert math.isclose(new_qp.body.elements[5].offset_path0, 0.3471177904070214)
        assert new_qp.body.elements[5].bus == "flux1"
        assert isinstance(new_qp.body.elements[6], SetOffset)
        assert math.isclose(new_qp.body.elements[6].offset_path0, 0.5442355808140428)
        assert new_qp.body.elements[6].bus == "flux2"
        assert isinstance(new_qp.body.elements[7], Wait)
        assert new_qp.body.elements[7].bus == "drive"
        assert isinstance(new_qp.body.elements[8], Wait)
        assert new_qp.body.elements[8].bus == "flux1"
        assert isinstance(new_qp.body.elements[9], Wait)
        assert new_qp.body.elements[9].bus == "flux2"
        assert isinstance(new_qp.body.elements[10], SetGain)
        assert math.isclose(new_qp.body.elements[10].gain, 0.08143146795214351)
        assert new_qp.body.elements[10].bus == "flux1"
        assert isinstance(new_qp.body.elements[11], Play)
        assert isinstance(new_qp.body.elements[11].waveform, Square)
        assert new_qp.body.elements[11].bus == "flux1"
        # Check that Square pulses are normalized
        assert math.isclose(new_qp.body.elements[11].waveform.amplitude, 1.0)
        assert isinstance(new_qp.body.elements[12], SetGain)
        assert new_qp.body.elements[12].bus == "flux2"
        assert math.isclose(new_qp.body.elements[12].gain, 0.012862935904286998)
        assert isinstance(new_qp.body.elements[13], Play)
        assert isinstance(new_qp.body.elements[13].waveform, Square)
        # Play structure is repeated (because there's two consecutive plays with the same bus)
        assert isinstance(new_qp.body.elements[14], SetGain)
        assert new_qp.body.elements[14].bus == "flux1"
        assert math.isclose(new_qp.body.elements[14].gain, 0.08143146795214351)
        assert isinstance(new_qp.body.elements[15], Play)
        assert isinstance(new_qp.body.elements[15].waveform, Square)
        assert new_qp.body.elements[15].bus == "flux1"
        assert isinstance(new_qp.body.elements[16], SetGain)
        assert new_qp.body.elements[16].bus == "flux2"
        assert math.isclose(new_qp.body.elements[16].gain, 0.012862935904286998)
        assert isinstance(new_qp.body.elements[17], Play)
        assert isinstance(new_qp.body.elements[17].waveform, Square)
        assert new_qp.body.elements[17].bus == "flux2"
        assert isinstance(new_qp.body.elements[18], Play)
        assert new_qp.body.elements[18].bus == "drive"
        assert isinstance(new_qp.body.elements[19], Sync)
        assert new_qp.body.elements[19].targets == ["drive", "readout"]
        assert isinstance(new_qp.body.elements[20], Measure)
        assert new_qp.body.elements[20].bus == "readout"
        assert isinstance(new_qp.body.elements[21], Sync)
        # The loop repeats itself until 47 iterations,
        # we focus here on the initial offsets being modified and the last point
        assert isinstance(new_qp.body.elements[22], SetOffset)
        assert math.isclose(new_qp.body.elements[22].offset_path0, 0.3471177904070214)
        assert new_qp.body.elements[22].bus == "flux1"
        assert isinstance(new_qp.body.elements[23], SetOffset)
        assert math.isclose(new_qp.body.elements[23].offset_path0, 0.5442355808140428)
        assert new_qp.body.elements[23].bus == "flux2"
        assert isinstance(new_qp.body.elements[24], Wait)
        assert new_qp.body.elements[24].bus == "drive"
        assert isinstance(new_qp.body.elements[25], Wait)
        assert new_qp.body.elements[25].bus == "flux1"
        assert isinstance(new_qp.body.elements[26], Wait)
        assert new_qp.body.elements[26].bus == "flux2"
        # New offsets are called after waits (again)
        assert isinstance(new_qp.body.elements[27], SetOffset)
        assert math.isclose(new_qp.body.elements[27].offset_path0, 0.3471177904070214)
        assert new_qp.body.elements[27].bus == "flux1"
        assert isinstance(new_qp.body.elements[28], SetOffset)
        assert math.isclose(new_qp.body.elements[28].offset_path0, 0.5442355808140428)
        # ...
        assert isinstance(new_qp.body.elements[43], Sync)

    def test_with_crosstalk_non_linear_convert_arbitrary_play(self):
        """Test with_crosstalk_qblox covers the non-linear implementation repeating consecutive offsets and plays."""
        # Build a 2x2 crosstalk matrix between flux_bus_0 and flux_bus_1
        inverse_xtalk_array = np.linalg.inv([[1, 0.5], [0.5, 1]])
        crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], inverse_xtalk_array)
        non_linear_crosstalk = NonLinearCrosstalkMatrix.from_linear(crosstalk)
        non_linear_crosstalk.set_non_linear_params("flux2", "flux1", beta_c=0.8, amplitude=0.5)

        gauss_wf = Gaussian(amplitude=0.1, duration=50, num_sigmas=4)
        square_wf = Square(amplitude=0.1, duration=50)
        square_iq = IQPair(I=square_wf, Q=square_wf)
        qp = QProgram()
        qp.play(bus="flux1", waveform=gauss_wf)
        qp.play(bus="drive", waveform=square_iq)
        qp.sync(["drive", "readout"])
        qp.measure(bus="readout", waveform=square_iq, weights=square_iq)

        new_qp = qp.with_crosstalk_qblox(non_linear_crosstalk)
        assert new_qp is not None
        assert isinstance(new_qp.body.elements[0], SetGain)
        assert math.isclose(new_qp.body.elements[0].gain, 1)
        assert new_qp.body.elements[0].bus == "flux1"
        assert isinstance(new_qp.body.elements[1], SetOffset)
        assert math.isclose(new_qp.body.elements[1].offset_path0, 0.0)
        assert new_qp.body.elements[1].bus == "flux1"
        assert isinstance(new_qp.body.elements[2], Play)
        assert isinstance(new_qp.body.elements[2].waveform, Arbitrary)
        assert new_qp.body.elements[2].bus == "flux1"
        assert isinstance(new_qp.body.elements[3], SetGain)
        assert new_qp.body.elements[3].bus == "flux2"
        assert math.isclose(new_qp.body.elements[3].gain, 1)
        assert isinstance(new_qp.body.elements[4], SetOffset)
        assert new_qp.body.elements[4].bus == "flux2"
        assert math.isclose(new_qp.body.elements[4].offset_path0, 0.0)
        assert isinstance(new_qp.body.elements[5], Play)
        assert isinstance(new_qp.body.elements[5].waveform, Arbitrary)
        assert new_qp.body.elements[5].bus == "flux2"
        assert isinstance(new_qp.body.elements[6], Play)
        assert new_qp.body.elements[6].bus == "drive"
        assert isinstance(new_qp.body.elements[7], Sync)
        assert new_qp.body.elements[7].targets == ["drive", "readout"]
        assert isinstance(new_qp.body.elements[8], Measure)
        assert new_qp.body.elements[8].bus == "readout"
        assert isinstance(new_qp.body.elements[9], Sync)

    @ignore_for_loop_deprecation
    def test_with_crosstalk_non_linear_play_before_loop(self):
        """Test with_crosstalk_qblox covers the non-linear implementation playing a pulse before a loop."""
        # Build a 2x2 crosstalk matrix between flux_bus_0 and flux_bus_1
        inverse_xtalk_array = np.linalg.inv([[1, 0.5], [0.5, 1]])
        crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], inverse_xtalk_array)
        non_linear_crosstalk = NonLinearCrosstalkMatrix.from_linear(crosstalk)
        non_linear_crosstalk.set_non_linear_params("flux2", "flux1", beta_c=0.8, amplitude=0.5)

        square_wf = Square(amplitude=0.1, duration=50)
        gauss_wf = Gaussian(amplitude=0.7, duration=50, num_sigmas=4)
        square_iq = IQPair(I=square_wf, Q=square_wf)
        qp = QProgram()
        offset = qp.variable("offset")
        qp.play(bus="flux1", waveform=gauss_wf)
        qp.sync()
        with qp.for_loop(variable=offset, start=0, stop=0.1, step=0.08):
            qp.set_offset(bus="flux1", offset_path0=offset)
            qp.play(bus="flux1", waveform=gauss_wf)
            qp.play(bus="drive", waveform=square_iq)
            qp.sync(["drive", "readout"])
            qp.measure(bus="readout", waveform=square_iq, weights=square_iq)

        new_qp = qp.with_crosstalk_qblox(non_linear_crosstalk)
        assert new_qp is not None
        assert isinstance(new_qp.body.elements[0], SetGain)
        assert math.isclose(new_qp.body.elements[0].gain, 1)
        assert new_qp.body.elements[0].bus == "flux1"
        assert isinstance(new_qp.body.elements[1], SetOffset)
        assert math.isclose(new_qp.body.elements[1].offset_path0, 0.0)
        assert new_qp.body.elements[1].bus == "flux1"
        assert isinstance(new_qp.body.elements[2], Play)
        assert isinstance(new_qp.body.elements[2].waveform, Arbitrary)
        assert new_qp.body.elements[2].bus == "flux1"
        assert isinstance(new_qp.body.elements[3], SetGain)
        assert new_qp.body.elements[3].bus == "flux2"
        assert math.isclose(new_qp.body.elements[3].gain, 1)
        assert isinstance(new_qp.body.elements[4], SetOffset)
        assert new_qp.body.elements[4].bus == "flux2"
        assert math.isclose(new_qp.body.elements[4].offset_path0, 0.0)
        assert isinstance(new_qp.body.elements[5], Play)
        assert isinstance(new_qp.body.elements[5].waveform, Arbitrary)
        assert new_qp.body.elements[5].bus == "flux2"
        assert isinstance(new_qp.body.elements[6], Sync)
        # Here the loop begins
        assert isinstance(new_qp.body.elements[7], SetOffset)
        assert math.isclose(new_qp.body.elements[7].offset_path0, 0.0)
        assert new_qp.body.elements[7].bus == "flux1"
        assert isinstance(new_qp.body.elements[8], SetOffset)
        assert math.isclose(new_qp.body.elements[8].offset_path0, 0.0)
        assert isinstance(new_qp.body.elements[9], SetGain)
        assert math.isclose(new_qp.body.elements[9].gain, 1)
        assert new_qp.body.elements[9].bus == "flux1"
        assert isinstance(new_qp.body.elements[10], Play)
        assert isinstance(new_qp.body.elements[10].waveform, Arbitrary)
        assert new_qp.body.elements[10].bus == "flux1"
        assert isinstance(new_qp.body.elements[11], SetGain)
        assert new_qp.body.elements[11].bus == "flux2"
        assert math.isclose(new_qp.body.elements[11].gain, 1)
        assert isinstance(new_qp.body.elements[12], Play)
        assert isinstance(new_qp.body.elements[12].waveform, Arbitrary)
        assert new_qp.body.elements[12].bus == "flux2"
        assert isinstance(new_qp.body.elements[13], Play)
        assert new_qp.body.elements[13].bus == "drive"
        assert isinstance(new_qp.body.elements[14], Sync)
        assert new_qp.body.elements[14].targets == ["drive", "readout"]
        assert isinstance(new_qp.body.elements[15], Measure)
        assert new_qp.body.elements[15].bus == "readout"
        assert isinstance(new_qp.body.elements[16], Sync)
        # ... second iteration of the loop
        assert isinstance(new_qp.body.elements[26], Sync)

    def test_with_crosstalk_non_linear_skips_sync_after_conditional(self):
        """Test with_crosstalk_qblox does not append the usual trailing loop Sync when a flux loop
        iteration's last element is a qp.if_trigger() block: that IfTrigger already self-times its
        own exit, and a Sync placed right after it would touch the gated bus outside the block, which
        the Qblox pre-pass forbids."""
        inverse_xtalk_array = np.linalg.inv([[1, 0.5], [0.5, 1]])
        crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], inverse_xtalk_array)
        non_linear_crosstalk = NonLinearCrosstalkMatrix.from_linear(crosstalk)
        non_linear_crosstalk.set_non_linear_params("flux2", "flux1", beta_c=0.8, amplitude=0.5)

        square_wf = Square(amplitude=0.1, duration=50)
        qp = QProgram()
        offset = qp.variable("offset")
        with qp.sweep(offset).from_range(0, 0.08, 0.08):
            qp.set_offset(bus="flux1", offset_path0=offset)
            qp.set_gain(bus="flux2", gain=0.05)
            qp.play(bus="flux1", waveform=square_wf)
            qp.play(bus="flux2", waveform=square_wf)
            with qp.if_trigger(expected_wait_time_ns=2252):
                qp.wait(bus="readout", duration=100)

        new_qp = qp.with_crosstalk_qblox(non_linear_crosstalk)

        # Two iterations of 7 elements each (no Sync inserted between them): SetOffset(flux1),
        # SetOffset(flux2), SetGain(flux1), Play(flux1), SetGain(flux2), Play(flux2), then each
        # iteration's own IfTrigger.
        assert len(new_qp.body.elements) == 14
        assert isinstance(new_qp.body.elements[6], IfTrigger)
        assert isinstance(new_qp.body.elements[7], SetOffset)
        assert isinstance(new_qp.body.elements[13], IfTrigger)
        assert new_qp.body.elements[13].expected_wait_time_ns == 2252

    def test_with_crosstalk_linear_repeated_bus_restarts_flux_vector(self):
        """Test with_crosstalk_qblox restarts the flux vector when a bus is played again on the linear path."""
        inverse_xtalk_array = np.linalg.inv([[1, 0.5], [0.5, 1]])
        crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], inverse_xtalk_array)

        square_wf = Square(amplitude=0.1, duration=40)
        long_square_wf = Square(amplitude=0.1, duration=400)
        qp = QProgram()
        qp.play(bus="flux1", waveform=square_wf)
        qp.play(bus="flux2", waveform=square_wf)
        qp.play(bus="flux1", waveform=long_square_wf)

        new_qp = qp.with_crosstalk_qblox(crosstalk)

        assert len(new_qp.body.elements) == 4
        # First group: flux1 and flux2 played together.
        assert isinstance(new_qp.body.elements[0], Play)
        assert new_qp.body.elements[0].bus == "flux1"
        assert math.isclose(new_qp.body.elements[0].waveform.amplitude, 0.15)
        assert new_qp.body.elements[0].waveform.duration == 40
        assert isinstance(new_qp.body.elements[1], Play)
        assert new_qp.body.elements[1].bus == "flux2"
        assert math.isclose(new_qp.body.elements[1].waveform.amplitude, 0.15)
        assert new_qp.body.elements[1].waveform.duration == 40
        # Second group: repeated flux1 compensated with flux2 back at zero.
        assert isinstance(new_qp.body.elements[2], Play)
        assert new_qp.body.elements[2].bus == "flux2"
        assert math.isclose(new_qp.body.elements[2].waveform.amplitude, 0.05)
        assert new_qp.body.elements[2].waveform.duration == 400
        assert isinstance(new_qp.body.elements[3], Play)
        assert new_qp.body.elements[3].bus == "flux1"
        assert math.isclose(new_qp.body.elements[3].waveform.amplitude, 0.1)
        assert new_qp.body.elements[3].waveform.duration == 400

    def test_with_crosstalk_linear_repeated_bus_keeps_flux_vector_offset(self):
        """Test with_crosstalk_qblox keeps the flux vector when a bus offset is set again on the linear path."""
        inverse_xtalk_array = np.linalg.inv([[1, 0.5], [0.5, 1]])
        crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], inverse_xtalk_array)

        qp = QProgram()
        qp.set_offset(bus="flux1", offset_path0=0.1)
        qp.set_offset(bus="flux2", offset_path0=0.2)
        qp.wait(bus="flux1", duration=100)
        qp.wait(bus="flux2", duration=100)
        qp.set_offset(bus="flux1", offset_path0=0.3)

        new_qp = qp.with_crosstalk_qblox(crosstalk)

        assert len(new_qp.body.elements) == 6
        # First group: flux1 and flux2 set together.
        assert isinstance(new_qp.body.elements[0], SetOffset)
        assert new_qp.body.elements[0].bus == "flux1"
        assert math.isclose(new_qp.body.elements[0].offset_path0, 0.2)
        assert isinstance(new_qp.body.elements[1], SetOffset)
        assert new_qp.body.elements[1].bus == "flux2"
        assert math.isclose(new_qp.body.elements[1].offset_path0, 0.25)
        assert isinstance(new_qp.body.elements[2], Wait)
        assert isinstance(new_qp.body.elements[3], Wait)
        # Second group: the flux vector is maintained, so flux2 persists when flux1 is set again.
        assert isinstance(new_qp.body.elements[4], SetOffset)
        assert new_qp.body.elements[4].bus == "flux2"
        assert math.isclose(new_qp.body.elements[4].offset_path0, 0.35)
        assert isinstance(new_qp.body.elements[5], SetOffset)
        assert new_qp.body.elements[5].bus == "flux1"
        assert math.isclose(new_qp.body.elements[5].offset_path0, 0.4)

    def test_with_crosstalk_linear_repeated_offset_group_is_not_overwritten(self):
        """Test with_crosstalk_qblox keeps each offset group's value when offsets are set again without a wait."""
        inverse_xtalk_array = np.linalg.inv([[1, 0.5], [0.5, 1]])
        crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], inverse_xtalk_array)

        qp = QProgram()
        qp.set_offset(bus="flux1", offset_path0=0.15)
        qp.set_offset(bus="flux2", offset_path0=0.15)
        qp.wait(bus="readout", duration=400)
        qp.sync()
        qp.set_offset(bus="flux1", offset_path0=0.0)
        qp.set_offset(bus="flux2", offset_path0=0.0)
        qp.play(bus="flux1", waveform=Square(amplitude=0.1, duration=40))
        qp.play(bus="flux2", waveform=Square(amplitude=0.1, duration=40))
        qp.set_offset(bus="flux1", offset_path0=0.15)
        qp.set_offset(bus="flux2", offset_path0=0.15)
        qp.wait(bus="readout", duration=400)

        new_qp = qp.with_crosstalk_qblox(crosstalk)

        offsets = [element for element in new_qp.body.elements if isinstance(element, SetOffset)]
        assert [offset.bus for offset in offsets] == ["flux1", "flux2"] * 3
        assert all(math.isclose(offset.offset_path0, 0.225) for offset in offsets[:2])
        assert all(math.isclose(offset.offset_path0, 0.0) for offset in offsets[2:4])
        assert all(math.isclose(offset.offset_path0, 0.225) for offset in offsets[4:])

    def test_with_crosstalk_linear_repeated_bus_keeps_flux_vector_gain(self):
        """Test with_crosstalk_qblox keeps the flux vector when a bus gain is set again on the linear path."""
        inverse_xtalk_array = np.linalg.inv([[1, 0.5], [0.5, 1]])
        crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], inverse_xtalk_array)

        qp = QProgram()
        qp.set_gain(bus="flux1", gain=0.1)
        qp.set_gain(bus="flux2", gain=0.2)
        qp.wait(bus="flux1", duration=100)
        qp.wait(bus="flux2", duration=100)
        qp.set_gain(bus="flux1", gain=0.3)

        new_qp = qp.with_crosstalk_qblox(crosstalk)

        assert len(new_qp.body.elements) == 6
        # First group: flux1 and flux2 set together.
        assert isinstance(new_qp.body.elements[0], SetGain)
        assert new_qp.body.elements[0].bus == "flux1"
        assert math.isclose(new_qp.body.elements[0].gain, 0.2)
        assert isinstance(new_qp.body.elements[1], SetGain)
        assert new_qp.body.elements[1].bus == "flux2"
        assert math.isclose(new_qp.body.elements[1].gain, 0.25)
        assert isinstance(new_qp.body.elements[2], Wait)
        assert isinstance(new_qp.body.elements[3], Wait)
        # Second group: the flux vector is maintained, so flux2 persists when flux1 is set again.
        assert isinstance(new_qp.body.elements[4], SetGain)
        assert new_qp.body.elements[4].bus == "flux2"
        assert math.isclose(new_qp.body.elements[4].gain, 0.35)
        assert isinstance(new_qp.body.elements[5], SetGain)
        assert new_qp.body.elements[5].bus == "flux1"
        assert math.isclose(new_qp.body.elements[5].gain, 0.4)

    @pytest.mark.parametrize(
        "crosstalk_type",
        [pytest.param(CrosstalkMatrix, id="linear_path"), pytest.param(NonLinearCrosstalkMatrix, id="non_linear_path")],
    )
    def test_with_crosstalk_qblox_adds_corrected_buses(self, crosstalk_type):
        """Test with_crosstalk_qblox adds the buses of the elements added to `qprogram.buses`."""
        inverse_xtalk_array = np.linalg.inv([[1, 0.5], [0.5, 1]])
        crosstalk = crosstalk_type.from_array(["flux1", "flux2"], inverse_xtalk_array)

        qp = QProgram()
        qp.set_offset(bus="flux1", offset_path0=0.15)
        qp.wait(bus="flux1", duration=50)

        new_qp = qp.with_crosstalk_qblox(crosstalk)
        assert new_qp.buses == {"flux1", "flux2"}

        qp = QProgram()
        qp.play(bus="flux1", waveform=Square(0.1, 50))

        new_qp = qp.with_crosstalk_qblox(crosstalk)
        assert new_qp.buses == {"flux1", "flux2"}

    @staticmethod
    def _sweep_steps(block):
        """All the sweep steps (including those of Parallel blocks) reachable from ``block``."""
        steps = []
        for element in block.elements:
            if isinstance(element, Parallel):
                steps += [loop.source.step for loop in element.loops]
            elif isinstance(element, Sweep):
                steps.append(element.source.step)
            if isinstance(element, Block):
                steps += TestQProgram._sweep_steps(element)
        return steps

    def test_with_crosstalk_qblox_offset_flux_vs_flux_unequal_length_loops(self):
        """Nested flux-vs-flux offset loops of different lengths must not raise: the per-bus arrays
        are accumulated without an eager element-wise cross product and compensated via decomposition."""
        crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], np.linalg.inv([[1, 0.5], [0.5, 1]]))
        square_wf = Square(amplitude=0.1, duration=50)
        qp = QProgram()
        offset_1 = qp.variable("offset_1")
        offset_2 = qp.variable("offset_2")
        with qp.sweep(offset_1).from_range(-0.19, 0.19, 0.01):  # 39 points
            with qp.sweep(offset_2).from_range(-0.18, 0.19, 0.01):  # 38 points
                qp.set_offset(bus="flux1", offset_path0=offset_1)
                qp.set_offset(bus="flux2", offset_path0=offset_2)
                qp.play(bus="flux1", waveform=square_wf)

        new_qp = qp.with_crosstalk_qblox(crosstalk)
        assert new_qp is not None

        # The two nested loops survive with their different lengths (previously this raised).
        outer = new_qp.body.elements[0]
        assert isinstance(outer, Parallel)
        inner = next(element for element in outer.elements if isinstance(element, Parallel))
        assert {loop.num_iterations() for loop in outer.loops} == {39}
        assert {loop.num_iterations() for loop in inner.loops} == {38}

        # Both flux buses are compensated at the innermost level, each combining the two variables.
        inner_offsets = [element for element in inner.elements if isinstance(element, SetOffset)]
        assert {offset.bus for offset in inner_offsets} == {"flux1", "flux2"}
        assert all(isinstance(offset.offset_path0, BinaryOp) for offset in inner_offsets)

    @ignore_for_loop_deprecation
    @pytest.mark.parametrize("start, stop, step", [(0.0, 1.0, 0.3), (1.0, 0.0, -0.3)])
    def test_with_crosstalk_qblox_loop_step_not_dividing_range(self, start, stop, step):
        """A step that doesn't divide the range gives 4 points in both directions, and the compensated loops keep
        them."""
        crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], np.linalg.inv([[1, 0.5], [0.5, 1]]))
        qp = QProgram()
        offset = qp.variable("offset")
        with qp.for_loop(variable=offset, start=start, stop=stop, step=step):
            qp.set_offset(bus="flux1", offset_path0=offset)
            qp.play(bus="flux1", waveform=Square(amplitude=0.1, duration=50))

        compensated = qp.with_crosstalk_qblox(crosstalk)

        parallel = compensated.body.elements[0]
        assert isinstance(parallel, Parallel)
        assert {loop.num_iterations() for loop in parallel.loops} == {4}

    def test_with_crosstalk_qblox_offsets_across_loop_levels_carried_and_summed(self):
        """flux_1 offset set in the outer loop and flux_2 in the inner one: the outer level keeps its
        compensated offsets for the time before the inner loop, and each innermost offset combines both
        variables' contributions (a sum of the two)."""
        from tests.qprogram.crosstalk.crosstalk_simulation import assert_compensated

        crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], np.linalg.inv([[1, 0.5], [0.5, 1]]))
        square_wf = Square(amplitude=0.1, duration=50)

        def build():
            qp = QProgram()
            offset_1 = qp.variable("offset_1")
            offset_2 = qp.variable("offset_2")
            with qp.sweep(offset_1).from_range(0.0, 0.1, 0.01):
                qp.set_offset(bus="flux1", offset_path0=offset_1)
                # Set explicitly: otherwise flux2 keeps the inner loop's last value from the previous iteration.
                qp.set_offset(bus="flux2", offset_path0=0.0)
                qp.wait(bus="flux1", duration=100)
                with qp.sweep(offset_2).from_range(0.0, 0.1, 0.01):
                    qp.set_offset(bus="flux2", offset_path0=offset_2)
                    qp.play(bus="flux1", waveform=square_wf)
                    qp.wait(bus="flux1", duration=100)
            return qp

        new_qp = build().with_crosstalk_qblox(crosstalk)
        outer = new_qp.body.elements[0]
        assert isinstance(outer, Parallel)
        assert {element.bus for element in outer.elements if isinstance(element, SetOffset)} == {"flux1", "flux2"}
        inner = next(element for element in outer.elements if isinstance(element, Parallel))
        inner_offsets = [element for element in inner.elements if isinstance(element, SetOffset)]
        assert {offset.bus for offset in inner_offsets} == {"flux1", "flux2"}
        # Each innermost offset combines the outer (a1) and inner (a2) contributions.
        assert all(isinstance(offset.offset_path0, BinaryOp) for offset in inner_offsets)
        assert_compensated(build(), new_qp, crosstalk)

    def test_with_crosstalk_qblox_identity_matrix_across_levels_drops_zero_terms(self):
        """An identity matrix has zero cross-terms: no constant (step-0) compensation loop survives
        and each innermost offset is swept by a single variable, matching having no crosstalk."""
        identity = CrosstalkMatrix().from_array(["flux1", "flux2"], np.eye(2))
        square_wf = Square(amplitude=0.1, duration=50)
        qp = QProgram()
        offset_1 = qp.variable("offset_1")
        offset_2 = qp.variable("offset_2")
        with qp.sweep(offset_1).from_range(0.0, 0.1, 0.01):
            qp.set_offset(bus="flux1", offset_path0=offset_1)
            with qp.sweep(offset_2).from_range(0.0, 0.1, 0.01):
                qp.set_offset(bus="flux2", offset_path0=offset_2)
                qp.play(bus="flux1", waveform=square_wf)

        new_qp = qp.with_crosstalk_qblox(identity)
        assert all(step != 0 for step in self._sweep_steps(new_qp.body))
        outer = new_qp.body.elements[0]
        # A compensated loop with a single live bus is a plain Sweep.
        inner = next(element for element in outer.elements if isinstance(element, (Sweep, Parallel)))
        inner_offsets = [element for element in inner.elements if isinstance(element, SetOffset)]
        # No cross-term: each offset depends on a single variable, not a sum.
        assert all(isinstance(offset.offset_path0, Variable) for offset in inner_offsets)

    def test_with_crosstalk_qblox_same_level_identity_skips_zero_cross_offsets(self):
        """Both offsets set at the same (innermost) level under an identity matrix: with more than one
        swept variable in scope, each bus's zero cross-term is skipped from the summed offset, so every
        offset depends on a single variable (not a sum) and no step-0 loop is produced."""
        identity = CrosstalkMatrix().from_array(["flux1", "flux2"], np.eye(2))
        square_wf = Square(amplitude=0.1, duration=50)
        qp = QProgram()
        offset_1 = qp.variable("offset_1")
        offset_2 = qp.variable("offset_2")
        with qp.sweep(offset_1).from_range(0.0, 0.1, 0.01):
            with qp.sweep(offset_2).from_range(0.0, 0.1, 0.01):
                qp.set_offset(bus="flux1", offset_path0=offset_1)
                qp.set_offset(bus="flux2", offset_path0=offset_2)
                qp.play(bus="flux1", waveform=square_wf)

        new_qp = qp.with_crosstalk_qblox(identity)
        assert all(step != 0 for step in self._sweep_steps(new_qp.body))
        inner = next(element for element in new_qp.body.elements[0].elements if isinstance(element, (Sweep, Parallel)))
        inner_offsets = [element for element in inner.elements if isinstance(element, SetOffset)]
        assert {offset.bus for offset in inner_offsets} == {"flux1", "flux2"}
        assert all(isinstance(offset.offset_path0, Variable) for offset in inner_offsets)

    def test_with_crosstalk_qblox_same_level_identity_skips_zero_cross_gains(self):
        """Same as above but for gains set at the same innermost level: the zero cross-term of each
        bus is skipped from the summed gain, leaving a single-variable gain per bus."""
        identity = CrosstalkMatrix().from_array(["flux1", "flux2"], np.eye(2))
        square_wf = Square(amplitude=0.1, duration=50)
        qp = QProgram()
        gain_1 = qp.variable("gain_1")
        gain_2 = qp.variable("gain_2")
        with qp.sweep(gain_1).from_range(0.0, 0.1, 0.01):
            with qp.sweep(gain_2).from_range(0.0, 0.1, 0.01):
                qp.set_gain(bus="flux1", gain=gain_1)
                qp.set_gain(bus="flux2", gain=gain_2)
                qp.play(bus="flux1", waveform=square_wf)

        new_qp = qp.with_crosstalk_qblox(identity)
        assert all(step != 0 for step in self._sweep_steps(new_qp.body))
        inner = next(element for element in new_qp.body.elements[0].elements if isinstance(element, (Sweep, Parallel)))
        inner_gains = [element for element in inner.elements if isinstance(element, SetGain)]
        assert {gain.bus for gain in inner_gains} == {"flux1", "flux2"}
        assert all(isinstance(gain.gain, Variable) for gain in inner_gains)

    def test_with_crosstalk_qblox_offsets_across_three_loop_levels(self):
        """Three nested flux loops (flux1/flux2 coupled, flux3 independent): a contribution carried
        through more than one enclosing level reaches the innermost block, and every level matches
        the uncompensated program numerically."""
        from tests.qprogram.crosstalk.crosstalk_simulation import assert_compensated

        matrix = np.linalg.inv([[1, 0.5, 0], [0.5, 1, 0], [0, 0, 1]])
        crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2", "flux3"], matrix)
        square_wf = Square(amplitude=0.1, duration=50)

        def build():
            qp = QProgram()
            a1 = qp.variable("a1")
            a2 = qp.variable("a2")
            a3 = qp.variable("a3")
            with qp.sweep(a1).from_range(0.0, 0.1, 0.02):
                qp.set_offset(bus="flux1", offset_path0=a1)
                with qp.sweep(a2).from_range(0.0, 0.1, 0.02):
                    qp.set_offset(bus="flux2", offset_path0=a2)
                    with qp.sweep(a3).from_range(0.0, 0.1, 0.02):
                        qp.set_offset(bus="flux3", offset_path0=a3)
                        qp.play(bus="flux1", waveform=square_wf)
                        qp.wait(bus="flux1", duration=100)
            return qp

        assert_compensated(build(), build().with_crosstalk_qblox(crosstalk), crosstalk)

    def test_with_crosstalk_qblox_gains_across_loop_levels_carried_and_summed(self):
        """Gains behave like offsets: the outer level keeps its compensated gains, and the gains in
        the inner block combine both loops."""
        from tests.qprogram.crosstalk.crosstalk_simulation import assert_compensated

        crosstalk = CrosstalkMatrix().from_array(["flux1", "flux2"], np.linalg.inv([[1, 0.5], [0.5, 1]]))
        square_wf = Square(amplitude=0.1, duration=50)

        def build():
            qp = QProgram()
            gain_1 = qp.variable("gain_1")
            gain_2 = qp.variable("gain_2")
            with qp.sweep(gain_1).from_range(0.0, 0.1, 0.01):
                qp.set_gain(bus="flux1", gain=gain_1)
                with qp.sweep(gain_2).from_range(0.0, 0.1, 0.01):
                    qp.set_gain(bus="flux2", gain=gain_2)
                    qp.play(bus="flux1", waveform=square_wf)
                    qp.wait(bus="flux1", duration=100)
            return qp

        new_qp = build().with_crosstalk_qblox(crosstalk)
        outer = new_qp.body.elements[0]
        assert {element.bus for element in outer.elements if isinstance(element, SetGain)} == {"flux1", "flux2"}
        inner = next(element for element in outer.elements if isinstance(element, Parallel))
        inner_gains = [element for element in inner.elements if isinstance(element, SetGain)]
        assert {gain.bus for gain in inner_gains} == {"flux1", "flux2"}
        assert all(isinstance(gain.gain, BinaryOp) for gain in inner_gains)
        assert_compensated(build(), new_qp, crosstalk, quantity="gain")

    def test_with_crosstalk_qblox_gain_identity_matrix_drops_zero_terms(self):
        """Identity matrix with gains: zero cross-terms compile to a constant gain (no step-0 loop),
        and each innermost gain is swept by a single variable."""
        identity = CrosstalkMatrix().from_array(["flux1", "flux2"], np.eye(2))
        square_wf = Square(amplitude=0.1, duration=50)
        qp = QProgram()
        gain_1 = qp.variable("gain_1")
        gain_2 = qp.variable("gain_2")
        with qp.sweep(gain_1).from_range(0.0, 0.1, 0.01):
            qp.set_gain(bus="flux1", gain=gain_1)
            with qp.sweep(gain_2).from_range(0.0, 0.1, 0.01):
                qp.set_gain(bus="flux2", gain=gain_2)
                qp.play(bus="flux1", waveform=square_wf)

        new_qp = qp.with_crosstalk_qblox(identity)
        assert all(step != 0 for step in self._sweep_steps(new_qp.body))
        inner = next(element for element in new_qp.body.elements[0].elements if isinstance(element, (Sweep, Parallel)))
        inner_gains = [element for element in inner.elements if isinstance(element, SetGain)]
        assert all(isinstance(gain.gain, Variable) for gain in inner_gains)

    def test_set_markers(self):
        qp = QProgram()
        qp.qblox.set_markers(bus="drive", mask="0111")

        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1
        assert isinstance(qp._body.elements[0], SetMarkers)
        assert qp._body.elements[0].bus == "drive"
        assert qp._body.elements[0].mask == "0111"

    @pytest.mark.parametrize("mask", ["1234", "0111011"])
    def test_set_markers_with_invalid_mask_raises_error(self, mask):
        qp = QProgram()
        with pytest.raises(AttributeError):
            qp.qblox.set_markers(bus="drive", mask=mask)

    def test_variable_in_waveform_is_rejected_at_compile_time(self):
        """Variables have no domain any more; a variable in a waveform's parameters is rejected when compiling,
        since qililab samples waveforms once, before the run."""
        qp = QProgram()
        amplitude = qp.variable("amplitude")
        with qp.sweep(amplitude).from_range(0.0, 1.0, 0.5):
            qp.play(bus="drive", waveform=Square(amplitude=amplitude, duration=40))

        with pytest.raises(ValidationError, match=re.escape("qililab.variable-in-waveform")):
            QbloxCompiler().compile(qprogram=qp)

    def test_variable_in_iq_drag_is_rejected_at_compile_time(self):
        """A variable in any parameter of an IQ waveform, here the DRAG coefficient, is rejected too."""
        qp = QProgram()
        drag_coefficient = qp.variable("drag_coefficient")
        with qp.sweep(drag_coefficient).from_range(0.0, 1.0, 0.5):
            qp.play(
                bus="drive",
                waveform=IQDrag(amplitude=1.0, duration=40, num_sigmas=4, drag_coefficient=drag_coefficient),
            )
        compiler = QbloxCompiler()

        with pytest.raises(ValidationError, match=re.escape("qililab.variable-in-waveform")):
            compiler.compile(qprogram=qp)

    def test_measure_reset_method(self):
        """Test measure_reset method"""
        one_wf = Square(amplitude=1.0, duration=40)
        zero_wf = Square(amplitude=0.0, duration=40)
        qp = QProgram()
        handle = qp.qblox.measure_reset(
            bus="readout",
            waveform=IQPair(one_wf, zero_wf),
            weights=IQPair(one_wf, zero_wf),
            control_bus="control",
            reset_pulse=IQPair(one_wf, zero_wf),
        )

        # Should append a single MeasureReset operation
        assert len(qp._active_block.elements) == 1
        assert len(qp._body.elements) == 1

        op = qp._body.elements[0]
        assert isinstance(op, MeasureReset)
        # Check measurement settings
        assert op.bus == "readout"
        assert op.waveform.I == one_wf
        assert op.waveform.Q == zero_wf
        assert op.weights.I == one_wf
        assert op.weights.Q == zero_wf
        # Check reset settings
        assert op.control_bus == "control"
        assert op.reset_pulse.I == one_wf
        assert op.reset_pulse.Q == zero_wf
        # Default trigger address, and the handle the results are stored under
        assert op.trigger_address == 1
        assert op.handle == handle
        assert handle.name == "m0"

        # Interface flags updated
        assert qp.qblox.weight_duration == {"readout": [40]}

    def test_with_bus_mapping_measure_reset(self):
        """Test with_bus_mapping method"""
        qp = QProgram()
        square_wf = Square(1, 200)
        drag = IQDrag(1, 40, 2, 2)
        with qp.average(1000):
            qp.qblox.measure_reset(
                bus="readout_bus",
                waveform=IQPair(square_wf, square_wf),
                weights=IQPair(I=square_wf, Q=square_wf),
                control_bus="drive_bus",
                reset_pulse=drag,
            )

        new_qp = qp.with_bus_mapping(bus_mapping={"drive_bus": "drive_q0_bus", "readout_bus": "readout_q0_bus"})
        assert len(new_qp.buses) == 2
        assert "drive_bus" not in new_qp.buses
        assert "readout_bus" not in new_qp.buses
        assert "drive_q0_bus" in new_qp.buses
        assert "readout_q0_bus" in new_qp.buses

        assert new_qp.body.elements[0].elements[0].bus == "readout_q0_bus"
        assert new_qp.body.elements[0].elements[0].control_bus == "drive_q0_bus"

        self_mapping_qp = qp.with_bus_mapping(bus_mapping={"drive_bus": "drive_bus", "readout_bus": "readout_bus"})

        assert len(self_mapping_qp.buses) == 2
        assert "drive_bus" in self_mapping_qp.buses
        assert "readout_bus" in self_mapping_qp.buses

        assert self_mapping_qp.body.elements[0].elements[0].bus == "readout_bus"
        assert self_mapping_qp.body.elements[0].elements[0].control_bus == "drive_bus"

        non_existant_mapping_qp = qp.with_bus_mapping(
            bus_mapping={"non_existant": "drive_bus", "non_existant_readout": "readout_bus"}
        )

        assert len(non_existant_mapping_qp.buses) == 2
        assert "drive_bus" in non_existant_mapping_qp.buses
        assert "readout_bus" in non_existant_mapping_qp.buses

        assert non_existant_mapping_qp.body.elements[0].elements[0].bus == "readout_bus"
        assert non_existant_mapping_qp.body.elements[0].elements[0].control_bus == "drive_bus"

    def test_measure_reset_raises_error(self):
        """Test that calling measure reset with a combination of calibrated and non calibrated parameters raises an error"""
        drag_reset = IQDrag(amplitude=0.5, duration=40, num_sigmas=4.5, drag_coefficient=-4.5)
        readout = IQPair(I=Square(1.0, 200), Q=Square(1.0, 200))
        weights = IQPair(I=Square(1.0, 2000), Q=Square(1.0, 2000))

        calibration = Calibration()
        calibration.add_waveform(bus="readout_q0_bus", name="readout", waveform=readout)
        calibration.add_weights(bus="readout_q0_bus", name="weights", weights=weights)

        with pytest.raises(
            NotImplementedError,
            match=re.escape(
                "For the waveform, weight, and reset pulse, you must either use the calibration file for all three or "
                "not use it at all."
            ),
        ):
            qp = QProgram()
            with qp.average(1000):
                qp.qblox.measure_reset(
                    bus="readout_q0_bus",
                    waveform="readout",
                    weights="weights",
                    control_bus="drive_q0_bus",
                    reset_pulse=drag_reset,
                )

    def test_wait_with_numpy_int_stores_python_int(self):
        qp = QProgram()
        qp.wait(bus="drive", duration=np.int64(100))
        assert qp._body.elements[0].duration == 100
        assert type(qp._body.elements[0].duration) is int

    def test_wait_trigger_with_numpy_int_stores_python_int(self):
        qp = QProgram()
        qp.qblox.wait_trigger(bus="drive", duration=np.int64(100))
        assert qp._body.elements[0].duration == 100
        assert type(qp._body.elements[0].duration) is int

    def test_if_trigger_creates_if_trigger_block_with_expected_wait_time(self):
        qp = QProgram()
        with qp.if_trigger(expected_wait_time_ns=2252):
            qp.wait(bus="readout", duration=100)

        if_trigger = qp._body.elements[0]
        assert isinstance(if_trigger, IfTrigger)
        assert if_trigger.expected_wait_time_ns == 2252
        assert len(if_trigger.elements) == 1

    def test_if_trigger_default_expected_wait_time_is_none(self):
        qp = QProgram()
        with qp.if_trigger():
            qp.wait(bus="readout", duration=100)

        if_trigger = qp._body.elements[0]
        assert isinstance(if_trigger, IfTrigger)
        assert if_trigger.expected_wait_time_ns is None

    def test_wait_trigger_then_if_trigger_raises_error(self):
        qp = QProgram()
        qp.qblox.wait_trigger(bus="drive", duration=100)
        with qp.if_trigger():
            qp.wait(bus="readout", duration=100)

        with pytest.raises(
            NotImplementedError,
            match=re.escape("if_trigger() cannot be used together with wait_trigger in the same QProgram."),
        ):
            QbloxCompiler().compile(qprogram=qp)

    def test_if_trigger_then_wait_trigger_raises_error(self):
        qp = QProgram()
        with qp.if_trigger():
            qp.wait(bus="readout", duration=100)
        qp.qdac.wait_trigger(bus="flux", port=1)

        with pytest.raises(
            NotImplementedError,
            match=re.escape("if_trigger() cannot be used together with wait_trigger in the same QProgram."),
        ):
            QbloxCompiler().compile(qprogram=qp)

    def test_measure_reset_then_if_trigger_raises_error(self):
        qp = QProgram()
        qp.qblox.measure_reset(
            bus="readout2",
            waveform=IQPair(I=Square(1.0, 1000), Q=Square(0.0, 1000)),
            weights=IQPair(I=Square(1.0, 2000), Q=Square(0.0, 2000)),
            control_bus="drive",
            reset_pulse=IQDrag(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5),
        )
        with qp.if_trigger():
            qp.wait(bus="readout", duration=100)

        with pytest.raises(
            NotImplementedError,
            match=re.escape("if_trigger() cannot be used together with qp.qblox.measure_reset() in the same QProgram."),
        ):
            QbloxCompiler().compile(qprogram=qp)

    def test_if_trigger_then_measure_reset_raises_error(self):
        qp = QProgram()
        with qp.if_trigger():
            qp.wait(bus="readout", duration=100)
        qp.qblox.measure_reset(
            bus="readout2",
            waveform=IQPair(I=Square(1.0, 1000), Q=Square(0.0, 1000)),
            weights=IQPair(I=Square(1.0, 2000), Q=Square(0.0, 2000)),
            control_bus="drive",
            reset_pulse=IQDrag(amplitude=1.0, duration=100, num_sigmas=5, drag_coefficient=1.5),
        )

        with pytest.raises(
            NotImplementedError,
            match=re.escape("if_trigger() cannot be used together with qp.qblox.measure_reset() in the same QProgram."),
        ):
            QbloxCompiler().compile(qprogram=qp)

    def test_set_offset_with_numpy_float_stores_python_float(self):
        qp = QProgram()
        qp.set_offset(bus="drive", offset_path0=np.float64(0.5), offset_path1=np.float64(0.1))
        assert qp._body.elements[0].offset_path0 == pytest.approx(0.5)
        assert qp._body.elements[0].offset_path1 == pytest.approx(0.1)
        assert type(qp._body.elements[0].offset_path0) is float
        assert type(qp._body.elements[0].offset_path1) is float

    def test_set_trigger_with_numpy_int_stores_python_int(self):
        qp = QProgram()
        qp.qblox.set_trigger(bus="drive", duration=np.int64(100), outputs=1)
        assert qp._body.elements[0].duration == 100
        assert type(qp._body.elements[0].duration) is int

    def test_set_frequency_with_numpy_float_stores_python_float(self):
        qp = QProgram()
        qp.set_frequency(bus="drive", frequency=np.float64(1e6))
        assert qp._body.elements[0].frequency == pytest.approx(1e6)
        assert type(qp._body.elements[0].frequency) is float

    def test_set_phase_with_numpy_float_stores_python_float(self):
        qp = QProgram()
        qp.set_phase(bus="drive", phase=np.float64(1.5))
        assert qp._body.elements[0].phase == pytest.approx(1.5)
        assert type(qp._body.elements[0].phase) is float

    def test_set_gain_with_numpy_float_stores_python_float(self):
        qp = QProgram()
        qp.set_gain(bus="drive", gain=np.float64(0.5))
        assert qp._body.elements[0].gain == pytest.approx(0.5)
        assert type(qp._body.elements[0].gain) is float

    def test_for_loop_with_numpy_bounds_stores_python_scalars(self):
        """The deprecated for_loop and its ForLoop description take numpy bounds and store Python numbers."""
        qp = QProgram()
        index = qp.variable("index")
        with pytest.warns(FutureWarning, match="qp.for_loop is deprecated"):
            loop_context = qp.for_loop(variable=index, start=np.int64(1), stop=np.int64(10), step=np.int64(1))
        with loop_context as loop:
            pass
        description = ForLoop(index, np.int64(1), np.float64(10.0), np.int64(1))

        assert [type(value) for value in (loop.source.start, loop.source.stop, loop.source.step)] == [float] * 3
        assert loop.num_iterations() == 10
        assert [type(value) for value in (description.start, description.stop, description.step)] == [int, float, int]

    def test_sweep_with_numpy_bounds_stores_python_scalars(self):
        qp = QProgram()
        freq = qp.variable("freq")
        with qp.sweep(freq).from_range(np.float64(1e6), np.float64(10e6), np.float64(1e6)):
            # body is irrelevant; only the loop bounds' types are under test
            pass
        loop = qp._body.elements[0]
        assert type(loop.source.start) is float
        assert type(loop.source.stop) is float
        assert type(loop.source.step) is float

    def test_average_with_numpy_int_stores_python_int(self):
        qp = QProgram()
        with qp.average(shots=np.int64(1000)):
            # body is irrelevant; only the shots type is under test
            pass
        loop = qp._body.elements[0]
        assert loop.shots == 1000
        assert type(loop.shots) is int


@pytest.mark.parametrize(
    "start,stop,step,expected_iterations",
    [
        (0, 10, 1, 11),
        (10, 0, -1, 11),
        # Within 1e-9 of an integer: snapped, not rounded down.
        (0, 0.7, 0.1, 8),
        (0.7, 0, -0.1, 8),
        # The step doesn't divide the range: rounded down in both directions.
        (1, 2.05, 0.1, 11),
        (2.05, 1, -0.1, 11),
        (0, 1, 0.3, 4),
        (1, 0, -0.3, 4),
        (0, 0.1, 0.08, 2),
        (0.1, 0, -0.08, 2),
        # The step points away from stop.
        (0, 1, -2, 0),
    ],
)
def test_for_loop_iterations(start, stop, step, expected_iterations):
    assert for_loop_iterations(start, stop, step) == expected_iterations


def test_for_loop_iterations_with_zero_step_raises():
    with pytest.raises(ValueError, match="Step value cannot be zero"):
        for_loop_iterations(100, 200, 0)
