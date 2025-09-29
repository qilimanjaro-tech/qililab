.. _runcards:

Runcards
========

The runcards are the serialized :class:`ql.Platform`'s in the form of dictionaries.

They contain all the laboratory information, settings and parameters, concretely they contain information about the:

- Gates transpilation

- Instruments

- Buses

|

Normally, in order to save the laboratory settings and its calibrated parameters, runcards get saved as YAML files to be retrieved later on.

Runcard dictionary structure:
------------------------------

Such dictionaries have the following main structure:

.. code-block:: python3

    {
        "name": name,                                           # str
        "gates_settings": gates_settings,                       # dict
        "chip": chip,                                           # dict
        "buses": buses,                                         # list[dict]
        "instruments": instruments,                             # list[dict]
        "instrument_controllers": instrument_controllers        # list[dict]
    }


Runcard YAML file example:
---------------------------

.. code-block:: yaml

    name: galadriel_soprano_master

    gates_settings:
        delay_between_pulses: 0
        delay_before_readout: 4
        timings_calculation_method: as_soon_as_possible
        reset_method: passive
        passive_reset_duration: 100
        minimum_clock_time: 4
        operations: []
        gates:
            M(0):
                -   bus: feedline_bus # alias of the bus
                    pulse:
                        amplitude: 1.0
                        phase: 0
                        duration: 2000
                        shape:
                            name: rectangular
            Drag(0):
                -   bus: drive_line_q0_bus
                    pulse:
                        amplitude: 1.0
                        phase: 0
                        duration: 20
                        shape:
                            name: drag
                            num_sigmas: 4
                            drag_coefficient: 0.0

            M(1):
                -   bus: feedline_bus # alias of the bus
                    pulse:
                        amplitude: 1.0
                        phase: 0
                        duration: 2000
                        shape:
                            name: rectangular
            Drag(1):
                -   bus: drive_line_q1_bus
                    pulse:
                        amplitude: 1.0
                        phase: 0
                        duration: 20
                        shape:
                            name: drag
                            num_sigmas: 4
                            drag_coefficient: 0.0


            CZ(0,1):
                -   bus: flux_line_q0_bus
                    pulse:
                        amplitude: 1.0
                        phase: 0
                        duration: 101
                        shape:
                            name: snz
                            t_phi: 1
                            b: 0.5
                -   bus: flux_line_q1_bus # park pulse
                    wait_time: 20
                    pulse:
                        amplitude: 1.0
                        phase: 0
                        duration: 121
                        shape:
                            name: rectangular

    chip:
        nodes:
            -   name: qubit
                alias: qubit_0
                qubit_index: 0
                frequency: 4.92e+09
                nodes: [qubit_1, resonator_q0, drive_line_q0, flux_line_q0]
            -   name: qubit
                alias: qubit_1
                qubit_index: 1
                frequency: 5.0e+09
                nodes: [qubit_0, resonator_q1, drive_line_q1, flux_line_q1]
            -   name: resonator
                alias: resonator_q0
                frequency: 7.1e+09
                nodes: [qubit_0, feedline_input, feedline_output]
            -   name: resonator
                alias: resonator_q1
                frequency: 7.2e+09
                nodes: [qubit_1, feedline_input, feedline_output]
            -   name: port
                alias: drive_line_q0
                nodes: [qubit_0]
                line: drive
            -   name: port
                alias: drive_line_q1
                nodes: [qubit_1]
                line: drive
            -   name: port
                alias: flux_line_q0
                nodes: [qubit_0]
                line: flux
            -   name: port
                alias: flux_line_q1
                nodes: [qubit_1]
                line: flux
            -   name: port
                alias: feedline_input
                nodes: [resonator_q0, resonator_q1]
                line: feedline_input
            -   name: port
                alias: feedline_output
                nodes: [resonator_q0, resonator_q1]
                line: feedline_output

    buses:
        - alias: feedline_bus
            system_control:
            name: readout_system_control
            instruments: [QRM1, rs_1]
            port: feedline_input
            distortions: []
        - alias: drive_line_q0_bus
            system_control:
            name: system_control
            instruments: [QCM-RF1]
            port: drive_line_q0
            distortions: []
        - alias: flux_line_q0_bus
            system_control:
            name: system_control
            instruments: [QCM1]
            port: flux_line_q0
            distortions: []
        - alias: drive_line_q1_bus
            system_control:
            name: system_control
            instruments: [QCM-RF1]
            port: drive_line_q1
            distortions: []
        - alias: flux_line_q1_bus
            system_control:
            name: system_control
            instruments: [QCM1]
            port: flux_line_q1
            distortions:
            - name: bias_tee
                tau_bias_tee: 11000
            - name: lfilter
                a:
                [
                    4.46297950e-01,
                    -4.74695321e-02,
                    -6.35339660e-02,
                    6.90858657e-03,
                    7.21417336e-03,
                    1.34171108e-02,
                ]
                b: [1.]
                norm_factor: 1.

    instruments:
        -   name: QRM
            alias: QRM1
            firmware: 0.7.0
            num_sequencers: 2
            out_offsets: [0, 0]
            awg_sequencers:
                -   identifier: 0
                    chip_port_id: feedline_input
                    qubit: 0
                    outputs: [0, 1]
                    gain_i: .5
                    gain_q: .5
                    offset_i: 0
                    offset_q: 0
                    weights_i: [1., 1., 1., 1., 1.] # to calibrate
                    weights_q: [1., 1., 1., 1., 1.] # to calibrate
                    weighed_acq_enabled: False
                    threshold: 0.5
                    threshold_rotation: 0.0
                    num_bins: 1
                    intermediate_frequency: 10.e+06
                    gain_imbalance: 1.
                    phase_imbalance: 0
                    hardware_modulation: true
                    scope_acquire_trigger_mode: sequencer
                    scope_hardware_averaging: true
                    sampling_rate: 1.e+09
                    integration_length: 2000
                    integration_mode: ssb
                    sequence_timeout: 1
                    acquisition_timeout: 1
                    hardware_demodulation: true
                    scope_store_enabled: false
                -   identifier: 1
                    chip_port_id: feedline_input
                    qubit: 1
                    outputs: [0, 1]
                    gain_i: .5
                    gain_q: .5
                    offset_i: 0
                    offset_q: 0
                    weights_i: [1., 1., 1., 1., 1.] # to calibrate
                    weights_q: [1., 1., 1., 1., 1.] # to calibrate
                    weighed_acq_enabled: False
                    threshold: 0.5
                    threshold_rotation: 0.0
                    num_bins: 1
                    intermediate_frequency: 20.e+06
                    gain_imbalance: 1.
                    phase_imbalance: 0
                    hardware_modulation: true
                    scope_acquire_trigger_mode: sequencer
                    scope_hardware_averaging: true
                    sampling_rate: 1.e+09
                    integration_length: 2000
                    integration_mode: ssb
                    sequence_timeout: 1
                    acquisition_timeout: 1
                    hardware_demodulation: true
                    scope_store_enabled: false
        -   name: QCM-RF
            alias: QCM-RF1
            firmware: 0.7.0
            num_sequencers: 2
            out0_lo_freq: 6.5e+09
            out0_lo_en: true
            out0_att: 0
            out0_offset_path0: 0.
            out0_offset_path1: 0.0
            out1_lo_freq: 6.7e+09
            out1_lo_en: true
            out1_att: 0
            out1_offset_path0: 0.
            out1_offset_path1: 0.
            awg_sequencers:
                -   identifier: 0
                    chip_port_id: drive_line_q0
                    outputs: [0, 1]
                    gain_i: 0.1
                    gain_q: 0.1
                    offset_i: 0. # -0.012
                    offset_q: 0.
                    num_bins: 1
                    intermediate_frequency: 10.e+06
                    gain_imbalance: 0.940
                    phase_imbalance: 14.482
                    hardware_modulation: true
                -   identifier: 1
                    chip_port_id: drive_line_q1
                    outputs: [2, 3]
                    gain_i: 1
                    gain_q: 1
                    offset_i: 0
                    offset_q: 0
                    num_bins: 1
                    intermediate_frequency: 20.e+06
                    gain_imbalance: 0.5
                    phase_imbalance: 0
                    hardware_modulation: true
        -   name: QCM
            alias: QCM1
            firmware: 0.7.0
            num_sequencers: 2
            out_offsets: [0.0, 0.0, 0.0, 0.0]
            awg_sequencers:
                -   identifier: 0
                    chip_port_id: flux_line_q0
                    outputs: [0, 1]
                    gain_i: 0.1
                    gain_q: 0.1
                    offset_i: 0.
                    offset_q: 0.
                    num_bins: 1
                    intermediate_frequency: 10.e+06
                    gain_imbalance: .5
                    phase_imbalance: 0.
                    hardware_modulation: true
                -   identifier: 1
                    chip_port_id: flux_line_q1
                    outputs: [1, 0]
                    gain_i: 1
                    gain_q: 1
                    offset_i: 0
                    offset_q: 0
                    num_bins: 1
                    intermediate_frequency: 0.
                    gain_imbalance: 0.5
                    phase_imbalance: 0
                    hardware_modulation: true
        -   name: RS
            alias: rs_1
            firmware: 4.2.76.0-3.30.046.294
            power: 16
            frequency: 8.0726e+09
            rf_on: true
        -   name: mini_circuits
            alias: attenuator
            firmware: None
            attenuation: 32

    instrument_controllers:
        -   name: cluster
            alias: cluster_controller_0
            reference_clock: internal
            connection:
            name: tcp_ip
            address: 192.178.1.10
            modules:
                -   alias: QRM1
                    slot_id: 12
                -   alias: QCM-RF1
                    slot_id: 6
                -   alias: QCM1
                    slot_id: 14
                -   alias: QCM2
                    slot_id: 14
        -   name: RS
            alias: RS_controller_0
            reference_clock: internal
            connection:
            name: tcp_ip
            address: 192.178.1.21
            modules:
                -   alias: rs_1
                    slot_id: 0
        -   name: mini_circuits
            alias: attenuator_controller_0
            connection:
            name: tcp_ip
            address: 192.188.1.39
            modules:
                -   alias: attenuator
                    slot_id: 0
