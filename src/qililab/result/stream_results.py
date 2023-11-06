import h5py
import numpy as np


class StreamArray:
    """Allows for real time saving of results from an experiment.

    This class wraps a numpy array and adds a context manager to save results on real time while they are acquired by
    the instruments.

    Args:
        shape (ndarray.shape): results array shape.
        path (str): path to save results.
        loops (dict[str, ndarray]): dictionary with each loop name in the experiment as key and numpy array as values.
    """

    def __init__(self, shape, path, loops):
        self.results = np.empty(shape=shape)
        self.path = path
        self.loops = loops
        self.file: h5py.File | None = None
        self.dataset = None

    def __setitem__(self, key, value):
        """Sets and item by key and value in the dataset.

        Args:
            key (str): key for the item to save.
            value (float): value to save.
        """
        if self.file is not None:
            self.dataset[key] = value
        self.results[key] = value

    def __enter__(self):
        """Enters the context manager."""
        self.file = h5py.File(name=self.path, mode="w")
        # Save loops
        g = self.file.create_group(name="loops")
        for loop_name, array in self.loops.items():
            g.create_dataset(name=loop_name, data=array)
        # Save results
        self.dataset = self.file.create_dataset("results", data=self.results)

    def __exit__(self, *args):
        """Exits the context manager."""
        if self.file is not None:
            self.file.__exit__()
            self.file = None

    def __getitem__(self, index):
        """Gets item by index.

        Args:
            index (int): item's index.
        """
        return self.results[index]

    def __len__(self):
        return len(self.results)

    def __iter__(self):
        """Gets length of results."""
        return iter(self.results)

    def __str__(self):
        """Gets string representation of results."""
        return str(self.results)

    def __repr__(self):
        """Gets string representation of results."""
        return repr(self.results)

    def __contains__(self, item):
        """Returns if an item is contained in results.

        Args:
            item (dict): item

        Returns:
            bool: True if an item is contained in results.
        """
        return item in self.results
