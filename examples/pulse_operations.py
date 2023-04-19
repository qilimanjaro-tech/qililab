import matplotlib.pyplot as plt

from qililab import DRAGPulse, GaussianPulse, SquarePulse
from qililab.utils import Waveforms

square: SquarePulse = SquarePulse(amplitude=1.0, duration=40, phase=0, frequency=8.4e9)
gaussian = GaussianPulse(amplitude=1.0, duration=40, phase=90, frequency=8.4e9, sigma=0.5)
drag = DRAGPulse(amplitude=1.0, duration=40, phase=90, frequency=8.4e9, sigma=0.5, delta=5)

envelope = drag.envelope(resolution=0.5)
print(envelope)

waveforms = drag.modulated_waveforms(resolution=0.5)

plt.plot(envelope)
plt.plot(waveforms.i)
plt.plot(waveforms.q)
plt.show()
