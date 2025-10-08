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

from qililab.instruments.qblox.qblox_module import QbloxModule
from qililab.qprogram.qprogram import Calibration, QProgram
from qililab.result.database import DatabaseManager, Measurement
from qililab.utils.serialization import serialize

if TYPE_CHECKING:
    from qililab.platform import Platform


class StreamArray:
    """Constructs a StreamArray instance.

    This methods serves as a constructor for user interface of the StreamArray class.
    This class allows to save the experiment inside the database as the Software loop progresses
    This ensures that in the event of a runtime failure, you can still access results up to the point of failure
    from a resulting file.

    Args:
        shape (list | tuple): Shape of the results array.
        loops (dict[str, np.ndarray] | dict[str, dict[str, Any]]): dictionary of loops with the name of the loop and the array.
        platform (Platform): platform where the experiment was executed
        experiment_name (str): Name of the experiment.
        db_manager (DatabaseManager): database manager loaded from the database after setting the db parameters.
        qprogram (QProgram | None, optional): Qprogram of the experiment, if there is no Qprogram related to the results it is not mandatory. Defaults to None.
        optional_identifier (str | None, optional): String containing a description or any rellevant information about the experiment. Defaults to None.
    """

    path: str
    _dataset: h5py.Dataset
    measurement: Measurement | None = None
    _file: h5py.File | None = None

    def __init__(
        self,
        shape: list | tuple,
        loops: dict[str, np.ndarray] | dict[str, dict[str, Any]],
        platform: "Platform",
        experiment_name: str,
        db_manager: DatabaseManager,
        qprogram: QProgram | None = None,
        calibration: Calibration | None = None,
        optional_identifier: str | None = None,
    ):
        self.results: np.ndarray
        self.shape = [shape] if isinstance(shape, int) else shape
        self.loops = loops
        self.experiment_name = experiment_name
        self.db_manager = db_manager
        self.optional_identifier = optional_identifier
        self.platform = platform
        self.qprogram = qprogram
        self.calibration = calibration
        self._first_value = True

    def __enter__(self):
        """The execution while the with StreamArray is created.

        Returns:
            StreamArray: StreamArray class created
        """
        self.measurement = self.db_manager.add_measurement(
            experiment_name=self.experiment_name,
            experiment_completed=False,
            optional_identifier=self.optional_identifier,
            platform=self.platform.to_dict() if self.platform else None,
            qprogram=serialize(self.qprogram) if self.qprogram else None,
            calibration=serialize(self.calibration) if self.calibration else None,
            debug_file=self._get_debug() if self.platform and self.qprogram else None,
        )
        self.path = self.measurement.result_path

        # Save loops
        self._file = h5py.File(name=self.path, mode="w", libver="latest")
        self._file.swmr_mode = True

        g = self._file.create_group(name="loops", track_order=True)
        for loop_name, array in self.loops.items():
            if isinstance(array, dict):
                g_dataset = g.create_dataset(name=loop_name, data=array["array"])
                g_dataset.attrs["bus"] = array["bus"]
                g_dataset.attrs["parameter"] = array["parameter"]
                g_dataset.attrs["units"] = array["units"]
            else:
                g.create_dataset(name=loop_name, data=array)

        # Create results dataset only once
        if len(self.shape) == len(self.loops.keys()):
            self.results = np.zeros(shape=self.shape, dtype=np.complex128)
            if self._file:
                self._dataset = self._file.create_dataset("results", data=self.results, dtype=np.complex128)
        else:
            self.results = np.zeros(shape=self.shape)
            if self._file:
                self._dataset = self._file.create_dataset("results", data=self.results)
        self._file.flush()

        return self

    def __setitem__(
        self, key: tuple, value: np.ndarray[Any, np.dtype[np.floating]] | np.ndarray[Any, np.dtype[np.complexfloating]]
    ):
        """Sets and item by key and value in the dataset.

        Args:
            key (tuple): key for the item to save.
            value (float | np.complexfloating): value to save.
        """
        if self._file is not None and self._dataset is not None:
            self._dataset[key] = value
            self._file.flush()
        self.results[key] = value

    def __exit__(self, exc_type, exc_value, traceback):
        """Exits the context manager."""
        if self._file is not None:
            self._file.__exit__()
            self._file = None

        self.measurement = self.measurement.end_experiment(self.db_manager.Session, traceback)

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

    def _get_debug(self):
        bus_aliases = set(self.qprogram.buses)
        buses = {bus_alias: self.platform.buses.get(alias=bus_alias) for bus_alias in bus_aliases}
        instruments = {
            instrument
            for _, bus in buses.items()
            for instrument in bus.instruments
            if isinstance(instrument, QbloxModule)
        }
        if instruments and all(isinstance(instrument, QbloxModule) for instrument in instruments):
            compiled = self.platform.compile_qprogram(self.qprogram, self.calibration)[0]

            sequences = compiled.sequences
            for bus_alias, bus in buses.items():
                if bus.distortions:
                    for distortion in bus.distortions:
                        for waveform in sequences[bus_alias]._waveforms._waveforms:
                            sequences[bus_alias]._waveforms.modify(waveform.name, distortion.apply(waveform.data))

            lines = []
            for bus_alias, seq in sequences.items():
                lines.append(f"Bus {bus_alias}:")
                lines.append(str(seq._program))
                lines.append("")

            return "\n".join(lines)
        debug_exception = "Non Qblox machine."
        return debug_exception


def stream_results(shape: tuple, path: str, loops: dict[str, np.ndarray]):
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
                [1.   0.  ]]))
    """
    return RawStreamArray(shape=shape, path=path, loops=loops)


class RawStreamArray:
    """
    Allows for real time saving of results from an experiment.
    This class wraps a numpy array and adds a context manager to save results on real time while they are acquired by
    the instruments.
    Args:
        shape (tuple): results array shape.
        path (str): path to save results.
        loops (dict[str, np.ndarray]): dictionary with each loop name in the experiment as key and numpy array as values.
    """

    def __init__(self, shape: tuple, path: str, loops: dict[str, np.ndarray]):
        self.results: np.ndarray
        self.shape = shape
        self.path = path
        self.loops = loops
        self._file: h5py.File | None = None
        self._dataset = None
        self._first_value = True

    def __setitem__(
        self, key: tuple, value: np.ndarray[Any, np.dtype[np.floating]] | np.ndarray[Any, np.dtype[np.complexfloating]]
    ):
        """Sets and item by key and value in the dataset.
        Args:
            key (tuple): key for the item to save.
            value (float | np.complexfloating): value to save.
        """
        # Create results dataset only once
        if self._first_value:
            if isinstance(value[0], np.complexfloating):
                self.results = np.zeros(shape=self.shape, dtype=np.complex128)
                if self._file:
                    self._dataset = self._file.create_dataset("results", data=self.results, dtype=np.complex128)
            else:
                self.results = np.zeros(shape=self.shape)
                if self._file:
                    self._dataset = self._file.create_dataset("results", data=self.results)
            self._first_value = False

        if self._file is not None and self._dataset is not None:
            self._dataset[key] = value
        self.results[key] = value

    def __enter__(self):
        self._file = h5py.File(name=self.path, mode="w")
        # Save loops
        g = self._file.create_group(name="loops")
        for loop_name, array in self.loops.items():
            g.create_dataset(name=loop_name, data=array)

        self._first_value = True

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
