#QUESTIONS FOR FABIO
# Power always has port1
# bounds of power -  do i want to query?
# always the S11?


from qcodes import VisaInstrument
from qcodes.parameters import (
    Parameter,
)
from qcodes.validators import Arrays, Bool, Enum, Ints, Numbers
from qcodes.parameters import create_on_off_val_mapping

class KeySightE5080B(VisaInstrument):
    """
    This is the qcodes driver for the Keysight E5080B Vector Network Analyzer
    """

    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, **kwargs)

        # Setting frequency range
        min_freq = 100e3
        max_freq = 53e9
        min_if_bandwidth = 1
        max_if_bandwidth = 15e6

        def get_power_limits(self):
            """Queries the minimum and maximum power limits."""
            max_power = float(self.ask(f"SOURce{self.channel}:POWer? MAX"))
            min_power = float(self.ask(f"SOURce{self.channel}:POWer? MIN"))
            return min_power, max_power

        # Sets the start frequency of the analyzer.
        self.start: Parameter = self.add_parameter(
            "start",
            label="Start Frequency",
            get_cmd="SENS:FREQ:STAR?",
            get_parser=float,
            set_cmd="SENS:FREQ:STAR {}",
            unit="Hz",
            vals=Numbers(min_value=min_freq, max_value=max_freq),
        )
        """Parameter start"""

        # Sets the stop frequency of the analyzer.
        self.stop: Parameter = self.add_parameter(
            "stop",
            label="Stop Frequency",
            get_cmd="SENS:FREQ:STOP?",
            get_parser=float,
            set_cmd="SENS:FREQ:STOP {}",
            unit="Hz",
            vals=Numbers(min_value=min_freq, max_value=max_freq),
        )
        """Parameter stop"""

        # Sets the center frequency of the analyzer.
        self.center: Parameter = self.add_parameter(
            "center",
            label="Center Frequency",
            get_cmd="SENS:FREQ:CENT?",
            get_parser=float,
            set_cmd="SENS:FREQ:CENT {}",
            unit="Hz",
            vals=Numbers(min_value=min_freq, max_value=max_freq),
        )
        """Parameter center"""

        # Sets and reads how the center frequency step size is set. When TRUE, center steps by 5% of span. When FALSE, center steps by STEP:SIZE value.
        # Default is 40 Mhz. When STEP:AUTO is TRUE, this value is ignored.
        self.step_auto: Parameter = self.add_parameter(
            "center_step_auto",
            label="Center Frequency Step Auto",
            get_cmd="SENS:FREQ:CENT:STEP:AUTO?",
            set_cmd="SENS:FREQ:CENT:STEP:AUTO {}",
            val_mapping=create_on_off_val_mapping(on_val="1", off_val="0"),
        )
        """Parameter center frequency step auto"""

        # Sets the center frequency step size of the analyzer. This command sets the manual step size (only valid when STEP:AUTO is FALSE).
        self.step_size: Parameter = self.add_parameter(
            "center_step_size",
            label="Center Frequency Step",
            get_cmd="SENS:FREQ:CENT:STEP:SIZE?",
            get_parser=float,
            set_cmd="SENS:FREQ:CENT:STEP:SIZE {}",
            unit="Hz",
            vals=Numbers(min_value=0, max_value=self.stop.get_latest()),
        )
        """Parameter center frequency step"""

        # Sets the frequency span of the analyzer.
        self.span: Parameter = self.add_parameter(
            "span",
            label="Frequency Span",
            get_cmd="SENS:FREQ:SPAN?",
            get_parser=float,
            set_cmd="SENS:FREQ:SPAN {}",
            unit="Hz",
            vals=Numbers(min_value=min_freq, max_value=max_freq),
        )
        """Parameter span"""

        # Sets the Continuous Wave (or Fixed) frequency. Must also send SENS:SWEEP:TYPE CW to put the analyzer into CW sweep mode.
        self.cw: Parameter = self.add_parameter(
            "cw",
            label="CW Frequency",
            get_cmd="SENS:FREQ:CW?",
            get_parser=float,
            set_cmd="SENS:FREQ:CW {}",
            unit="Hz",
        )
        """Parameter Continuous wave"""

        
        # Sets the number of data points for the measurement.
        self.points: Parameter = self.add_parameter(
            "points",
            label="Points",
            get_cmd="SENS:SWE:POIN?",
            get_parser=int,
            set_cmd="SENS:SWE:POIN {}",
            unit="",
            vals=Numbers(min_value=11, max_value=100003),
        )
        """Parameter points"""

        # Sets the RF power output level.
        self.source_power: Parameter = self.add_parameter(
            "source_power",
            label="power",
            unit="dBm",
            get_cmd="SOUR:POW?",
            set_cmd= self._set_power_bounds,
            get_parser=float,
            vals=Numbers(),
        )
        """Parameter source_power"""

        # Sets the bandwidth of the digital IF filter to be used in the measurement.
        self.if_bandwidth: Parameter = self.add_parameter(
            "if_bandwidth",
            label="if_bandwidth",
            unit="Hz",
            get_cmd="SENS:BWID?",
            set_cmd="SENS:BWID {}",
            get_parser=float,
            vals=Numbers(min_value=min_if_bandwidth, max_value=max_if_bandwidth),
        )
        """Parameter if_bandwidth"""

        # Sets the bandwidth of the digital IF filter to be used in the measurement.
        self.if_bandwidth: Parameter = self.add_parameter(
            "if_bandwidth",
            label="if_bandwidth",
            unit="Hz",
            get_cmd="SENS:BWID?",
            set_cmd="SENS:BWID {}",
            get_parser=float,
            vals=Numbers(min_value=min_if_bandwidth, max_value=max_if_bandwidth),
        )
        """Parameter if_bandwidth"""

        # Sets the type of analyzer sweep mode. First set sweep type, then set sweep parameters such as frequency or power settings. Default is LIN
        self.sweep_type: Parameter = self.add_parameter(
            "sweep_type",
            label="Type",
            get_cmd="SENS:SWE:TYPE?",
            set_cmd="SENS:SWE:TYPE {}",
            vals=Enum("LIN", "LOG", "POW", "CW", "SEGM"),
        )
        """Parameter sweep_type"""


#REVIEW BELOW
        # Set/get a measurement parameter for the specified measurement.
        self.if_bandwidth: Parameter = self.add_parameter(
            "if_bandwidth",
            label="if_bandwidth",
            unit="Hz",
            get_cmd="CALC:MEAS:PAR?",
            set_cmd="CALC%:MEAS:PAR? {}", #NEED TO SPECIFY THE PARAM
            get_parser=float,
            vals=Numbers(min_value=min_if_bandwidth, max_value=max_if_bandwidth),
        )
        """Parameter if_bandwidth"""

        # Turns trace averaging ON or OFF.
        self.averages_enabled: Parameter = self.add_parameter(
            "averages_enabled",
            label="Averages Enabled",
            get_cmd="SENS:AVER?",
            set_cmd="SENS:AVER {}",
            val_mapping={True: "1", False: "0"},
        )
        """Parameter averages_enabled"""

        # Sets the number of measurements to combine for an average. Must also set SENS:AVER[:STATe] ON
        self.averages_count: Parameter = self.add_parameter(
            "averages_count",
            label="Averages Count",
            get_cmd="SENS:AVER:COUN?",
            get_parser=int,
            set_cmd="SENS:AVER:COUN {:d}",
            unit="",
            vals=Numbers(min_value=1, max_value=65536),
        )
        """Parameter averages count"""

        #Sets the type of averaging to perform: Point or Sweep (default is sweep).
        self.averages_mode: Parameter = self.add_parameter(
            "averages_mode",
            label="Averages Mode",
            get_cmd="SENS:AVER:MODE?",
            set_cmd="SENS:AVER:MODE {}",
            vals=Enum("POIN", "SWEEP"),
        )
        """Parameter averages mode"""

    
    #Write only commands

    def clear_averages(self) -> None:
        """
        Clears and restarts averaging of the measurement data. Does NOT apply to point averaging.
        """
        self.write("SENS:AVER:CLE")

    def _set_power_bounds(self, value):
        """Sets the power bounds after dynamically determining valid limits."""
        max_power = float(self.ask("SOUR:POW?MAX"))
        min_power = float(self.ask("SOUR:POW?MIN"))
        self.power_level.vals = Numbers(min_value=min_power, max_value=max_power)
        self.write("SOUR:POW {}")