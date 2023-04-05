"""VectorNetworkAnalyzer class."""
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument
from qililab.result.vna_result import VNAResult
from qililab.typings.instruments.vector_network_analyzer import VectorNetworkAnalyzerDriver


class VectorNetworkAnalyzer(Instrument):
    """Abstract base class defining all vector network analyzers"""

    @dataclass
    class VectorNetworkAnalyzerSettings(Instrument.InstrumentSettings):
        """Contains the settings of a specific signal generator."""

    settings: VectorNetworkAnalyzerSettings
    device: VectorNetworkAnalyzerDriver

    def to_dict(self):
        """Return a dict representation of the VectorNetworkAnalyzer class."""
        return dict(super().to_dict().items())

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Set initial instrument settings."""
        self.device.initial_setup()

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument settings."""
        self.device.reset()

    @Instrument.CheckDeviceInitialized
    def turn_on(self):
        """Start an instrument."""
        return self.send_command(command=":OUTP", arg="ON")

    @Instrument.CheckDeviceInitialized
    def turn_off(self):
        """Stop an instrument."""
        return self.send_command(command=":OUTP", arg="OFF")

    def send_command(self, command: str, arg: str = "") -> str:
        """Send a command directly to the device."""
        return self.device.send_command(command=command, arg=arg)

    def send_query(self, query: str):
        """Send a query directly to the device."""
        return self.device.send_query(query)

    def send_binary_query(self, query: str):
        """Send a binary query directly to the device."""
        return self.device.send_binary_query(query)  # type: ignore

    def read_tracedata(self):
        """Get data from device."""

    def acquire_result(self):
        """Convert the data received from the device to a Result object."""
        return VNAResult(data=self.read_tracedata())
