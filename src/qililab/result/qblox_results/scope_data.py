""" Qblox Scope Data """

from dataclasses import dataclass


@dataclass
class ScopeData:
    """Scope data."""

    @dataclass
    class PathData:
        """Path data."""

        data: list[float]
        avg_cnt: int
        out_of_range: bool

    path0: PathData
    path1: PathData

    def __post_init__(self):
        """Change invalid name and cast to PathData class."""
        if isinstance(self.path0, dict) and isinstance(self.path1, dict):
            if "out-of-range" in self.path0:  # pylint: disable=unsupported-membership-test
                self.path0["out_of_range"] = self.path0.pop("out-of-range")
            self.path0 = self.PathData(**self.path0)  # pylint: disable=not-a-mapping
            if "out-of-range" in self.path1:  # pylint: disable=unsupported-membership-test
                self.path1["out_of_range"] = self.path1.pop("out-of-range")
            self.path1 = self.PathData(**self.path1)  # pylint: disable=not-a-mapping
