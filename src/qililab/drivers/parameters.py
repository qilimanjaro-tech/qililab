""" Contains parameters for the drivers
"""

# TESTING this feature


class LO:
    """Local Oscillator"""

    frequency = "lo_frequency"


class Attenuator:  # This is the same name as the interface but I felt like naming it ATT would make things complicated
    attenuation = "attenuation"


class Drivers:
    lo = LO()
    attenuator = Attenuator()


drivers = Drivers()
