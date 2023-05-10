""" AWG Qblox ADC Sequencer """
from dataclasses import dataclass

from qililab.instruments.awg_settings.awg_adc_sequencer import AWGADCSequencer
from qililab.instruments.awg_settings.awg_qblox_sequencer import AWGQbloxSequencer


@dataclass
class AWGQbloxADCSequencer(AWGQbloxSequencer, AWGADCSequencer):
    """AWG Qblox ADC Sequencer"""

    weights_i: list[float]
    weights_q: list[float]
    weighed_acq_enabled: bool
    threshold: float

    def __post_init__(self):
        super().__post_init__()
        self._verify_weights()

    def _verify_weights(self):
        """Verifies that the length of weights_i and weights_q are equal.

        Raises:
            IndexError: The length of weights_i and weights_q must be equal.
        """
        if len(self.weights_i) != len(self.weights_q):
            raise IndexError("The length of weights_i and weights_q must be equal.")

    @property
    def used_integration_length(self) -> int:
        """Final integration length used by the AWG in the integration.

        Returns:
            int: Length of the weights if weighed acquisition is enabled, configured `integration_length` if disabled.
        """
        return len(self.weights_i) if self.weighed_acq_enabled else self.integration_length
