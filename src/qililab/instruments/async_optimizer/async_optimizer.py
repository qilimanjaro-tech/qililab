"""AsyncOpt instrument."""
from dataclasses import dataclass

import numpy as np

from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.utils import InstrumentFactory

from typing import Union
from qililab.typings import InstrumentName, AsyncOptDriver
from qililab.typings.enums import Parameter
from qililab.experiment.experiment import Experiment


@InstrumentFactory.register
class AsyncOpt(Instrument):
    """AsyncOpt class.
    Args:
        name (InstrumentName): name of the instrument
        device (AsyncOptDriver): Instance of the Instrument device driver.
        settings (AsyncOptSettings): Settings of the instrument.
    """

    name = InstrumentName.ASYNC_OPT

    @dataclass
    class AsyncOptSettings(Instrument.InstrumentSettings):
        """Settings for AsyncOpt instrument."""

        learner: None = None # not sure how to put it as a Scikit-Optimize or Adaptive learner
        data_process: None = None # not sure how to put it as a function type
        iteration: int = 0
        control_var_set_call: None = None # not sure how to put it as a function type
        experiment: Experiment

    settings: AsyncOptSettings
    device: AsyncOptDriver

    @Instrument.CheckDeviceInitialized
    @Instrument.CheckParameterValueFloatOrInt
    def setup(
        self,
        parameter: Parameter,
        value: float | str | bool,
        channel_id: int | None = None,
    ):
        """Setup instrument."""
        if parameter == Parameter.ITERATION:
            self.set_parameter
            return
        raise ParameterNotFound(f"Invalid Parameter: {parameter.value}")

    @property
    def iteration(self):
        """AsyncOpt 'iteration' property.

        Returns:
            int: the iteration value
        """
        return self.settings.iteration

    @iteration.setter
    def iteration(self, value: int):
        """
        This function implements an asynchronous optimization loop
        numbered steps follow the scheme of sciki optimize
        https://scikit-optimize.github.io/stable/auto_examples/ask-and-tell.html
        it also complies with adaptive

        Args:
            float: Maximum voltage allowed in current mode.
        """
        previous_value = self.settings.iteration
        self.settings.iteration = value

        if previous_value>0:
            # feed previous result values
            # 3. observe the outcome of running the experiment
            last_experiment_data = self.settings.experiment.results.results[-1] # line 243 experiment.py
            # process it
            last_y = self.settings.data_process(last_experiment_data)
            # feed it
            # 4. walk back to your laptop and tell the optimizer about the outcome
            self.settings.learner.tell(self.last_x,last_y)
        # get next values
        # 1. ask for a new set of parameters
        self.last_x = self.settings.learner.ask(n=1)
        # set these values
        # 2. walk to the experiment and program in the new parameters
        for i_x, this_x in enumerate(self.last_x):
            self.settings.control_var_set_call[i_x](value=this_x)
