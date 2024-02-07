from dataclasses import dataclass


@dataclass
class BusSettings:
    """Dataclass with all the settings the buses of the platform need.

    Args:
        alias (str): Alias of the bus.
        system_control (dict): Dictionary containing the settings of the system control of the bus.
        distortions (list[dict]): List of dictionaries containing the settings of the distortions applied to each
            bus.
        delay (int, optional): Delay applied to all pulses sent in this bus. Defaults to 0.
    """

    alias: str
    instruments: list[str]
    channels: list[int | str | list[int | str] | None]
