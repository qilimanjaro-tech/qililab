"""VectorNetworkAnalyzer class."""
from dataclasses import dataclass

from qililab.instruments.instrument import Instrument
from qililab.typings.enums import VNAScatteringParameters, VNATriggerModes

DEFAULT_NUMBER_POINTS = 1000


class VectorNetworkAnalyzer(Instrument):
    """Abstract base class defining all vector network analyzers"""

    @dataclass
    class VectorNetworkAnalyzerSettings(Instrument.InstrumentSettings):
        """Contains the settings of a specific signal generator.

        Args:
            power (float): Power of the instrument. Value range is (-120, 25).
        """

        power: float
        scattering_parameter: VNAScatteringParameters = VNAScatteringParameters.S21
        frequency_span: float | None = None
        frequency_center: float | None = None
        if_bandwidth: float | None = None
        averaging_enabled: bool = False
        number_averages: int = 1
        trigger_mode: VNATriggerModes = VNATriggerModes.INT
        number_points: int = DEFAULT_NUMBER_POINTS

    settings: VectorNetworkAnalyzerSettings

    @property
    def power(self):
        """VectorNetworkAnalyzer 'power' property.

        Returns:
            float: settings.power.
        """
        return self.settings.power

    @property
    def scattering_parameter(self):
        """VectorNetworkAnalyzer 'scattering_parameter' property.

        Returns:
            float: settings.scattering_parameter.
        """
        return self.settings.scattering_parameter.value

    @property
    def frequency_span(self):
        """VectorNetworkAnalyzer 'frequency_span' property.

        Returns:
            float: settings.frequency_span.
        """
        return self.settings.frequency_span

    @property
    def frequency_center(self):
        """VectorNetworkAnalyzer 'frequency_center' property.

        Returns:
            float: settings.frequency_center.
        """
        return self.settings.frequency_center

    @property
    def if_bandwidth(self):
        """VectorNetworkAnalyzer 'if_bandwidth' property.

        Returns:
            float: settings.if_bandwidth.
        """
        return self.settings.if_bandwidth

    @property
    def averaging_enabled(self):
        """VectorNetworkAnalyzer 'averaging_enabled' property.

        Returns:
            float: settings.averaging_enabled.
        """
        return self.settings.averaging_enabled

    @property
    def number_averages(self):
        """VectorNetworkAnalyzer 'number_averages' property.

        Returns:
            float: settings.number_averages.
        """
        return self.settings.number_averages

    @property
    def trigger_mode(self):
        """VectorNetworkAnalyzer 'trigger_mode' property.

        Returns:
            float: settings.trigger_mode.
        """
        return self.settings.trigger_mode.value

    @property
    def number_points(self):
        """VectorNetworkAnalyzer 'number_points' property.

        Returns:
            float: settings.number_points.
        """
        return self.settings.number_points

    def to_dict(self):
        """Return a dict representation of the VectorNetworkAnalyzer class."""
        return dict(super().to_dict().items())

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Set initial instrument settings."""
        self.device.initial_setup()

    @Instrument.CheckDeviceInitialized
    def setup(self):
        """Set instrument settings."""

    @Instrument.CheckDeviceInitialized
    def reset(self):
        """Reset instrument settings."""
        self.device.reset()

    @Instrument.CheckDeviceInitialized
    def stop(self):
        """Stop an instrument."""
        self.device.stop()
