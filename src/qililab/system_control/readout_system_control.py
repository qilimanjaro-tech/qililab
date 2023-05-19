"""ReadoutSystemControl class."""


from qililab.instruments import AWGAnalogDigitalConverter
from qililab.result import Result
from qililab.typings.enums import SystemControlName
from qililab.utils import Factory

from .system_control import SystemControl


@Factory.register
class ReadoutSystemControl(SystemControl):
    """System control used for readout."""

    name = SystemControlName.READOUT_SYSTEM_CONTROL

    def acquire_result(self) -> Result:
        """Read the result from the vector network analyzer instrument

        Returns:
            Result: Acquired result
        """
        # TODO: Support acquisition from multiple instruments
        results: list[Result] = []
        for instrument in self.instruments:
            result = instrument.acquire_result()
            if result is not None:
                results.append(result)

        if len(results) > 1:
            raise ValueError(
                f"Acquisition from multiple instruments is not supported. Obtained a total of {len(results)} results. "
            )

        return results[0]

    @property
    def acquisition_delay_time(self) -> int:
        """SystemControl 'acquisition_delay_time' property.
        Delay (in ns) between the readout pulse and the acquisition."""
        for instrument in self.instruments:
            if isinstance(instrument, AWGAnalogDigitalConverter):
                return instrument.acquisition_delay_time
        raise ValueError(f"The system control {self.name.value} doesn't have an AWG instrument.")
