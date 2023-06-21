from qililab._instruments import AWGSequencer
from qililab.pulse import Pulse, PulseBusSchedule
from qililab.pulse.pulse_event import PulseEvent

awg = AWGSequencer(name="seq", address="...", output_i=1, output_q=0)
#awg.set("gain", 3)

"""port= 2
timeline: list[PulseEvent] = []
pulse_bus_schedule = PulseBusSchedule(port=port, timeline=timeline)
nshots = 1
repetition_duration = 1000
num_bins = 1
awg.execute(pulse_bus_schedule=pulse_bus_schedule, nshots=nshots, repetition_duration=repetition_duration, num_bins=num_bins)"""