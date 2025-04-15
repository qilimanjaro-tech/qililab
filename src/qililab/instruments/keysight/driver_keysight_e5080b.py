# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This file is meant to be qcode
from typing import Any

import qcodes.validators as vals
from qcodes import VisaInstrument
from qcodes.parameters import Parameter, create_on_off_val_mapping
from qcodes.validators import Enum, Numbers


class Driver_KeySight_E5080B(VisaInstrument):
    """
    This is the qcodes driver for the Keysight E5080B Vector Network Analyzer
    """

    def __init__(self, name: str, address: str, **kwargs: Any) -> None:
        super().__init__(name, address, terminator="\n", **kwargs)

        # Setting frequency range
        min_freq = 100e3
        max_freq = 53e9
        min_if_bandwidth = 1
        max_if_bandwidth = 15e6
        min_nop = 11
        max_nop = 100003
        min_power = -100
        max_power = 20

        # Sets the start frequency of the analyzer.
        self.start_freq: Parameter = self.add_parameter(
            "start_freq",
            label="Start Frequency",
            get_cmd="SENS:FREQ:STAR?",
            get_parser=float,
            set_cmd="SENS:FREQ:STAR {}",
            unit="Hz",
            vals=Numbers(min_value=min_freq, max_value=max_freq),
        )
        """Parameter start_freq"""

        # Sets the stop frequency of the analyzer.
        self.stop_freq: Parameter = self.add_parameter(
            "stop_freq",
            label="Stop Frequency",
            get_cmd="SENS:FREQ:STOP?",
            get_parser=float,
            set_cmd="SENS:FREQ:STOP {}",
            unit="Hz",
            vals=Numbers(min_value=min_freq, max_value=max_freq),
        )
        """Parameter stop_freq"""

        # Sets the center frequency of the analyzer.
        self.center_freq: Parameter = self.add_parameter(
            "center_freq",
            label="Center Frequency",
            get_cmd="SENS:FREQ:CENT?",
            get_parser=float,
            set_cmd="SENS:FREQ:CENT {}",
            unit="Hz",
            vals=Numbers(min_value=min_freq, max_value=max_freq),
        )
        """Parameter center_freq"""

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
            vals=Numbers(min_value=min_nop, max_value=max_nop),
        )
        """Parameter points"""

        # Sets the RF power output level.
        self.source_power: Parameter = self.add_parameter(
            "source_power",
            label="source_power",
            unit="dBm",
            get_cmd="SOUR:POW?",
            set_cmd="SOUR:POW {}",
            get_parser=float,
            vals=Numbers(min_value=min_power, max_value=max_power),
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

        # Sets the type of analyzer sweep mode. First set sweep type, then set sweep parameters such as frequency or power settings. Default is LIN
        self.sweep_type: Parameter = self.add_parameter(
            "sweep_type",
            label="Type",
            get_cmd="SENS:SWE:TYPE?",
            set_cmd="SENS:SWE:TYPE {}",
            vals=Enum("LIN", "LOG", "POW", "CW", "SEGM"),
        )
        """Parameter sweep_type"""

        # Sets the number of trigger signals the specified channel will ACCEPT. Default is CONT.
        self.sweep_mode: Parameter = self.add_parameter(
            "sweep_mode",
            label="Type",
            get_cmd="SENS:SWE:MODE?",
            set_cmd="SENS:SWE:MODE {}",
            vals=Enum("HOLD", "CONT", "GRO", "SING"),
        )
        """Parameter sweep_mode"""

        # Set/get a measurement parameter for the specified measurement.
        self.scattering_parameter: Parameter = self.add_parameter(
            "scattering_parameter",
            label="scattering_parameter",
            get_cmd="CALC:MEAS:PAR?",
            set_cmd="CALC:MEAS:PAR {}",
            vals=vals.Enum("S11", "S12", "S21", "S22"),
        )
        """Parameter scattering_parameter"""

        # Turns trace averaging ON or OFF. Default OFF
        self.averages_enabled: Parameter = self.add_parameter(
            "averages_enabled",
            label="Averages Enabled",
            get_cmd="SENS:AVER?",
            set_cmd="SENS:AVER {}",
            val_mapping=create_on_off_val_mapping(on_val="1", off_val="0"),
        )
        """Parameter averages_enabled"""

        # Sets the number of measurements to combine for an average. Must also set SENS:AVER[:STATe] ON
        self.averages_count: Parameter = self.add_parameter(
            "averages_count",
            label="Averages Count",
            get_cmd="SENS:AVER:COUN?",
            get_parser=int,
            set_cmd="SENS:AVER:COUN {:d}",
            vals=Numbers(min_value=1, max_value=65536),
        )
        """Parameter averages count"""

        # Sets the type of averaging to perform: Point or Sweep (default is sweep).
        self.averages_mode: Parameter = self.add_parameter(
            "averages_mode",
            label="Averages Mode",
            get_cmd="SENS:AVER:MODE?",
            set_cmd="SENS:AVER:MODE {}",
            vals=Enum("POIN", "SWE"),
        )
        """Parameter averages mode"""

        # Sets the data format for transferring measurement data and frequency data. Default is ASCii,0.
        self.format_data: Parameter = self.add_parameter(
            "format_data",
            label="Format Data",
            get_cmd="FORM:DATA?",
            set_cmd="FORM:DATA {}",
            vals=Enum("REAL,32", "REAL,64", "ASCii,0"),
        )
        """Parameter averages mode"""

        # Turns RF power from the source ON or OFF.
        self.rf_on: Parameter = self.add_parameter(
            "rf_on",
            label="RF ON",
            get_cmd="OUTP?",
            set_cmd="OUTP {}",
            val_mapping=create_on_off_val_mapping(on_val="1", off_val="0"),
        )
        """Parameter RF Power Source"""

        # Set the byte order used for GPIB data transfer.
        # Some computers read data from the analyzer in the reverse order. This command is only implemented if FORMAT:DATA is set to :REAL.
        self.format_border: Parameter = self.add_parameter(
            "format_border",
            label="Format Border",
            get_cmd="FORM:BORD?",
            set_cmd="FORM:BORD {}",
            vals=Enum("NORM", "SWAP"),
        )
        """Parameter Format Border"""

        self.add_function("clear_averages", call_cmd="SENS:AVER:CLE")

        # Clear Status
        # Clears the instrument status byte by emptying the error queue and clearing all event registers. Also cancels any preceding *OPC command or query
        self.add_function("cls", call_cmd="*CLS")

        # Operation complete command
        # Generates the OPC message in the standard event status register when all pending overlapped operations have been completed (for example, a sweep, or a Default)
        self.add_function("opc", call_cmd="*OPC")

        # System Reset
        # Deletes all traces, measurements, and windows.
        self.add_function("system_reset", call_cmd="SYST:PRES")
