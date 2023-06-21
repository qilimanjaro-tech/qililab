from qililab._instruments import QililabPulsar
from qililab.pulse import Pulse, PulseBusSchedule
from qililab.pulse.pulse_event import PulseEvent

pulsar = QililabPulsar("pulsar", "...")
pulsar.set("reference_source", True)
