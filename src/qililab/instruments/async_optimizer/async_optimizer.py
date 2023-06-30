"""AsyncOpt instrument."""
from dataclasses import dataclass

import numpy as np

from qililab.instruments.instrument import Instrument, ParameterNotFound
from qililab.instruments.utils import InstrumentFactory

from typing import Union
from qililab.typings import InstrumentName
from qililab.typings.enums import Parameter


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
    class AsyncOptSettings:
        """Settings for AsyncOpt instrument."""

        alias: str
        learner: None = None # not sure how to put it as a Scikit-Optimize or Adaptive learner
        data_process: None = None # not sure how to put it as a function type
        iteration: int = -1
        control_var_set_call: None = None # not sure how to put it as a function type
        experiment: None = None

    settings: AsyncOptSettings
    device: int=0

    def setup(
        self,
        parameter: Parameter,
        value: float | str | bool,
        channel_id: int | None = None,
    ):
        """Setup instrument."""
        if parameter == Parameter.ITERATION:
            self.iteration =value
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
        print(f'entered async iteration handling {previous_value}->{value}')

        if value==0:
            print('Removed unfinished')
            self.settings.learner.remove_unfinished()
        elif previous_value==value:
            print('Returned void')
            return
    

        if previous_value>-1:
            # feed previous result values
            # 3. observe the outcome of running the experiment
            last_experiment_data = self.settings.experiment.results.results[-1] # line 243 experiment.py
            # process it
            last_y = self.settings.data_process(last_experiment_data)
            # feed it
            # 4. walk back to your laptop and tell the optimizer about the outcome
            print(f'Last_x={self.last_x}; Last_y={last_y}')
            if len(self.last_x)==1:
                last_x = self.last_x[0]
            else:
                last_x = self.last_x
            self.settings.learner.tell(last_x,last_y)
        # get next values
        # 1. ask for a new set of parameters
        self.last_x = self.settings.learner.ask(n=1)[0]

        # set these values
        # 2. walk to the experiment and program in the new parameters
        for this_call, this_x in zip(self.settings.control_var_set_call,self.last_x):
            this_call(value=this_x)
