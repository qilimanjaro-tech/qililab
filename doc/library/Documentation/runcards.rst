Runcards
==============

Runcards are a convenient method to tell qililab our experimental setup.

They are files in the format ``.yml`` that are imported as dictionaries on qililab, here is a schematic example of a runcard.

.. note::
    The example below is a schematic representation of a basic runcard, wherever it is ``...`` : should go more lines of code that refer to the settings of each part of the runcard.

.. code-block:: python
    :caption: Runcard Scheme

    settings:
    id_: 0
    category: platform
    name: sauron
    ...

    schema:
        chip:
            id_: 0
            category: chip
            ...

        instruments:
            - name: QRM
            alias: QRM
            id_: 1
            ...

        buses:
            - id_: 1
            name: time_domain_readout_bus
            category: bus
            ...

        instrument_controllers:
            - name: qblox_cluster
            id_: 1
            alias: cluster_controller_0
            category: instrument_controller
            ...


As shown in the example every runcard has a *settings* section and a *schema* section (according to the indentation).

The *settings* refer to the general setting of the platform you want to create and the *schema* refers to the elements and how are they connected in the circuit.

To see in more detail each part of a runcard, check out:

* :doc:`Settings<Runcards/settings>`
* Schema:

  * :doc:`Chip<Runcards/chip>`

  * :doc:`Instruments<Runcards/instruments>`

  * :doc:`Buses<Runcards/buses>`

  * :doc:`Instrument Controllers<Runcards/i_controllers>`

.. toctree::
   :maxdepth: 4
   :hidden:

   Runcards/settings
   Runcards/chip
   Runcards/instruments
   Runcards/buses
   Runcards/i_controllers

