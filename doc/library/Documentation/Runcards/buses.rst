Buses
+++++++++++++++++++++++++
Buses describes an abstraction of **a physical line** in the lab setup. 
It contains all required equipment necessary to communicate from the measurement **PC to a target** (Qubit, Resonator or Coupler) **via a chip port**.

Each bus is a collection of instuments connected to a given port and stores the schedule of pulses that will be send to that port.
In the `buses` section of the runcard, we create thous lines by grouping different instruments to a bus, replicating the setup of the lab.

Every bus may have a *system controller*. There are several types of *sistem controllers* in regard to the fuctionality of the bus.

Time Domain
**************
These type of system controller are for buses that needs to perform **sequencies** of pusles in contrast to the :ref:`continous buses <cont>`, **time domain** must be time aware as they have to be able to generate a sequence of an specific order and timing.

Baseband Bus
---------------
The system control contains an **AWG** and a **Current Source**

Control Bus
-------------
The system control contains an **AWG** and a **Signal Generator**
|

.. image:: ../../img/control_bus.png
    :align: center

|

::

  - id_: 5
    name: time_domain_control_bus
    category: bus
    bus_category: time_domain
    bus_subcategory: control
    alias: drive_line_q2_bus
    system_control:
        id_: 7
        name: time_domain_control_system_control
        category: system_control
        system_control_category: time_domain
        system_control_subcategory: control
        awg: QCM
        signal_generator: rs_1
    port: 12

Readout Bus
---------------
The system control contains an **AWG**, a **Signal Generator** and an **ADC**
|

.. image:: ../../img/readout_bus.png
    :align: center


|

::

  - id_: 1
    name: time_domain_readout_bus
    category: bus
    bus_category: time_domain
    bus_subcategory: readout
    alias: feedline_input_output_bus
    system_control:
    id_: 1
    name: time_domain_readout_system_control
    category: system_control
    system_control_category: time_domain
    system_control_subcategory: readout
    awg: QRM
    signal_generator: rs_1
    port: 100

.. _cont:

Continous
***********
These type of system controller are for buses that doesn't require any pulse sequence, just the system control is turned on and setup with the desired parameters. There is no time awareness it is always on.

Current bias Bus
--------------------
The system control contains a **Current Source**
::

  - id_: 2
    name: continuous_current_bias_bus
    category: bus
    bus_category: continuous
    bus_subcategory: current_bias
    alias: flux_bias_line_q4_bus
    system_control:
      id_: 4
      name: continuous_current_bias_system_control
      category: system_control
      system_control_category: continuous
      system_control_subcategory: current_bias
      current_source: S4g_1
    port: 5

Microwave bias Bus
-----------------------
The system control contains a **Signal generator**

Readout Bus
---------------
The system control contains a **VNA**

Simulated
*****************
Only ment for simulation
::

  - id_: 0
    category: bus
    subcategory: control
    system_control:
      id_: 0
      category: system_control
      subcategory: simulated_system_control
      qubit: csfq4jj
      qubit_params:  # qubit parameters
        n_cut: 10
        phi_x: 6.28318530718 # 2*pi
        phi_z: -0.25132741228 # -0.08*pi
      drive: zport
      drive_params:  # driving hamiltonian parameters
        dimension: 10
      resolution: 0.01
      store_states: True
    port: 0
