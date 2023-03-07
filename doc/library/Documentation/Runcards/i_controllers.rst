Instrument Controllers
+++++++++++++++++++++++++
Instrument controllers, as the name suggests, are from where the instruments are controlled.
**explicar que hay algunos instrumentos que van solos i otros en grupos (creo). expliacar alguna cosa mas supongo.**

As in the instrument section, every type of instrument controller has its own specs to determine.
Below there are some examples of the different instrument controllers implemented in qililab.

Qblox Cluster
---------------
::

  - name: qblox_cluster
    id_: 1
    alias: cluster_controller_0
    category: instrument_controller
    subcategory: multiple_instruments
    reference_clock: internal
    connection:
    name: tcp_ip
    address: 192.168.1.2
    modules:
    - awg: QCM_0
        slot_id: 1
    - awg: QCM_1
        slot_id: 2
    - awg: QCM_2
        slot_id: 3
    - awg_dac: QRM_0
        slot_id: 4

Qblox Spi Rack
-----------------
::

  - name: qblox_spi_rack
    id_: 7
    alias: qblox_spi_rack
    category: instrument_controller
    subcategory: multiple_instruments
    connection:
      name: usb
      address: /dev/ttyACM0
    modules:
      - current_source: S4g_0
        slot_id: 1
      - current_source: S4g_1
        slot_id: 2

Rohde Schwarz
-----------------
::

  - name: rohde_schwarz
    id_: 2
    alias: rohde_schwarz_controller_drive_q0
    category: instrument_controller
    subcategory: single_instrument
    connection:
      name: tcp_ip
      address: 192.168.0.10
    modules:
      - signal_generator: rs_0
        slot_id: 1
