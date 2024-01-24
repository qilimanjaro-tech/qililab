"""Tests for the SystemControl class."""
import re
from unittest.mock import MagicMock

import pytest
from qpysequence import Acquisitions, Program, Sequence, Waveforms, Weights

import qililab as ql
from qililab.instruments import AWG, Instrument, ParameterNotFound
from qililab.instruments.qblox import QbloxModule
from qililab.instruments.rohde_schwarz import SGS100A
from qililab.platform import Platform
from qililab.pulse import Gaussian, Pulse, PulseBusSchedule, PulseEvent, PulseSchedule
from qililab.system_control import SystemControl
from tests.data import Galadriel
from tests.test_utils import build_platform


@pytest.fixture(name="platform")
def fixture_platform() -> Platform:
    """Return Platform object."""
    return build_platform(runcard=Galadriel.runcard)


@pytest.fixture(name="qpysequence")
def fixture_qpysequence() -> Sequence:
    """Return Sequence instance."""
    return Sequence(program=Program(), waveforms=Waveforms(), acquisitions=Acquisitions(), weights=Weights())


@pytest.fixture(name="pulse_schedule")
def fixture_pulse_schedule() -> PulseSchedule:
    """Return PulseSchedule instance."""
    pulse_shape = Gaussian(num_sigmas=4)
    pulse = Pulse(amplitude=1, phase=0, duration=50, frequency=1e9, pulse_shape=pulse_shape)
    pulse_event = PulseEvent(pulse=pulse, start_time=0, qubit=0)
    return PulseSchedule([PulseBusSchedule(timeline=[pulse_event], port="feedline_input")])


@pytest.fixture(name="system_control")
def fixture_system_control(platform: Platform):
    """Fixture that returns an instance of a SystemControl class."""
    settings = {"instruments": ["QRM_0", "rs_1"]}
    return SystemControl(settings=settings, platform_instruments=platform.instruments)


@pytest.fixture(name="system_control_qcm")
def fixture_system_control_qcm(platform: Platform):
    """Fixture that returns an instance of a SystemControl class."""
    settings = {"instruments": ["QCM", "rs_1"]}
    return SystemControl(settings=settings, platform_instruments=platform.instruments)


@pytest.fixture(name="system_control_without_awg")
def fixture_system_control_without_awg(platform: Platform):
    """Fixture that returns an instance of a SystemControl class."""
    settings = {"instruments": ["rs_1"]}
    return SystemControl(settings=settings, platform_instruments=platform.instruments)


class TestInitialization:
    """Unit tests checking the ``SystemControl`` initialization."""

    def test_init(self, system_control: SystemControl):
        """Test initialization."""
        assert isinstance(system_control.settings, SystemControl.SystemControlSettings)
        assert system_control.name.value == "system_control"
        for instrument in system_control.settings.instruments:
            assert isinstance(instrument, Instrument)
        assert not hasattr(system_control.settings, "platform_instruments")

    def test_init_with_a_wrong_instrument_alias_raises_an_error(self, platform: Platform):
        """Test that an error is raised when initializing a SystemControl with an instrument alias that is not
        present in the platform.
        """
        alias = "UnknownInstrument"
        wrong_system_control_settings = {"instruments": [alias]}
        with pytest.raises(
            NameError,
            match=f"The instrument with alias {alias} could not be found within the instruments of the platform",
        ):
            SystemControl(settings=wrong_system_control_settings, platform_instruments=platform.instruments)


@pytest.fixture(name="base_system_control")
def fixture_base_system_control(platform: Platform) -> SystemControl:
    """Load SystemControl.

    Returns:
        SystemControl: Instance of the ControlSystemControl class.
    """
    return platform.buses[0].system_control


class TestMethods:
    """Unit tests checking the ``SystemControl`` methods."""

    def test_iter_method(self, system_control: SystemControl):
        """Test __iter__ method."""
        for instrument in system_control:
            assert isinstance(instrument, Instrument)

    def test_upload_qpysequence(self, system_control: SystemControl, qpysequence: Sequence):
        awg = system_control.instruments[0]
        assert isinstance(awg, AWG)
        awg.device = MagicMock()
        system_control.upload_qpysequence(qpysequence=qpysequence, port="feedline_input")
        for seq_idx in range(awg.num_sequencers):
            # qrm has 2 sequencers and since device is a magic mock, the mock device registers n calls
            #  of sequence no matter the seq_idx, where n is the number of sequencers in the module
            assert awg.device.sequencers[seq_idx].sequence.call_count == 2

    def test_upload_qpysequence_raises_error_when_awg_is_missing(
        self, system_control_without_awg: SystemControl, qpysequence: Sequence
    ):
        """Test that the ``upload`` method raises an error when the system control doesn't have an AWG."""
        with pytest.raises(
            AttributeError,
            match="The system control doesn't have any AWG to upload a qpysequence.",
        ):
            system_control_without_awg.upload_qpysequence(qpysequence=qpysequence, port="feedline_input")

    def test_upload(self, platform: Platform, pulse_schedule: PulseSchedule, system_control: SystemControl):
        """Test upload method."""
        awg = platform.instruments.elements[1]
        assert isinstance(awg, AWG)
        awg.device = MagicMock()
        _ = platform.compile(pulse_schedule, num_avg=1000, repetition_duration=2000, num_bins=1)
        system_control.upload(port=pulse_schedule.elements[0].port)
        for seq_idx in range(awg.num_sequencers):
            assert awg.device.sequencers[seq_idx].sequence.call_count == 1  # device.sequence.to_dict() in upload method

    def test_run_raises_error(self, system_control_without_awg: SystemControl):
        """Test that the ``run`` method raises an error when the system control doesn't have an AWG."""
        with pytest.raises(
            AttributeError,
            match="The system control doesn't have any AWG to run a program",
        ):
            system_control_without_awg.run(port="feedline_input")

    def test_set_parameter_device(self, system_control: SystemControl):
        """Test the ``set_parameter`` method with a Rohde & Schwarz instrument."""
        for instrument in system_control.instruments:
            instrument.device = MagicMock()
        system_control.set_parameter(parameter=ql.Parameter.LO_FREQUENCY, value=1e9, channel_id=0)
        for instrument in system_control.instruments:
            if isinstance(instrument, SGS100A):
                instrument.device.frequency.assert_called_once_with(1e9)  # type: ignore
            else:
                instrument.device.frequency.assert_not_called()  # type: ignore

    def test_set_parameter_no_device(self, system_control_qcm: SystemControl):
        """Test the ``set_parameter`` method with a qblox module without device."""
        system_control_qcm.set_parameter(parameter=ql.Parameter.IF, value=12.0e06, port_id="drive_q0")
        for instrument in system_control_qcm.instruments:
            if isinstance(instrument, QbloxModule):
                assert instrument.awg_sequencers[0].intermediate_frequency == 12.0e06

    def test_set_parameter_error(self, system_control_qcm: SystemControl):
        """Test the ``set_parameter`` method with an invalid parameter and check that it raises an error."""
        param = ql.Parameter.GATE_OPTIONS
        error_string = re.escape(
            f"Could not find parameter {param.value} in the system control {system_control_qcm.name}"
        )
        with pytest.raises(ParameterNotFound, match=error_string):
            system_control_qcm.set_parameter(parameter=param, value=12.0e06, port_id="drive_q0")

    def test_get_parameter_error(self, system_control_qcm: SystemControl):
        """Test the ``get_parameter`` method with an invalid parameter and check that it raises an error."""
        param = ql.Parameter.GATE_OPTIONS
        error_string = re.escape(
            f"Could not find parameter {param.value} in the system control {system_control_qcm.name}"
        )

        with pytest.raises(ParameterNotFound, match=error_string):
            system_control_qcm.get_parameter(parameter=param, port_id="drive_q0")


class TestProperties:  # pylint: disable=too-few-public-methods
    """Unit tests checking the SystemControl attributes and methods"""

    def test_instruments_property(self, system_control: SystemControl):
        """Test instruments property."""
        assert system_control.instruments == system_control.settings.instruments
