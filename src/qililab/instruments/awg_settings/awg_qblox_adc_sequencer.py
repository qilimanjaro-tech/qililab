""" AWG Qblox ADC Sequencer """


from dataclasses import dataclass, field

from qililab.instruments.awg_settings.awg_adc_sequencer import AWGADCSequencer
from qililab.instruments.awg_settings.awg_qblox_sequencer import AWGQbloxSequencer


@dataclass
class AWGQbloxADCSequencer(AWGQbloxSequencer, AWGADCSequencer):
    """AWG Qblox ADC Sequencer"""

    weights_path0: list[float]
    weights_path1: list[float]
    weighed_acq_enabled: bool
    threshold: float

    def __post_init__(self):
        super().__post_init__()
        self._verify_weights()

    def _verify_weights(self):
        """Verifies that the length of weights_path0 and weights_path1 are equal.

        Raises:
            IndexError: The length of weights_path0 and weights_path1 must be equal.
        """
        if len(self.weights_path0) != len(self.weights_path1):
            raise IndexError("The length of weights_path0 and weights_path1 must be equal.")

    @property
    def used_integration_length(self) -> int:
        """Final integration length used by the AWG in the integration.

        Returns:
            int: Length of the weights if weighed acquisition is enabled, configured `integration_length` if disabled.
        """
        return len(self.weights_path0) if self.weighed_acq_enabled else self.integration_length
