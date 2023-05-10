"""Qblox QCM class"""
from dataclasses import dataclass

from qpysequence.program import Loop, Register
from qpysequence.weights import Weights

from qililab.instruments import Instrument
from qililab.instruments.awg_settings import AWGQbloxSequencer
from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.instruments.utils.instrument_factory import InstrumentFactory
from qililab.result.qblox_results.qblox_result import QbloxResult
from qililab.typings import InstrumentName, Parameter


@InstrumentFactory.register
class QbloxQCM(QbloxModule):
    """Qblox QCM class.

    Args:
        settings (QBloxQCMSettings): Settings of the instrument.
    """

    name = InstrumentName.QBLOX_QCM

    @dataclass
    class QbloxQCMSettings(QbloxModule.QbloxModuleSettings):
        """Contains the settings of a specific pulsar."""

        out_offsets: list[float]

    settings: QbloxQCMSettings

    def _generate_weights(self, sequencer: AWGQbloxSequencer) -> Weights:
        """Generate acquisition weights.

        Returns:
            dict: Acquisition weights.
        """
        return Weights()

    def _append_acquire_instruction(self, loop: Loop, bin_index: Register | int, sequencer_id: int):
        """Append an acquire instruction to the loop."""

    def acquire_result(self) -> QbloxResult:
        """Read the result from the AWG instrument

        Returns:
            QbloxResult: Acquired Qblox result
        """
        raise NotImplementedError

    @Instrument.CheckDeviceInitialized
    def initial_setup(self):
        """Initial setup"""
        super().initial_setup()
        for idx, offset in enumerate(self.out_offsets):
            self._set_out_offset(output=idx, value=offset)

    @Instrument.CheckDeviceInitialized
    def setup(self, parameter: Parameter, value: float | str | bool, channel_id: int | None = None):
        """Set Qblox instrument calibration settings."""
        if parameter in {Parameter.OFFSET_OUT0, Parameter.OFFSET_OUT1, Parameter.OFFSET_OUT2, Parameter.OFFSET_OUT3}:
            output = int(parameter.value[-1])
            self._set_out_offset(output=output, value=value)
            return
        super().setup(parameter=parameter, value=value, channel_id=channel_id)

    @Instrument.CheckParameterValueFloatOrInt
    def _set_out_offset(self, output: int, value: float | str | bool):
        """Set output offsets of the Qblox device.

        Args:
            output (int): output to update
            value (float | str | bool): value to update

        Raises:
            ValueError: when value type is not float or int
        """
        if output > len(self.out_offsets):
            raise IndexError(
                f"Output {output} is out of range. The runcard has only {len(self.out_offsets)} output offsets defined."
                " Please update the list of output offsets of the runcard such that it contains a value for each "
                "output of the device."
            )
        self.out_offsets[output] = value
        getattr(self.device, f"out{output}_offset")(float(value))
