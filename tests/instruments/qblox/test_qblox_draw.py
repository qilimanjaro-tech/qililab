"""Tests for the QbloxDraw class."""
from unittest.mock import MagicMock

import pytest
from qpysequence import Acquisitions, Program, Sequence, Waveforms, Weights

from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.qblox import QbloxQCM
from qililab.platform import Platform
from qililab.data_management import build_platform
from qililab.typings import Parameter
from typing import cast
from qblox_instruments.qcodes_drivers.sequencer import Sequencer
from qblox_instruments.qcodes_drivers.module import Module as QcmQrm
from unittest.mock import patch

import numpy as np
import pytest
import qpysequence as QPy

from qililab import Calibration, Domain, Gaussian, IQPair, QbloxCompiler, QProgram, Square
from qililab.qprogram.blocks import ForLoop
from tests.test_utils import is_q1asm_equal
from qililab.config import logger
from qililab.instruments.qblox.qblox_draw import QbloxDraw


@pytest.fixture(name="parsing")
def fixture_parsing() -> QProgram:
    qp = QProgram()
    frequency = qp.variable(label="drive", domain=Domain.Frequency)
    FREQ_START = 100e6
    FREQ_STOP = 200e6
    FREQ_STEP = 50e6
    with qp.for_loop(frequency, FREQ_START, FREQ_STOP, FREQ_STEP):
        with qp.average(2):
            qp.set_frequency(bus="drive", frequency=frequency)
            qp.play(bus="drive", waveform= Square(amplitude=1, duration=10))
            qp.wait("drive",10)
    return qp


class TestQBloxDraw:
    def test_parsing(self, parsing: QProgram):
        compiler = QbloxCompiler()
        draw = QbloxDraw()
        sequences, _ = compiler.compile(qprogram=parsing)
        parsing = draw._parse_program(sequences)
        expected_parsing = [('move', '3, R0', (), 0),
                            ('move', '400000000, R1', (), 1),
                            ('move', '2, R2', ('loop_0',), 2),
                            ('set_freq', 'R1', ('loop_0', 'avg_0'), 3),
                            ('play', '0, 1, 10', ('loop_0', 'avg_0'), 4),
                            ('wait', '10', ('loop_0', 'avg_0'), 5),
                            ('loop', 'R2, @avg_0', ('loop_0', 'avg_0'), 6),
                            ('add', 'R1, 200000000, R1', ('loop_0',), 7),
                            ('loop', 'R0, @loop_0', ('loop_0',), 8),
                            ('set_mrk', '0', (), 9),
                            ('upd_param', '4', (), 10),
                            ('stop', '', (), 11)]
        assert parsing["drive"]["program"]["main"] == expected_parsing

    # def test_qp_draw(self, qp_draw: QProgram):
    #     compiler = QbloxCompiler()
    #     draw = QbloxDraw()
    #     qp_draw.draw()
    #     expected_parsing = [('move', '3, R0', (), 0),
    #                         ('move', '400000000, R1', (), 1),
    #                         ('move', '2, R2', ('loop_0',), 2),
    #                         ('set_freq', 'R1', ('loop_0', 'avg_0'), 3),
    #                         ('play', '0, 1, 10', ('loop_0', 'avg_0'), 4),
    #                         ('wait', '10', ('loop_0', 'avg_0'), 5),
    #                         ('loop', 'R2, @avg_0', ('loop_0', 'avg_0'), 6),
    #                         ('add', 'R1, 200000000, R1', ('loop_0',), 7),
    #                         ('loop', 'R0, @loop_0', ('loop_0',), 8),
    #                         ('set_mrk', '0', (), 9),
    #                         ('upd_param', '4', (), 10),
    #                         ('stop', '', (), 11)]
    #     assert parsing["drive"]["program"]["main"] == expected_parsing


        