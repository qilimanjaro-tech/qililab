Instrument Controllers
+++++++++++++++++++++++++
Instrument controllers, are the way qililab has to **communicate** with each **intrument** is connected to.
Each instrument must be connected to an instrument controller that serves as the *drivers* of said instrument.
So, an instrument controller, serves as a mediatior between our desire instrucctions and the actual actions of an instrument.

An instrument controller can contain one or multiple instruments. The option ``subcategory:`` is utilized to determinate wether is a ``single_instrumet`` or a ``multiple_instruments``.
For a multiple instument, each instument is assigned in the section ``modules:``

As in the :doc:`instrument<instruments>` section, every type of instrument controller has its own specs to determine.
Below there are **some examples** of the different instrument controllers implemented in qililab.

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
