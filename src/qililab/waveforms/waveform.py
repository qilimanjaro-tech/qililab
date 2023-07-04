from typing import Protocol


class Waveform(Protocol):
    duration: int
    resolution: int

    def envelope(self):
        pass
