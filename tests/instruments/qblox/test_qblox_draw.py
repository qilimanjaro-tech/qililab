"""Tests for the QbloxDraw class."""

import numpy as np
import pytest
import plotly.io as pio
from tests.data import Galadriel, SauronQuantumMachines

from qililab import Domain, QProgram, Square, IQPair
from qililab.qprogram.qblox_compiler import QbloxCompiler
from qililab.data_management import build_platform
from qililab.instruments.qblox.qblox_draw import QbloxDraw
from qililab.platform import Platform


@pytest.fixture(name="parsing")
def fixture_parsing() -> QProgram:
    qp = QProgram()
    frequency = qp.variable(label="drive", domain=Domain.Frequency)
    FREQ_START = 100e6
    FREQ_STOP = 200e6
    FREQ_STEP = 50e6
    with qp.for_loop(frequency, FREQ_START, FREQ_STOP, FREQ_STEP):
        qp.set_frequency(bus="drive", frequency=frequency)
        qp.play(bus="drive", waveform=Square(amplitude=1, duration=10))
        qp.wait("drive", 10)
    return qp


@pytest.fixture(name="qp_draw")
def fixture_qp_draw() -> QProgram:
    qp = QProgram()
    frequency = qp.variable(label="drive", domain=Domain.Frequency)
    FREQ_START = 100e6
    FREQ_STOP = 200e6
    FREQ_STEP = 50e6
    qp.set_gain("drive", 1)
    with qp.for_loop(frequency, FREQ_START, FREQ_STOP, FREQ_STEP):
        with qp.average(2):
            qp.reset_phase("drive")
            qp.set_frequency(bus="drive", frequency=frequency)
            qp.play(bus="drive", waveform=Square(amplitude=1, duration=5))
            qp.set_frequency(bus="drive", frequency=frequency)
            qp.wait("drive", 5)
            qp.play(bus="drive", waveform=Square(amplitude=1, duration=5))
    qp.set_frequency(bus="drive", frequency=frequency)
    return qp


@pytest.fixture(name="qp_draw_with_time_window")
def fixture_qp_draw_with_time_window() -> QProgram:
    qp = QProgram()
    square_wf = IQPair(
        I=Square(amplitude=0.5, duration=5),
        Q=Square(amplitude=0, duration=5),
    )
    weights_shape = Square(amplitude=1, duration=20)
    bins = qp.variable(label="bins", domain=Domain.Scalar, type=int)
    with qp.for_loop(variable=bins, start=1, stop=3):
        qp.wait("readout_q13_bus",10)
        qp.measure(bus="readout_q13_bus", waveform =square_wf, weights= IQPair(I=weights_shape, Q=weights_shape))
    return qp

@pytest.fixture(name="qp_draw_with_time_window_nested_loop")
def fixture_qp_draw_with_time_window_nested_loop() -> QProgram:
    qp = QProgram()
    frequency = qp.variable(label="drive", domain=Domain.Frequency)
    ampl = qp.variable("drive", domain=Domain.Voltage)
    with qp.average(3):
        with qp.for_loop(frequency, 0, 100e6, 100e6):
            with qp.for_loop(ampl, 0, 1, 0.3):
                qp.set_gain("drive",ampl)
                qp.set_frequency("drive",frequency) #will do nothing for the plotting via the platform as HM is disabled
                qp.play(bus="drive", waveform= Square(amplitude=1, duration=10))
                qp.wait("drive",5)
    return qp

@pytest.fixture(name="qp_draw_with_timeout_no_loop")
def fixture_qp_draw_with_timeout_no_loop() -> QProgram:
    qp = QProgram()
    qp.wait("drive",10)
    qp.play("drive", Square(amplitude=1, duration=20))
    qp.wait("drive",10)
    return qp

@pytest.fixture(name="qp_plat_draw_qcmrf_offset")
def fixture_qp_plat_draw_qcmrf_offset() -> QProgram:
    qp = QProgram()
    qp.set_offset("drive_line_q1_bus", 0.5)
    qp.set_frequency("drive_line_q1_bus", 100e6)
    qp.play(bus="drive_line_q1_bus", waveform=Square(amplitude=1, duration=10))
    qp.wait("drive_line_q1_bus", 10)
    qp.wait("drive_line_q2_bus", 10)
    qp.set_offset("drive_line_q1_bus", 0)
    return qp


@pytest.fixture(name="qp_plat_draw_qcmrf")
def fixture_qp_plat_draw_qcmrf() -> QProgram:
    qp = QProgram()
    qp.set_phase("drive_line_q1_bus", 0.5)
    qp.set_frequency("drive_line_q1_bus", 100e6)
    qp.play(bus="drive_line_q1_bus", waveform=Square(amplitude=1, duration=10))
    qp.wait("drive_line_q1_bus", 10)
    qp.set_phase("drive_line_q1_bus", 0)
    return qp


@pytest.fixture(name="qp_plat_draw_qcm_flux")
def fixture_qp_plat_draw_qcm_flux() -> QProgram:
    qp = QProgram()
    qp.set_phase("flux_line_q0_bus", 0.5)
    qp.play(bus="flux_line_q0_bus", waveform=Square(amplitude=1, duration=10))
    qp.wait("flux_line_q0_bus", 10)
    qp.set_phase("flux_line_q0_bus", 0)
    return qp


@pytest.fixture(name="qp_plat_draw_qcm_flux_offset")
def fixture_qp_plat_draw_qcm_flux_offset() -> QProgram:
    qp = QProgram()
    qp.set_offset("flux_line_q0_bus", 0.5)
    qp.play(bus="flux_line_q0_bus", waveform=Square(amplitude=1, duration=10))
    qp.wait("flux_line_q0_bus", 10)
    qp.set_offset("flux_line_q0_bus", 0)
    return qp


@pytest.fixture(name="qp_plat_draw_qrm")
def fixture_qp_plat_draw_qrm() -> QProgram:
    qp = QProgram()
    qp.play(bus="feedline_input_output_bus", waveform=Square(amplitude=1, duration=10))
    qp.wait("feedline_input_output_bus", 10)
    return qp


@pytest.fixture(name="platform")
def fixture_platform():
    return build_platform(runcard=Galadriel.runcard)



@pytest.fixture(name="qp_play_interrupted_by_another_play")
def fixture_play_interrupted_by_another_play():
    qp = QProgram()
    qp.qblox.play("drive",Square(1,10),7)
    qp.qblox.play("drive",Square(-1,10),1)
    qp.wait("drive", 5)
    return qp

@pytest.fixture(name="qp_not_sub")
def fixture_not_sub():
    qp = QProgram()
    frequency = qp.variable(label="drive", domain=Domain.Frequency)
    FREQ_START = -100e6
    FREQ_STOP = -200e6
    FREQ_STEP = -50e6
    with qp.for_loop(frequency, FREQ_START, FREQ_STOP, FREQ_STEP):
        qp.set_frequency(bus="drive", frequency=frequency)
        qp.play(bus="drive", waveform=Square(amplitude=1, duration=10))
        qp.wait("drive", 10)
    return qp

@pytest.fixture(name="qp_real_time")
def fixture_qp_real_time() -> QProgram:
    qp = QProgram()
    weights_shape = Square(amplitude=1, duration=20)
    qp.qblox.play(bus="feedline_input_output_bus_1", waveform=Square(amplitude=1, duration=10),wait_time= 20)
    qp.qblox.play(bus="feedline_input_output_bus_1", waveform=Square(amplitude=1, duration=60),wait_time = 20)
    qp.qblox.acquire(bus="feedline_input_output_bus_1", weights= IQPair(I=weights_shape, Q=weights_shape))
    qp.qblox.acquire(bus="feedline_input_output_bus_1", weights= IQPair(I=weights_shape, Q=weights_shape))
    return qp

@pytest.fixture(name="qp_acquire")
def fixture_qp_acquire() -> QProgram:
    qp = QProgram()
    weights_shape = Square(amplitude=1, duration=20)
    square_wf = Square(1,10)
    qp.qblox.play("feedline_input_output_bus_1",square_wf,2)
    qp.qblox.acquire(bus="feedline_input_output_bus_1", weights= IQPair(I=weights_shape, Q=weights_shape))
    return qp

class TestQBloxDraw:
    def test_parsing(self, parsing: QProgram):
        compiler = QbloxCompiler()
        draw = QbloxDraw()
        sequences, _ = compiler.compile(qprogram=parsing)
        pio.renderers.default = "json"
        parsing = draw._parse_program(sequences)
        expected_parsing = [
            ("move", "3, R0", (), 0),
            ("move", "400000000, R1", (), 1),
            ("set_freq", "R1", ("loop_0",), 2),
            ("set_freq", "R1", ("loop_0",), 3),
            ("play", "0, 1, 10", ("loop_0",), 4),
            ("wait", "10", ("loop_0",), 5),
            ("add", "R1, 200000000, R1", ("loop_0",), 6),
            ("loop", "R0, @loop_0", ("loop_0",), 7),
            ("nop", "2", (), 8),
        ]
        assert parsing["drive"]["program"]["main"] == expected_parsing

    def test_qp_draw(self, qp_draw: QProgram):
        expected_results = {
        "drive I": [ 7.07106781e-01,  5.72061403e-01,  2.18508012e-01, -2.18508012e-01,
         -5.72061403e-01,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00,  7.07106781e-01,  5.72061403e-01,
          2.18508012e-01, -2.18508012e-01, -5.72061403e-01, -7.07106781e-01,
         -5.72061403e-01, -2.18508012e-01,  2.18508012e-01,  5.72061403e-01,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00, -7.07106781e-01, -5.72061403e-01, -2.18508012e-01,
          2.18508012e-01,  5.72061403e-01, -7.07106781e-01, -4.15626938e-01,
          2.18508012e-01,  6.72498512e-01,  5.72061403e-01,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
          7.07106781e-01,  4.15626938e-01, -2.18508012e-01, -6.72498512e-01,
         -5.72061403e-01, -2.42511464e-15,  5.72061403e-01,  6.72498512e-01,
          2.18508012e-01, -4.15626938e-01,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  1.72753526e-16,
         -5.72061403e-01, -6.72498512e-01, -2.18508012e-01,  4.15626938e-01,
          7.07106781e-01,  2.18508012e-01, -5.72061403e-01, -5.72061403e-01,
          2.18508012e-01,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00,  7.07106781e-01,  2.18508012e-01,
         -5.72061403e-01, -5.72061403e-01,  2.18508012e-01,  7.07106781e-01,
          2.18508012e-01, -5.72061403e-01, -5.72061403e-01,  2.18508012e-01,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  7.07106781e-01,  2.18508012e-01, -5.72061403e-01,
         -5.72061403e-01,  2.18508012e-01],
        "drive Q": [ 0.00000000e+00,  4.15626938e-01,  6.72498512e-01,  6.72498512e-01,
          4.15626938e-01,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00, -1.73191211e-16,  4.15626938e-01,
          6.72498512e-01,  6.72498512e-01,  4.15626938e-01,  1.51586078e-15,
         -4.15626938e-01, -6.72498512e-01, -6.72498512e-01, -4.15626938e-01,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  1.68905200e-15, -4.15626938e-01, -6.72498512e-01,
         -6.72498512e-01, -4.15626938e-01,  3.29150838e-15, -5.72061403e-01,
         -6.72498512e-01, -2.18508012e-01,  4.15626938e-01,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
         -1.03914727e-15,  5.72061403e-01,  6.72498512e-01,  2.18508012e-01,
         -4.15626938e-01, -7.07106781e-01, -4.15626938e-01,  2.18508012e-01,
          6.72498512e-01,  5.72061403e-01,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  7.07106781e-01,
          4.15626938e-01, -2.18508012e-01, -6.72498512e-01, -5.72061403e-01,
         -1.21268863e-14,  6.72498512e-01,  4.15626938e-01, -4.15626938e-01,
         -6.72498512e-01,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00, -2.42467696e-15,  6.72498512e-01,
          4.15626938e-01, -4.15626938e-01, -6.72498512e-01, -7.62216404e-15,
          6.72498512e-01,  4.15626938e-01, -4.15626938e-01, -6.72498512e-01,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00, -1.80171382e-14,  6.72498512e-01,  4.15626938e-01,
         -4.15626938e-01, -6.72498512e-01]}
        
        pio.renderers.default = "json"
        figure = qp_draw.draw(averages_displayed=True)
        np.testing.assert_allclose(figure.data[0].y, np.array(expected_results[figure.data[0].name]), rtol=1e-2, atol=1e-12)
        np.testing.assert_allclose(figure.data[1].y, np.array(expected_results[figure.data[1].name]), rtol=1e-2, atol=1e-12)

    def test_qp_draw_with_timeout(self, qp_draw_with_time_window: QProgram):
        expected_results = {
        "readout_q13_bus I": [0.        , 0.        , 0.        , 0.        , 0.        ,
         0.        , 0.        , 0.        , 0.        , 0.        ,
         0.35355339, 0.35355339, 0.35355339, 0.35355339, 0.35355339,
         0.        , 0.        , 0.        , 0.        , 0.        ,
         0.        , 0.        , 0.        , 0.        , 0.        ,
         0.        , 0.        , 0.        , 0.        , 0.        ,
         0.        , 0.        , 0.        , 0.        , 0.        ,
         0.        , 0.        , 0.        , 0.        , 0.        ,
         0.        , 0.        , 0.        , 0.        ],

        "readout_q13_bus Q": [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
         0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
         0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]}

        pio.renderers.default = "json"
        figure = qp_draw_with_time_window.draw(averages_displayed = True, time_window=40)
        np.testing.assert_allclose(figure.data[0].y, np.array(expected_results[figure.data[0].name]), rtol=1e-2, atol=1e-12)
        np.testing.assert_allclose(figure.data[1].y, np.array(expected_results[figure.data[1].name]), rtol=1e-2, atol=1e-12)

    def test_qp_draw_with_timeout_nested_loop(self, qp_draw_with_time_window_nested_loop: QProgram):
        expected_results={
        "drive I": [0.        , 0.        , 0.        , 0.        , 0.        ,
         0.        , 0.        , 0.        , 0.        , 0.        ,
         0.        , 0.        , 0.        , 0.        , 0.        ,
         0.23569507, 0.23569507, 0.23569507, 0.23569507, 0.23569507,
         0.23569507, 0.23569507, 0.23569507, 0.23569507, 0.23569507],

        "drive Q": [0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
         0., 0., 0., 0., 0., 0., 0., 0.]}
        pio.renderers.default = "json"
        figure = qp_draw_with_time_window_nested_loop.draw(time_window=20)
        np.testing.assert_allclose(figure.data[0].y, np.array(expected_results[figure.data[0].name]), rtol=1e-2, atol=1e-12)
        np.testing.assert_allclose(figure.data[1].y, np.array(expected_results[figure.data[1].name]), rtol=1e-2, atol=1e-12)

    def test_qp_draw_with_timeout_no_loop(self, qp_draw_with_timeout_no_loop: QProgram):
        expected_results = {
        "drive I": [0., 0., 0., 0., 0., 0., 0., 0., 0., 0.],

        "drive Q": [0., 0., 0., 0., 0., 0., 0., 0., 0., 0.]}

        pio.renderers.default = "json"
        figure = qp_draw_with_timeout_no_loop.draw(time_window=10)
        np.testing.assert_allclose(figure.data[0].y, np.array(expected_results[figure.data[0].name]), rtol=1e-2, atol=1e-12)
        np.testing.assert_allclose(figure.data[1].y, np.array(expected_results[figure.data[1].name]), rtol=1e-2, atol=1e-12)

    def test_platform_draw_qcmrf(self, qp_plat_draw_qcmrf: QProgram, platform: Platform):
        expected_results = {
        "drive_line_q1_bus I": [0.20155136, 0.20075692, 0.19967336, 0.19871457, 0.19824677,
       0.19844864, 0.19924308, 0.20032664, 0.20128543, 0.20175323,
       0.2       , 0.2       , 0.2       , 0.2       , 0.2       ,
       0.2       , 0.2       , 0.2       , 0.2       , 0.2       ],
        "drive_line_q1_bus Q": [0.07084751, 0.07159752, 0.07173733, 0.07121354, 0.07022622,
       0.06915249, 0.06840248, 0.06826267, 0.06878646, 0.06977378,
       0.07      , 0.07      , 0.07      , 0.07      , 0.07      ,
       0.07      , 0.07      , 0.07      , 0.07      , 0.07      ]}
        pio.renderers.default = "json"
        figure = platform.draw(qp_plat_draw_qcmrf)
        np.testing.assert_allclose(figure.data[0].y, np.array(expected_results[figure.data[0].name]), rtol=1e-2, atol=1e-12)
        np.testing.assert_allclose(figure.data[1].y, np.array(expected_results[figure.data[1].name]), rtol=1e-2, atol=1e-12)

    def test_platform_draw_qcmrf_offset(self, qp_plat_draw_qcmrf_offset: QProgram, platform: Platform):
        expected_results = {
        "drive_line_q1_bus I": [ 1.08562427,  0.39696727, -0.36692454, -0.91427044, -1.0360029 ,
       -0.68562427,  0.00303273,  0.76692454,  1.31427044,  1.4360029 ,
        1.0838565 ,  0.39553711, -0.36747081, -0.91372416, -1.03457275,
       -0.6838565 ,  0.00446289,  0.76747081,  1.31372416,  1.43457275],
        "drive_line_q1_bus Q": [ 0.9538565 ,  1.30561181,  1.18540541,  0.63915205, -0.12449805,
       -0.8138565 , -1.16561181, -1.04540541, -0.49915205,  0.26449805,
        0.9538565 ,  1.30457275,  1.18372416,  0.63747081, -0.12553711,
       -0.8138565 , -1.16457275, -1.04372416, -0.49747081,  0.26553711],
        "drive_line_q2_bus I": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
        "drive_line_q2_bus Q": [0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6]}
        pio.renderers.default = "json"
        figure = platform.draw(qp_plat_draw_qcmrf_offset)
        np.testing.assert_allclose(figure.data[0].y, np.array(expected_results[figure.data[0].name]), rtol=1e-2, atol=1e-12)
        np.testing.assert_allclose(figure.data[1].y, np.array(expected_results[figure.data[1].name]), rtol=1e-2, atol=1e-12)
        np.testing.assert_allclose(figure.data[2].y, np.array(expected_results[figure.data[2].name]), rtol=1e-2, atol=1e-12)
        np.testing.assert_allclose(figure.data[3].y, np.array(expected_results[figure.data[3].name]), rtol=1e-2, atol=1e-12)

    def test_platform_draw_qcm(self, qp_plat_draw_qcm_flux: QProgram, platform: Platform):
        expected_data_draw_i = [
            2.5,
            2.5,
            2.5,
            2.5,
            2.5,
            2.5,
            2.5,
            2.5,
            2.5,
            2.5,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ]
        pio.renderers.default = "json"
        figure = platform.draw(qp_plat_draw_qcm_flux)
        np.testing.assert_allclose(figure.data[0].y, expected_data_draw_i, rtol=1e-9, atol=1e-12)
        assert len(figure.data) == 1

    def test_platform_draw_qcm_offset(self, qp_plat_draw_qcm_flux_offset: QProgram, platform: Platform):
        expected_data_draw_i = [
            2.5,
            2.5,
            2.5,
            2.5,
            2.5,
            2.5,
            2.5,
            2.5,
            2.5,
            2.5,
            1.24996185,
            1.24996185,
            1.24996185,
            1.24996185,
            1.24996185,
            1.24996185,
            1.24996185,
            1.24996185,
            1.24996185,
            1.24996185,
        ]
        pio.renderers.default = "json"
        figure = platform.draw(qp_plat_draw_qcm_flux_offset)
        np.testing.assert_allclose(figure.data[0].y, expected_data_draw_i, rtol=1e-2, atol=1e-12)
        assert len(figure.data) == 1

    def test_get_value(self):
        draw = QbloxDraw()
        register = {}
        register["avg_no_loop"] = 1
        pio.renderers.default = "json"
        assert draw._get_value(None, register) is None

    def test_qp_plat_draw_qrm(self, qp_plat_draw_qrm: QProgram, platform: Platform):
        expected_data_draw_i = [
            0.5,
            0.5,
            0.5,
            0.5,
            0.5,
            0.5,
            0.5,
            0.5,
            0.5,
            0.5,
            0.123,
            0.123,
            0.123,
            0.123,
            0.123,
            0.123,
            0.123,
            0.123,
            0.123,
            0.123,
        ]
        pio.renderers.default = "json"
        figure = platform.draw(qp_plat_draw_qrm)
        np.testing.assert_allclose(
            figure.data[0].y, expected_data_draw_i, rtol=1e-2, atol=1e-12
        )
        assert len(figure.data) == 1


    @pytest.mark.qm
    def test_platform_draw_quantum_machine_raises_error(
        self, qp_quantum_machine: QProgram, platform_quantum_machines: Platform
    ):
        pio.renderers.default = "json"
        with pytest.raises(NotImplementedError) as exc_info:
            platform_quantum_machines.draw(qp_quantum_machine)
    
        # Optionally check the error message
        assert str(exc_info.value) == "The drawing feature is currently only supported for QBlox."


    def test_play_interrupted_by_another_play(self, qp_play_interrupted_by_another_play: QProgram):
        expected_data_draw_i = [ 0.70710678,  0.70710678,  0.70710678,  0.70710678,  0.70710678,
                  0.70710678,  0.70710678, -0.70710678, -0.70710678, -0.70710678,
                 -0.70710678, -0.70710678, -0.70710678, -0.70710678, -0.70710678,
                 -0.70710678, -0.70710678]
        compiler = QbloxCompiler()
        qblox_draw = QbloxDraw()
        results = compiler.compile(qp_play_interrupted_by_another_play)
        pio.renderers.default = "json"
        _, data_draw = qblox_draw.draw(sequencer=results, runcard_data= None)
        np.testing.assert_allclose(data_draw["drive"][0], expected_data_draw_i, rtol=1e-2, atol=1e-12)

    def test_qp_not_sub(self, qp_not_sub: QProgram):
        expected_data_draw_i = [ 7.07106781e-01,  5.72061403e-01,  2.18508014e-01, -2.18508009e-01,
         -5.72061400e-01, -7.07106781e-01, -5.72061407e-01, -2.18508020e-01,
          2.18508004e-01,  5.72061397e-01,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
          7.07106781e-01,  4.15626957e-01, -2.18507989e-01, -6.72498504e-01,
         -5.72061418e-01, -2.77680190e-08,  5.72061386e-01,  6.72498521e-01,
          2.18508042e-01, -4.15626912e-01,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
          7.07106781e-01,  2.18508056e-01, -5.72061375e-01, -5.72061431e-01,
          2.18507966e-01,  7.07106781e-01,  2.18508061e-01, -5.72061372e-01,
         -5.72061434e-01,  2.18507960e-01,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00]
        expected_data_draw_q = [ 0.00000000e+00, -4.15626937e-01, -6.72498511e-01, -6.72498513e-01,
         -4.15626941e-01, -5.55360364e-09,  4.15626932e-01,  6.72498510e-01,
          6.72498515e-01,  4.15626946e-01,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
          2.22144147e-08, -5.72061389e-01, -6.72498520e-01, -2.18508037e-01,
          4.15626916e-01,  7.07106781e-01,  4.15626961e-01, -2.18507984e-01,
         -6.72498502e-01, -5.72061422e-01,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
          4.44288298e-08, -6.72498498e-01, -4.15626976e-01,  4.15626899e-01,
          6.72498527e-01,  4.99824354e-08, -6.72498496e-01, -4.15626980e-01,
          4.15626895e-01,  6.72498529e-01,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
          0.00000000e+00,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00]
        compiler = QbloxCompiler()
        qblox_draw = QbloxDraw()
        results = compiler.compile(qp_not_sub)
        pio.renderers.default = "json"
        _, data_draw = qblox_draw.draw(sequencer=results, runcard_data= None)
        np.testing.assert_allclose(data_draw["drive"][0], expected_data_draw_i, rtol=1e-2, atol=1e-12)
        np.testing.assert_allclose(data_draw["drive"][1], expected_data_draw_q, rtol=1e-2, atol=1e-12)

    def test_qp_real_time(self, qp_real_time: QProgram, platform: Platform):
        expected_results = {
        "feedline_input_output_bus_1 I": [0.12335355, 0.12335077, 0.12334245, 0.12332873, 0.12330982,
         0.12328603, 0.12325773, 0.12322536, 0.12318944, 0.12315054,
         0.123     , 0.123     , 0.123     , 0.123     , 0.123     ,
         0.123     , 0.123     , 0.123     , 0.123     , 0.123     ,
         0.12271397, 0.12269018, 0.12267127, 0.12265755, 0.12264923,
         0.12264645, 0.12264923, 0.12265755, 0.12267127, 0.12269018,
         0.12271397, 0.12274227, 0.12277464, 0.12281056, 0.12284946,
         0.12289075, 0.12293375, 0.1229778 , 0.1230222 , 0.12306625,
         0.12310925, 0.12315054, 0.12318944, 0.12322536, 0.12325773,
         0.12328603, 0.12330982, 0.12332873, 0.12334245, 0.12335077,
         0.12335355, 0.12335077, 0.12334245, 0.12332873, 0.12330982,
         0.12328603, 0.12325773, 0.12322536, 0.12318944, 0.12315054,
         0.12310925, 0.12306625, 0.1230222 , 0.1229778 , 0.12293375,
         0.12289075, 0.12284946, 0.12281056, 0.12277464, 0.12274227,
         0.12271397, 0.12269018, 0.12267127, 0.12265755, 0.12264923,
         0.12264645, 0.12264923, 0.12265755, 0.12267127, 0.12269018],
        
        "feedline_input_output_bus_1 Q":  [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
         0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
         0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
         0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
         0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
         0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
         0.5, 0.5]}
        pio.renderers.default = "json"
        figure = platform.draw(qp_real_time)

        np.testing.assert_allclose(figure.data[0].y, np.array(expected_results[figure.data[0].name]), rtol=1e-2, atol=1e-12)
        np.testing.assert_allclose(figure.data[1].y, np.array(expected_results[figure.data[1].name]), rtol=1e-2, atol=1e-12)

    def test_call_handlers_raises_on_unknown_instruction(self):
        draw = QbloxDraw()
        
        # Simulate minimal valid input for internal method
        program_line = ("badcmd", "")  # unknown Q1ASM instruction
        param = {
            "classical_time_counter": 0,
            "real_time_counter": 0,
            "intermediate_frequency": [0],
            "phase": [0],
            "q1asm_offset_i": [0],
            "q1asm_offset_q": [0],
            "intermediate_frequency_new": False,
            "phase_new": False,
            "q1asm_offset_i_new": False,
            "q1asm_offset_q_new": False,
            "acquiring_status": np.array([0]),
            "acquire_idx": 0,
            "play_idx": 0,
            "max_voltage": 1,
            "hardware_modulation": True,
            "gain_i": 1,
            "gain_q": 1
        }
        register = {}
        _, data_draw = [[0.0], [0.0]]
        waveform_seq = []

        with pytest.raises(NotImplementedError, match=r'The Q1ASM operation "badcmd" is not implemented in the plotter yet. Please contact someone from QHC.'):
            draw._call_handlers(program_line, param, register, data_draw, waveform_seq)

    def test_drawer_hardware_loop_time_raises_error(
        self, platform: Platform
    ):

        drive_wf = IQPair(I=Square(amplitude=1.0, duration=40), Q=Square(amplitude=0.0, duration=40))
        qprogram = QProgram()
        
        time=qprogram.variable(label="time",domain=Domain.Time)
        with qprogram.for_loop(variable=time, start=10, stop=500, step=10):
            qprogram.play(bus="drive_line_q0_bus", waveform=drive_wf)
            qprogram.play(bus="drive_line_q1_bus", waveform=drive_wf)
            qprogram.wait(bus="drive_line_q1_bus", duration=time)
            qprogram.sync()

        with pytest.raises(NotImplementedError) as exc_info:
            platform.draw(qprogram)
    
        assert str(exc_info.value) == "QbloxDraw does not support hardware time-domain loops at the moment."

    def test_platform_acquire(self,platform: Platform, qp_acquire: QProgram):
        expected_results = {
        "feedline_input_output_bus_1 I": [0.12335355, 0.12335077, 0.12334245, 0.12332873, 0.12330982, 0.12328603,
                 0.12325773, 0.12322536, 0.12318944, 0.12315054, 0.123     , 0.123     ,
                 0.123     , 0.123     , 0.123     , 0.123     , 0.123     , 0.123     ,
                 0.123     , 0.123     , 0.123     , 0.123     , 0.123     , 0.123     ],
        
        "feedline_input_output_bus_1 Q":  [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
                 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]}
        pio.renderers.default = "json"
        figure = platform.draw(qp_acquire)

        np.testing.assert_allclose(figure.data[0].y, np.array(expected_results[figure.data[0].name]), rtol=1e-2, atol=1e-12)
        np.testing.assert_allclose(figure.data[1].y, np.array(expected_results[figure.data[1].name]), rtol=1e-2, atol=1e-12)

    def test_interrupt_acquire(self):
        """Even though Qililab prevents overlapping acquires, this has been tested and the interruption will be possible if qililab ever allows for it."""

        qblox_draw = QbloxDraw()
        param = {
            "acquiring_status": [1, 1, 1],
            "intermediate_frequency": [10, 20]
        }
        out = qblox_draw._interrupt_acquire(param)
        assert len(out["acquiring_status"]) == len(out["intermediate_frequency"])
        assert out["acquiring_status"] == [1, 1]

