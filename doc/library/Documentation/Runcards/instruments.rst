Instruments
++++++++++++
On this part of the runcard we determine the instruments at our disposal and the characteristics of each of them.
There are different types of instruments and some specs have to be determined via the runcard.

Below there are some examples of the different instruments implemented in qililab.

Rohde Schwarz
-----------------
::

  - name: rohde_schwarz
    alias: rs_3
    id_: 7
    category: signal_generator
    firmware: 4.30.046.295
    power: 15
    frequency: 6.53392e+09

S4g
---------
::

  - name: S4g
    alias: S4g_0
    id_: 10
    category: current_source
    firmware: None
    current: [0.0, 0.0, 0.0, 0.0]
    ramping_enabled: [true, true, true, true]
    ramp_rate: [0.0001, 0.0001, 0.0001, 0.0001]
    span: ["range_max_bi", "range_max_bi", "range_max_bi", "range_max_bi"]
    dacs: [1, 2, 3, 4]

QCM
---------
::

  - name: QCM
    alias: QCM_0
    id_: 0
    category: awg
    firmware: 0.7.0
    num_sequencers: 2
    num_bins: [1, 1]
    intermediate_frequencies: [1.e+08, 1.e+08]
    gain: [1, 1]
    gain_imbalance: [0, 0]
    phase_imbalance: [0, 0]
    offset_i: [0, 0]
    offset_q: [0, 0]
    hardware_modulation: [true, true]
    sync_enabled: [true, true]

QRM
-------
::

  - name: QRM
    alias: QRM_0
    id_: 3
    category: awg_dac
    firmware: 0.7.0
    num_sequencers: 5
    intermediate_frequencies: [2.e+07, 2.e+07, 2.e+07, 2.e+07, 2.e+07]
    gain: [1, 1, 1, 1, 1]
    gain_imbalance: [0, 0, 0, 0, 0]
    phase_imbalance: [0, 0, 0, 0, 0]
    offset_i: [0, 0, 0, 0, 0]
    offset_q: [0, 0, 0, 0, 0]
    hardware_modulation: [true, true, true, true, true]
    sync_enabled: [true, true, true, true, true]
    num_bins: [1, 1, 1, 1, 1]
    scope_acquire_trigger_mode:
      [sequencer, sequencer, sequencer, sequencer, sequencer]
    scope_hardware_averaging: [false, false, false, false, false]
    sampling_rate: [1.e+09, 1.e+09, 1.e+09, 1.e+09, 1.e+09]
    hardware_integration: [true, true, true, true, true]
    hardware_demodulation: [true, true, true, true, true]
    integration_length: [2000, 2000, 2000, 2000, 2000]
    acquisition_delay_time: 100
    integration_mode: [ssb, ssb, ssb, ssb, ssb]
    sequence_timeout: [1, 1, 1, 1, 1]
    acquisition_timeout: [1, 1, 1, 1, 1]
    scope_store_enabled: [false, false, false, false, false]
