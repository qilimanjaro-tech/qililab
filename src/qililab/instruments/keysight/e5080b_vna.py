"""KeySight Vector Network Analyzer E5080B class."""
import time
from dataclasses import dataclass

import numpy as np

from qililab.constants import DEFAULT_TIMEOUT
from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.instruments.vector_network_analyzer import VectorNetworkAnalyzer
from qililab.typings.enums import InstrumentName, Parameter, VNAScatteringParameters, VNASweepModes, VNATriggerModes
from qililab.typings.instruments.keysight_e5080b import E5080BDriver

DEFAULT_NUMBER_POINTS = 1000


@InstrumentFactory.register
class E5080B(VectorNetworkAnalyzer):

    """KeySight Vector Network Analyzer E5080B"""

    name = InstrumentName.KEYSIGHT_E5080B
    device: E5080BDriver

    @dataclass
    class E5080BSettings(VectorNetworkAnalyzer.VectorNetworkAnalyzerSettings):
        """Contains the settings of a specific VectorNetworkAnalyzer.

        Args:
            power (float): Power of the instrument in dBm
            scatering_parameter (str): Scatering parameter of the instrument
            frequency_span (float): Frequency span of the instrument in KHz
            frequency_center (float): Frequency center of the instrument in Hz
            frequency_start (float): Frequency start of the instrument in Hz
            frequency_stop (float): Frequency stop of the instrument in Hz
            if_bandwidth (float): Bandwidth of the instrument in Hz
            averaging_enabled (bool): Whether averaging is enabled or not in the instrument
            trigger_mode (str): Trigger mode of the instrument
            number_points (int): Number of points for sweep
            sweep_mode (str): Sweeping mode of the instrument
            device_timeout (float): Timeout of the instrument in ms
            electrical_delay (float): Electrical delay of the instrument in s
        """

        power: float
        scattering_parameter: VNAScatteringParameters = VNAScatteringParameters.S11
        frequency_span: float | None = None
        frequency_center: float | None = None
        frequency_start: float | None = None
        frequency_stop: float | None = None
        if_bandwidth: float | None = None
        averaging_enabled: bool = False
        number_averages: int = 1
        trigger_mode: VNATriggerModes = VNATriggerModes.INT
        number_points: int = DEFAULT_NUMBER_POINTS
        sweep_mode: VNASweepModes = VNASweepModes.CONT
        device_timeout: float = DEFAULT_TIMEOUT
        electrical_delay: float = 0.0

    settings: E5080BSettings

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool | int, channel_id: int | None = None):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (float | str | bool): new value
            channel_id (int | None): channel identifier of the parameter to update
        """
        if isinstance(value, str):
            self._set_parameter_str(parameter=parameter, value=value)
            return
        if isinstance(value, bool):
            self._set_parameter_bool(parameter=parameter, value=value)
            return
        if isinstance(value, float):
            self._set_parameter_float(parameter=parameter, value=value)
            return
        if isinstance(value, int):
            self._set_parameter_int(parameter=parameter, value=value)
            return
        raise ParameterNotFound(f"Invalid Parameter: {parameter} with type {type(parameter)}")

    def _set_parameter_str(self, parameter: Parameter, value: str):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (str): new value
        """
        if parameter == Parameter.SCATTERING_PARAMETER:
            self.scattering_parameter = value
            return
        if parameter == Parameter.TRIGGER_MODE:
            self.settings.trigger_mode = VNATriggerModes(value)
            return
        if parameter == Parameter.SWEEP_MODE:
            self.sweep_mode = VNASweepModes(value)
            return

        raise ParameterNotFound(f"Invalid Parameter: {parameter}")

    def _set_parameter_bool(self, parameter: Parameter, value: bool):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (bool): new value
        """
        if parameter == Parameter.AVERAGING_ENABLED:
            self.averaging_enabled = value
            return

        raise ParameterNotFound(f"Invalid Parameter: {parameter}")

    def _set_parameter_float(
        self,
        parameter: Parameter,
        value: float,
    ):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (float): new value
        """

        if parameter == Parameter.POWER:
            self.power = value
            return
        if parameter == Parameter.FREQUENCY_SPAN:
            self.frequency_span = value
            return
        if parameter == Parameter.FREQUENCY_CENTER:
            self.frequency_center = value
            return
        if parameter == Parameter.FREQUENCY_START:
            self.frequency_start = value
            return
        if parameter == Parameter.FREQUENCY_STOP:
            self.frequency_stop = value
            return
        if parameter == Parameter.IF_BANDWIDTH:
            self.if_bandwidth = value
            return
        if parameter == Parameter.DEVICE_TIMEOUT:
            self.device_timeout = value
            return
        if parameter == Parameter.ELECTRICAL_DELAY:
            self.electrical_delay = value
            return

        raise ParameterNotFound(f"Invalid Parameter: {parameter}")

    def _set_parameter_int(self, parameter: Parameter, value: int):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (int): new value
        """

        if parameter == Parameter.NUMBER_AVERAGES:
            self.number_averages = value
            return

        if parameter == Parameter.NUMBER_POINTS:
            self.number_points = value
            return

        raise ParameterNotFound(f"Invalid Parameter: {parameter}")

    @property
    def power(self):
        """VectorNetworkAnalyzer 'power' property.

        Returns:
            float: settings.power
        """
        return self.settings.power

    @power.setter
    def power(self, value: float, channel=1, port=1):
        """sets the power in dBm"""
        self.settings.power = value
        power = f"{self.settings.power:.1f}"
        self.send_command(f"SOUR{channel}:POW{port}", power)

    @property
    def scattering_parameter(self):
        """VectorNetworkAnalyzer 'scattering_parameter' property.

        Returns:
            str: settings.scattering_parameter.
        """
        return self.settings.scattering_parameter

    @scattering_parameter.setter
    def scattering_parameter(self, value: str, channel=1):
        """sets the scattering parameter"""
        if value in {"S11", "S12", "S21", "S22"}:
            self.settings.scattering_parameter = VNAScatteringParameters(value)
            scat_par = self.settings.scattering_parameter.value
            self.send_command(f"CALC1:MEAS{channel}:PAR", scat_par)
            return
        raise ValueError(f"Invalid swescattering parameter value: {value}")

    @property
    def frequency_span(self):
        """VectorNetworkAnalyzer 'frequency_span' property.

        Returns:
            float: settings.frequency_span.
        """
        return self.settings.frequency_span

    @frequency_span.setter
    def frequency_span(self, value: float, channel=1):
        """sets the frequency span in kHz"""
        self.settings.frequency_span = value
        freq = str(self.settings.frequency_span)
        self.send_command(f"SENS{channel}:FREQ:SPAN", freq)

    @property
    def frequency_center(self):
        """VectorNetworkAnalyzer 'frequency_center' property.

        Returns:
            float: settings.frequency_center.
        """
        return self.settings.frequency_center

    @frequency_center.setter
    def frequency_center(self, value: float, channel=1):
        """sets the frequency center"""
        self.settings.frequency_center = value
        freq = str(self.settings.frequency_center)
        self.send_command(f"SENS{channel}:FREQ:CENT", freq)

    @property
    def frequency_start(self):
        """VectorNetworkAnalyzer 'frequency_start' property.

        Returns:
            float: settings.frequency_start.
        """
        return self.settings.frequency_start

    @frequency_start.setter
    def frequency_start(self, value: float, channel=1):
        """sets the frequency start"""
        self.settings.frequency_start = value
        freq = str(self.settings.frequency_start)
        self.send_command(f"SENS{channel}:FREQ:STAR", freq)

    @property
    def frequency_stop(self):
        """VectorNetworkAnalyzer 'frequency_stop' property.

        Returns:
            float: settings.frequency_stop.
        """
        return self.settings.frequency_stop

    @frequency_stop.setter
    def frequency_stop(self, value: float, channel=1):
        """sets the frequency stop in Hz"""
        self.settings.frequency_stop = value
        freq = str(self.settings.frequency_stop)
        self.send_command(f"SENS{channel}:FREQ:STOP", freq)

    @property
    def if_bandwidth(self):
        """VectorNetworkAnalyzer 'if_bandwidth' property.

        Returns:
            float: settings.if_bandwidth.
        """
        return self.settings.if_bandwidth

    @if_bandwidth.setter
    def if_bandwidth(self, value: float, channel=1):
        """sets the if bandwidth in Hz"""
        self.settings.if_bandwidth = value
        bandwidth = str(self.settings.if_bandwidth)
        self.send_command(f"SENS{channel}:BWID", bandwidth)

    @property
    def averaging_enabled(self):
        """VectorNetworkAnalyzer 'averaging_enabled' property.

        Returns:
            bool: settings.averaging_enabled.
        """
        return self.settings.averaging_enabled

    @averaging_enabled.setter
    def averaging_enabled(self, value: bool):
        """sets the averaging enabled"""
        self.settings.averaging_enabled = value
        self._average_state(state=self.settings.averaging_enabled)

    @property
    def number_averages(self):
        """VectorNetworkAnalyzer 'number_averages' property.

        Returns:
            int: settings.number_averages.
        """
        return self.settings.number_averages

    @number_averages.setter
    def number_averages(self, value: int, channel=1):
        """sets the number averages"""
        self.settings.number_averages = value
        self._average_count(count=str(self.settings.number_averages), channel=channel)

    @property
    def trigger_mode(self):
        """VectorNetworkAnalyzer 'trigger_mode' property.

        Returns:
            str: settings.trigger_mode.
        """
        return self.settings.trigger_mode

    @property
    def number_points(self):
        """VectorNetworkAnalyzer 'number_points' property.

        Returns:
            int: settings.number_points.
        """
        return self.settings.number_points

    @number_points.setter
    def number_points(self, value: int):
        """sets the number of points for sweep"""
        self.settings.number_points = value
        points = str(self.settings.number_points)
        self.send_command(":SENS1:SWE:POIN", points)

    @property
    def sweep_mode(self):
        """VectorNetworkAnalyzer'sweep_mode' property.

        Returns:mode
            str: settings.sweep_mode.
        """
        return self.settings.sweep_mode

    @sweep_mode.setter
    def sweep_mode(self, value: str, channel=1):
        """
        Sets the sweep mode

        Input:
            mode (str) : Sweep mode: 'hold', 'cont', single' and 'group'
        """
        if value in {"hold", "cont", "group", "single"}:
            self.settings.sweep_mode = VNASweepModes(value)
            mode = self.settings.sweep_mode.name
            self.send_command(f"SENS{channel}:SWE:MODE", mode)
            return
        raise ValueError(f"Invalid sweep mode value: {value}")

    @property
    def device_timeout(self):
        """VectorNetworkAnalyzer 'device_timeout' property.

        Returns:
            float: settings.device_timeout.
        """
        return self.settings.device_timeout

    @device_timeout.setter
    def device_timeout(self, value: float):
        """sets the device timeout in mili seconds"""
        self.settings.device_timeout = value

    @property
    def electrical_delay(self):
        """VectorNetworkAnalyzer 'electrical_delay' property.

        Returns:
            float: settings.electrical_delay.
        """
        return self.settings.electrical_delay

    @electrical_delay.setter
    def electrical_delay(self, value: float):
        """
        Set electrical delay in channel 1

        Input:
            value (str) : Electrical delay in ns
                example: value = '100E-9' for 100ns
        """
        self.settings.electrical_delay = value
        etime = f"{self.settings.electrical_delay:.12f}"
        self.send_command("SENS1:CORR:EXT:PORT1:TIME", etime)

    def _get_sweep_mode(self, channel=1):
        """Return the current sweep mode."""
        return str(self.send_query(f":SENS{channel}:SWE:MODE?")).rstrip()

    def _get_trace(self, channel=1, trace=1):
        """Get the data of the current trace."""
        self.send_command(command="FORM:DATA", arg="REAL,32")
        self.send_command(command="FORM:BORD", arg="SWAPPED")  # SWAPPED
        data = self.send_binary_query(f"CALC{channel}:MEAS{trace}:DATA:SDAT?")
        datareal = np.array(data[::2])  # Elements from data starting from 0 iterating by 2
        dataimag = np.array(data[1::2])  # Elements from data starting from 1 iterating by 2

        return datareal + 1j * dataimag

    def _average_state(self, state, channel=1):
        """Set status of Average."""
        if state:
            self.send_command(f"SENS{channel}:AVER:STAT", "ON")
        else:
            self.send_command(f"SENS{channel}:AVER:STAT", "OFF")

    def _average_count(self, count, channel):
        """Set the average count"""
        self.send_command(f"SENS{channel}:AVER:COUN", count)
        self.send_command(command=f":SENS{channel}:AVER:CLE", arg="")

    def _set_count(self, count: str, channel=1):
        """
        Sets the trigger count (groups)
        Input:
            count (str) : Count number
        """
        self.send_command(f"SENS{channel}:SWE:GRO:COUN", count)

    def _pre_measurement(self):
        """
        Set everything needed for the measurement
        Averaging has to be enabled.
        Trigger count is set to number of averages
        """
        if not self.averaging_enabled:
            self.averaging_enabled = True
            self.number_averages = 1
        self._set_count(str(self.settings.number_averages))

    def _start_measurement(self):
        """
        This function is called at the beginning of each single measurement in the spectroscopy script.
        Also, the averages need to be reset.
        """
        self.average_clear()
        self.sweep_mode = "group"

    def _wait_until_ready(self, period=0.25) -> bool:
        """Waiting function to wait until VNA is ready."""
        timelimit = time.time() + self.device_timeout
        while time.time() < timelimit:
            if self.ready():
                return True
            time.sleep(period)
        return False

    def average_clear(self, channel=1):
        """Clears the average buffer."""
        self.send_command(command=f":SENS{channel}:AVER:CLE", arg="")

    def get_frequencies(self):
        """return freqpoints"""
        return np.array(self.send_binary_query("SENS:X?"))

    def ready(self) -> bool:
        """
        This is a proxy function.
        Returns True if the VNA is on HOLD after finishing the required number of averages.
        """
        try:  # the VNA sometimes throws an error here, we just ignore it
            return self._get_sweep_mode() == "HOLD"
        except Exception:
            return False

    def release(self, channel=1):
        """Bring the VNA back to a mode where it can be easily used by the operator."""
        self.settings.sweep_mode = VNASweepModes("cont")
        self.send_command(f"SENS{channel}:SWE:MODE", self.settings.sweep_mode.value)

    def autoscale(self):
        """Autoscale"""
        self.send_command(command="DISP:WIND:TRAC:Y:AUTO")

    def read_tracedata(self):
        """
        Return the current trace data.
        It already releases the VNA after finishing the required number of averages.
        """
        self._pre_measurement()
        self._start_measurement()
        if self._wait_until_ready():
            trace = self._get_trace()
            self.release()
            return trace
        raise TimeoutError("Timeout waiting for trace data")
