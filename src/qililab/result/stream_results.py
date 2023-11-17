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

        .. note::

            All the following examples are explained in detail in the :ref:`Platform <platform>` section of the documentation. However, here are a few thing to keep in mind:

            - To connect, your computer must be in the same network of the instruments specified in the runcard, with their IP's addresses. Connection is necessary for the subsequent steps.

            - You might want to skip the ``platform.initial_setup()`` and the ``platform.turn_on_instruments()`` steps if you think nothing has been modified, but we recommend doing them every time.

            - ``platform.turn_on_instruments()`` is used to turn on the signal output of all the sources defined in the runcard (RF, Voltage and Current sources).

            - You can print ``platform.chip`` and ``platform.buses`` at any time to check the platform's structure.

        **1. Executing an experiment and saving the results live time:**


        To execute an experiment you first need to define the loops and the values you want to loop for, for example, a Rabi experiment
        where you will loop over amplitude values, measuring the results out of the amplitude in each of the steps.
        Then you also need to build, connect, set up, and execute the platform, which together look like:

        .. code-block:: python

            import numpy as np
            import qililab as ql

            # Building the platform:
            platform = ql.build_platform(runcard="runcards/galadriel.yml")

            # Connecting and setting up the platform:
            platform.connect()
            platform.initial_setup()
            platform.turn_on_instruments()

            # Executing the experiment on the platform:
            AMP_VALUES = np.arange(0, 1, 1000)

            stream_array = ql.stream_results(shape=(1000, 2), loops={"amp": AMP_VALUES}, path="results.h5", name="rabi")

            with stream_array:
                for i, amp in enumerate(AMP_VALUES):
                    platform.set_parameter(alias="drive_q0", parameter=ql.Parameter.AMPLITUDE, value=amp)
                    results = platform.execute(circuit)
                    stream_array[i][0] = results.array[0]
                    stream_array[i][0] = results.array[1]

        The results would look something like this:

        >>> print(ql.load_results(path="results.h5"))
        (array([[700.,   0.],
            [  0.,   0.],
            [  0.,   0.],
            ...,
            [  0.,   0.],
            [  0.,   0.],
            [  0.,   0.]]), {'amp': array([1, 2, 3])})

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
        self._results = np.zeros(shape=shape)
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
        self._results[key] = value

    def __enter__(self):
        """Enters the context manager."""
        self._file = h5py.File(name=self.path, mode="w")
        # Save loops
        g = self._file.create_group(name="loops")
        for loop_name, array in self.loops.items():
            g.create_dataset(name=loop_name, data=array)
        # Save results
        self._dataset = self._file.create_dataset("results", data=self._results)

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
        return self._results[index]

    def __len__(self):
        """Gets length of results."""
        return len(self._results)

    def __iter__(self):
        """Gets iterator of results."""
        return iter(self._results)

    def __str__(self):
        """Gets string representation of results."""
        return str(self._results)

    def __repr__(self):
        """Gets string representation of results."""
        return repr(self._results)

    def __contains__(self, item: dict[str, Any]):
        """Returns if an item is contained in results.

        Args:
            item (dict): item

        Returns:
            bool: True if an item is contained in results.
        """
        return item in self._results
