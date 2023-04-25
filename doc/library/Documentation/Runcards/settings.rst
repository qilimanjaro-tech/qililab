Settings
==========
As said, the settings section contains the main settings of the runcard. In our case, the platform we want to work with.
Here is an example of a complete settings section of a simple runcard:

::

    settings:
    id_: 0
    category: platform
    name: sauron
    delay_between_pulses: 0
    delay_before_readout: 40
    master_amplitude_gate: 1
    master_duration_gate: 20
    gates:
        - name: M
        amplitude: 1.0
        phase: 0
        duration: 6000
        shape:
            name: rectangular

Several settings have to be addressed to create a platform:

* ``id_`` : no ho se
* ``category`` :
* ``name`` : the name with which the platform is going to be referred as
* ``delay_between_pulses`` : the minimum delay between pulses
* ``delay_before_readout`` : the minimum delay before readout
* ``master_amplitude_gate`` : the default amplitude to work with
* ``master_duration_gate`` : the default duration of gates
* ``gates`` : the type of gates implemented

    * ``name`` : the name with which the gate is going to be referred as
    * ``amplitude`` : the amplitude of the pulse
    * ``phase`` : the phase of the pulse
    * ``duration`` : the duration of the pulse
    * ``shape`` : the shape of the pulse
