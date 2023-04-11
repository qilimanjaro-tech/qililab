"""KeySight Vector Network Analyzer E5080B class."""
import time
from dataclasses import dataclass

import numpy as np

from qililab.instruments.instrument import ParameterNotFound
from qililab.instruments.utils import InstrumentFactory
from qililab.instruments.vector_network_analyzer import VectorNetworkAnalyzer
from qililab.typings.enums import InstrumentName, Parameter, VNAScatteringParameters, VNASweepModes, VNATriggerModes
from qililab.typings.instruments.keysight_e5080b import E5080BDriver


@InstrumentFactory.register
class E5080B(VectorNetworkAnalyzer):

    """KeySight Vector Network Analyzer E5080B"""

    name = InstrumentName.KEYSIGHT_E5080B
    device: E5080BDriver

    @dataclass
    class E5080BSettings(VectorNetworkAnalyzer.VectorNetworkAnalyzerSettings):
        """Contains the settings of a specific VectorNetworkAnalyzer.

        Args:
            sweep_mode (str): Sweeping mode of the instrument
        """

        sweep_mode: VNASweepModes = VNASweepModes.CONT

    settings: E5080BSettings

    def _set_parameter_str(self, parameter: Parameter, value: str):
        """Set instrument settings parameter to the corresponding value

        Args:
            parameter (Parameter): settings parameter to be updated
            value (str): new value
        """
        if parameter == Parameter.SCATTERING_PARAMETER:
            self.scattering_parameter = VNAScatteringParameters(value)
            return
        if parameter == Parameter.TRIGGER_MODE:
            self.settings.trigger_mode = VNATriggerModes(value)
            return
        if parameter == Parameter.SWEEP_MODE:
            self.sweep_mode = VNASweepModes(value)
            return

        raise ParameterNotFound(f"Invalid Parameter: {parameter}")

    @VectorNetworkAnalyzer.power.setter  # type: ignore
    def power(self, value: float, channel=1, port=1):
        """sets the power in dBm"""
        self.settings.power = value
        power = f"{self.settings.power:.1f}"
        self.send_command(f"SOUR{channel}:POW{port}", power)

    @VectorNetworkAnalyzer.scattering_parameter.setter  # type: ignore
    def scattering_parameter(self, value: str, channel=1):
        """sets the scattering parameter"""
        if value in {"S11", "S12", "S21", "S22"}:
            self.settings.scattering_parameter = VNAScatteringParameters(value)
            scat_par = self.settings.scattering_parameter.value
            self.send_command(f"CALC1:MEAS{channel}:PAR", scat_par)
            return
        raise ValueError(f"Invalid swescattering parameter value: {value}")

    @VectorNetworkAnalyzer.frequency_span.setter  # type: ignore
    def frequency_span(self, value: float, channel=1):
        """sets the frequency span in kHz"""
        self.settings.frequency_span = value
        freq = str(self.settings.frequency_span)
        self.send_command(f"SENS{channel}:FREQ:SPAN", freq)

    @VectorNetworkAnalyzer.frequency_center.setter  # type: ignore
    def frequency_center(self, value: float, channel=1):
        """sets the frequency center in Hz"""
        self.settings.frequency_center = value
        freq = str(self.settings.frequency_center)
        self.send_command(f"SENS{channel}:FREQ:CENT", freq)

    @VectorNetworkAnalyzer.frequency_start.setter  # type: ignore
    def frequency_start(self, value: float, channel=1):
        """sets the frequency start in Hz"""
        self.settings.frequency_start = value
        freq = str(self.settings.frequency_start)
        self.send_command(f"SENS{channel}:FREQ:STAR", freq)

    @VectorNetworkAnalyzer.frequency_stop.setter  # type: ignore
    def frequency_stop(self, value: float, channel=1):
        """sets the frequency stop in Hz"""
        self.settings.frequency_stop = value
        freq = str(self.settings.frequency_stop)
        self.send_command(f"SENS{channel}:FREQ:STOP", freq)

    @VectorNetworkAnalyzer.if_bandwidth.setter  # type: ignore
    def if_bandwidth(self, value: float, channel=1):
        """sets the if bandwidth in Hz"""
        self.settings.if_bandwidth = value
        bandwidth = str(self.settings.if_bandwidth)
        self.send_command(f"SENS{channel}:BWID", bandwidth)

    @VectorNetworkAnalyzer.averaging_enabled.setter  # type: ignore
    def averaging_enabled(self, value: bool):
        """sets the averaging enabled"""
        self.settings.averaging_enabled = value
        self._average_state(state=self.settings.averaging_enabled)

    @VectorNetworkAnalyzer.number_averages.setter  # type: ignore
    def number_averages(self, value: int, channel=1):
        """sets the number averages"""
        self.settings.number_averages = value
        self._average_count(count=str(self.settings.number_averages), channel=channel)

    @VectorNetworkAnalyzer.number_points.setter  # type: ignore
    def number_points(self, value: int):
        """sets the number of points for sweep"""
        self.settings.number_points = value
        points = str(self.settings.number_points)
        self.send_command(":SENS1:SWE:POIN", points)

    @VectorNetworkAnalyzer.electrical_delay.setter  # type: ignore
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
