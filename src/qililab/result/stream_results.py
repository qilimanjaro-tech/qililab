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
from typing import Any

import h5py
import numpy as np


def stream_results(shape: tuple, path: str, loops: dict[str, np.ndarray]):
    """Constructs a StreamArray instance.

    This methods serves as a constructor for user interface of the StreamArray class.

    Args:
        shape (tuple): results array shape.
        path (str): path to save results.
        loops (dict[str, np.ndarray]): dictionary with each loop name in the experiment as key and numpy array as values.

    Examples:

        **1. Executing an experiment and saving the results live time:**


        To execute an experiment you first need to define the loops and the values you want to loop for, for example, a Rabi experiment
        where you will loop over amplitude values, measuring the results out of the amplitude in each of the steps.
        Then you also need to build, connect, set up, and execute the platform, which together look like:

        .. code-block:: python

            from qibo.models import Circuit
            import numpy as np
            import qililab as ql

            # Constants
            QUBIT = 0
            M_BUFFER_TIME = 0
            AMP_VALUES = np.linspace(0, 1, 1000)
            PLATFORM_PATH = "runcards/galadriel.yml"

            # Building the platform:
            platform = ql.build_platform(runcard=PLATFORM_PATH)

            # Connecting and setting up the platform:
            platform.connect()
            platform.initial_setup()
            platform.turn_on_instruments()

            # Define circuit
            circuit = Circuit(QUBIT + 1)
            circuit.add(ql.Drag(QUBIT, theta=np.pi, phase=0))
            circuit.add(ql.Wait(QUBIT, M_BUFFER_TIME))
            circuit.add(gates.M(QUBIT))

            # Executing the experiment on the platform:
            stream_array = ql.stream_results(shape=(1000, 2), loops={"amp": AMP_VALUES}, path="results.h5")

            with stream_array:
                for i, amp in enumerate(AMP_VALUES):
                    platform.set_parameter(alias="drive_q0", parameter=ql.Parameter.AMPLITUDE, value=amp)
                    results = platform.execute(circuit)
                    stream_array[(i, 0)] = results.array[0]
                    stream_array[(i, 1)] = results.array[1]

        The results would look something like this:

        >>> print(ql.load_results(path="results.h5"))
        (array([[700.,   0.],
            [  0.,   0.],
            [  0.,   0.],
            ...,
            [  0.,   0.],
            [  0.,   0.],
            [  0.,   0.]]), {'amp': array([0, 0.1,..., 1.0])})

        You can also include nested loops experiments like this:

        .. code-block:: python

            from qibo.models import Circuit
            import numpy as np
            import qililab as ql

            # Constants
            QUBIT = 0
            M_BUFFER_TIME = 0
            AMP_VALUES = np.linspace(0, 1, 1000)
            FREQ_VALUES = np.linspace(0, 1, 1000)
            PLATFORM_PATH = "runcards/galadriel.yml"

            # Building the platform:
            platform = ql.build_platform(runcard=PLATFORM_PATH)

            # Connecting and setting up the platform:
            platform.connect()
            platform.initial_setup()
            platform.turn_on_instruments()

            # Define circuit
            circuit = Circuit(QUBIT + 1)
            circuit.add(ql.Drag(QUBIT, theta=np.pi, phase=0))
            circuit.add(ql.Wait(QUBIT, M_BUFFER_TIME))
            circuit.add(gates.M(QUBIT))

            # Executing the experiment on the platform:
            stream_array = ql.stream_results(shape=(1000, 1000, 2), loops={"amp": AMP_VALUES, "freq": FREQ_VALUES}, path="results.h5")

            with stream_array:
                for i, amp in enumerate(AMP_VALUES):
                    platform.set_parameter(alias="drive_q0", parameter=ql.Parameter.AMPLITUDE, value=amp)
                    for j, freq in enumerate(FREQ_VALUES):
                        platform.set_parameter(alias="drive_q0", parameter=ql.Parameter.LO_FREQUENCY, value=freq)
                        results = platform.execute(circuit)
                        stream_array[(i, j, 0)] = results.array[0]
                        stream_array[(i, j, 1)] = results.array[1]

        The results would look something like this:

        >>> print(ql.load_results(path="results.h5"))
        (array([[[700.,   0.],
            [  0.,   0.],
            [  0.,   0.],
            ...,
            [  0.,   0.],
            [  0.,   0.],
            [  0.,   0.]]]), {'amp': array([0, 0.1,...,1.0], 'freq': array([0, 0.1,...,1.0])})

    **2. Executing an experiment and saving the results live time using SLURM:**


        You can also run an experiment using SLURM and save the results live time using from a notebook by doing:

        .. code-block:: python

            from qibo.models import Circuit
            import numpy as np
            import qililab as ql

            %%submit_job -o results -p galadriel

            QUBIT = 0
            M_BUFFER_TIME = 0
            AMP_VALUES = np.linspace(0, 0.4, num=11)
            HW_AVG = 1000
            REPETITION_DURATION = 200_000
            PLATFORM_PATH = "runcards/galadriel.yml"

            # Building the platform:
            platform = ql.build_platform(runcard=PLATFORM_PATH)
            platform.connect()
            platform.initial_setup()
            platform.turn_on_instruments()

            # Define circuit
            circuit = Circuit(QUBIT + 1)
            circuit.add(ql.Drag(QUBIT, theta=np.pi, phase=0))
            circuit.add(ql.Wait(QUBIT, M_BUFFER_TIME))
            circuit.add(gates.M(QUBIT))

            # Executing the experiment through SLURM:
            stream_array = ql.stream_results(shape=(1000, 2), loops={"amp": AMP_VALUES}, path="results.h5")

            with stream_array:
                for i, amp in enumerate(AMP_VALUES):
                    platform.set_parameter(alias=f"Drag({QUBIT})", parameter=ql.Parameter.AMPLITUDE, value=float(amp))
                    results = platform.execute(program=circuit, num_avg=HW_AVG, repetition_duration=REPETITION_DURATION)
                    stream_array[(i, 0)] = results.array[0]
                    stream_array[(i, 1)] = results.array[1]

            results = stream_array.results

        The results would look something like this:

        >>> print(results.result())
        (array([[ 0.24409233, -6.61454812],
            [-0.06998486, -6.5098212 ],
            [-1.08470591, -5.96761065],
            ...,
            [ 0.        ,  0.        ],
            [ 0.        ,  0.        ],
            [ 0.        ,  0.        ]]))

    """
    return StreamArray(shape=shape, path=path, loops=loops)


class StreamArray:
    """Allows for real time saving of results from an experiment.

    This class wraps a numpy array and adds a context manager to save results on real time while they are acquired by
    the instruments.

    Args:
        shape (tuple): results array shape.
        path (str): path to save results.
        loops (dict[str, np.ndarray]): dictionary with each loop name in the experiment as key and numpy array as values.
    """

    def __init__(self, shape: tuple, path: str, loops: dict[str, np.ndarray]):
        self.results = np.zeros(shape=shape)
        self.path = path
        self.loops = loops
        self._file: h5py.File | None = None
        self._dataset = None

    def __setitem__(self, key: str, value: float):
        """Sets and item by key and value in the dataset.

        Args:
            key (str): key for the item to save.
            value (float): value to save.
        """
        if self._file is not None and self._dataset is not None:
            self._dataset[key] = value
        self.results[key] = value

    def __enter__(self):
        self._file = h5py.File(name=self.path, mode="w")
        # Save loops
        g = self._file.create_group(name="loops")
        for loop_name, array in self.loops.items():
            g.create_dataset(name=loop_name, data=array)
        # Save results
        self._dataset = self._file.create_dataset("results", data=self.results)

        return self

    def __exit__(self, *args):
        """Exits the context manager."""
        if self._file is not None:
            self._file.__exit__()
            self._file = None

    def __getitem__(self, index: int):
        """Gets item by index.

        Args:
            index (int): item's index.
        """
        return self.results[index]

    def __len__(self):
        """Gets length of results."""
        return len(self.results)

    def __iter__(self):
        """Gets iterator of results."""
        return iter(self.results)

    def __str__(self):
        """Gets string representation of results."""
        return str(self.results)

    def __repr__(self):
        """Gets string representation of results."""
        return repr(self.results)

    def __contains__(self, item: dict[str, Any]):
        """Returns if an item is contained in results.

        Args:
            item (dict): item

        Returns:
            bool: True if an item is contained in results.
        """
        return item in self.results
