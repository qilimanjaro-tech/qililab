from pathlib import Path

from qililab.waveforms import IQPair, Waveform
from qililab.yaml import yaml


@yaml.register_class
class Calibration:
    def __init__(self) -> None:
        self.operations: dict[str, dict[str, Waveform | IQPair]] = {}

    def add_operation(self, bus: str, operation: str, waveform: Waveform | IQPair):
        if bus not in self.operations:
            self.operations[bus] = {}
        self.operations[bus][operation] = waveform

    def get_operation(self, bus: str, operation: str):
        if bus not in self.operations or operation not in self.operations[bus]:
            raise TypeError()
        return self.operations[bus][operation]

    def dump(self, file: str):
        path = Path(file) if file.endswith(".yml") or file.endswith(".yaml") else Path(f"{file}.yml")

        with open(file=path, mode="w", encoding="utf-8") as stream:
            yaml.dump(data=self, stream=stream)

        return str(path)

    @classmethod
    def load(cls, file: str):
        with open(file=file, mode="r", encoding="utf8") as stream:
            data = yaml.load(stream)
        if not isinstance(data, cls):
            raise TypeError()
        return data
