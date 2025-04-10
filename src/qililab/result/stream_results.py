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
from typing import TYPE_CHECKING, Any

import h5py
import numpy as np

from qililab.qprogram import QProgram
from qililab.result.database import DatabaseManager, Measurement
from qililab.utils.serialization import serialize

if TYPE_CHECKING:
    from qililab.platform import Platform


class StreamArray:
    """Constructs a StreamArray instance.

    This methods serves as a constructor for user interface of the StreamArray class.

    Args:
        shape (tuple): results array shape.
        path (str): path to save results.
        loops (dict[str, np.ndarray]): dictionary with each loop name in the experiment as key and numpy array as values.

    Examples:

        You have the option to save your results in real-time using this feature.
        This ensures that in the event of a runtime failure, you can still access results up to the point of failure
        from a resulting file. You have to specify the desired shape of the results, the loops to include,
        and the path to the resulting file. Then you can start saving results in real-time by doing:


        .. code-block:: python

            import numpy as np
            import qililab as ql

            LOOP_VALUES = np.linspace(0, 1, 5)
            stream_array = ql.stream_results(shape=(5, 2), loops={"loop_name": LOOP_VALUES}, path="results.h5")

            with stream_array:
                for i, value in enumerate(LOOP_VALUES):
                    stream_array[(i, 0)] = value

        >>> stream_array
        [[0.   0.  ]
         [0.25 0.  ]
         [0.5  0.  ]
         [0.75 0.  ]
         [1.   0.  ]]

        >>> ql.load_results("results.h5")
        (array([[0., 0.],
               [0.25, 0.],
               [0.5, 0.],
               [0.75, 0.],
               [1., 0.]]), {'loop_name': array([0.  , 0.25, 0.5 , 0.75, 1.  ])})

    .. note::

        The output of `stream_results` is not picklable, thus it cannot be returned in a SLURM job. In this scenario we suggest copying the array with the data into a different variable and returning that variable instead:

        .. code-block:: python

            %%submit_job -o results -d galadriel
            LOOP_VALUES = np.linspace(0, 1, 5)
            stream_array = ql.stream_results(shape=(5, 2), loops={"loop_name": LOOP_VALUES}, path="results.h5")
            with stream_array:
                for i, value in enumerate(LOOP_VALUES):
                    # Here you can execute any algorithm you want
                    stream_array[(i, 0)] = value

            results = stream_array.results

        >>> results.result()
        (array([[0.   0.  ]
                [0.25 0.  ]
                [0.5  0.  ]
                [0.75 0.  ]
                [1.   0.  ]])

    """

    path: str
    _dataset: h5py.Dataset
    measurement: Measurement | None = None
    _file: h5py.File | None = None

    def __init__(
        self,
        shape: list | tuple,
        loops: dict[str, np.ndarray],
        platform: "Platform",
        experiment_name: str,
        db_manager: DatabaseManager,
        qprogram: QProgram | None = None,
        optional_identifier: str | None = None,
    ):

        self.results = np.zeros(shape=shape)
        self.loops = loops
        self.experiment_name = experiment_name
        self.db_manager = db_manager
        self.optional_identifier = optional_identifier
        self.platform = platform
        self.qprogram = qprogram

    def __enter__(self):

        self.measurement = self.db_manager.add_measurement(
            experiment_name=self.experiment_name,
            experiment_completed=False,
            optional_identifier=self.optional_identifier,
            platform=self.platform.to_dict(),
            qprogram=serialize(self.qprogram),
        )
        self.path = self.measurement.result_path

        # Save loops
        self._file = h5py.File(name=self.path, mode="w")

        g = self._file.create_group(name="loops")
        for loop_name, array in self.loops.items():
            g.create_dataset(name=loop_name, data=array)

        self._dataset = self._file.create_dataset("results", data=self.results)

        return self

    def __setitem__(self, key: tuple, value: float):
        """Sets and item by key and value in the dataset.

        Args:
            key (tuple): key for the item to save.
            value (float): value to save.
        """
        if self._file is not None and self._dataset is not None:
            self._dataset[key] = value
        self.results[key] = value

    def __exit__(self, *args):
        """Exits the context manager."""
        if self._file is not None:
            self._file.__exit__()
            self._file = None

        self.measurement = self.measurement.end_experiment(self.db_manager.Session)

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
