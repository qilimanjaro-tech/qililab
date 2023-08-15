Qililab Documentation
=====================

.. rst-class:: lead grey-text ml-2

   :Release: |release|

.. rst-class:: lead center

   Qililab is a generic and scalable quantum control library used for fast characterization
   and calibration of quantum chips. Qililab also offers the ability to execute high-level
   quantum algorithms with your quantum hardware.

.. grid:: 2

   .. grid-item-card:: Getting Started
      :link: getting_started/what_is_qililab.html
      :text-align: center
      :img-top: _static/rocket.png

      New to Qililab? Here you will find a description of Qililab's main concepts, together
      with some tutorials on how to install and start using Qililab in your laboratory!

   .. grid-item-card:: Fundamentals and Usage
      :link: fundamentals/platform.html
      :text-align: center
      :img-top: _static/book.png

      This section contains in-depth information about the key concepts of Qililab.

.. grid:: 2

   .. grid-item-card:: Contributor's Guide
      :link: development/contributing_to_qililab.html
      :text-align: center
      :img-top: _static/person.png

      Want to contribute to the codebase? Please check this guide to learn Qililab's best practices
      and code quality requirements.

   .. grid-item-card:: API Reference
      :link: code/ql.html
      :text-align: center
      :img-top: _static/code.png

      The API reference contains a detailed description of the functions, modules
      and classes included in Qililab.

.. toctree::
   :caption: Getting Started
   :maxdepth: 1
   :hidden:

   getting_started/what_is_qililab
   getting_started/installation
   getting_started/quickstart


.. toctree::
   :caption: Fundamentals and Usage
   :maxdepth: 1
   :hidden:

   fundamentals/platform
   fundamentals/runcard
   fundamentals/qprogram
   fundamentals/transpilation

.. toctree::
   :caption: Contributor's Guide
   :maxdepth: 1
   :hidden:

   development/contributing_to_qililab

.. toctree::
   :caption: API Reference
   :maxdepth: 1
   :hidden:

   code/ql
   code/chip
   code/drivers
   code/experiment
   code/platform
   code/pulse
   code/qprogram
   code/result
   code/transpiler
   code/waveforms
