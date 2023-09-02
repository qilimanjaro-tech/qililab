"""
This module contains all the methods and classes used for automatic calibration.
A high level view of how the automatic calibration algorithm works and how the different classes and methods are used 
can be found in this Notion page: https://www.notion.so/qilimanjaro/Automatic-qubit-calibration-algorithm-architecture-73133434c9c04b9cb8f6bd178d0b06d9?pvs=4

**Examples** are found in the `qililab/src/qililab/automatic_calibration/examples` folder

**Things left to do to improve this module:**

    - Of course, the TODOs and FIXMEs in the code.

    - In the examples, each experiment has a custom analysis function. There should be a more generic analysis function that, based
      in the arguments it receives, analyzes the data for a specific experiment. To write this generic analysis function, a developer 
      can follow the structure of the custom ones defined in the examples, since they are all very similar and follow more or less
      the same steps. This similarity was introduced on purpose to make the transition to a generic analysis function easier.
    - The way the algorithm is implemented now, the optimal parameters found by the nodes are updated in the platform using 
      `Platform.set_parameter()`, but when the program terminates they are lost. In the `Controller.run_automatic_calibration()' method, 
      before returning, the parameters of the platform should be saved either in a "calibration file" or directly used to overwrite
      the old parameters in the runcard.
    - I have tested the automatic calibration code manually with dummy data, for the most part without connecting to the actual hardware. 
      I tried to cover as many edge cases as possible, and I haven't found any issues. However, of course, unit tests must be written 
      for this code, and it must be tested more on hardware.
    - I have tested the code on hardware (galadriel) by running `qililab/automatic_calibration/examples/single_node_automatic_calibration_example.py`.
      The automatic calibration logic worked without any issues, but the data returned by the experiment was not good. After trying a lot of variations
      in the runcard's parameters, I believe that the issue must lie in the `Platform.execute()` method. I strongly recommend testing `Platform.execute()`
      on hardware before continuing to test the automatic calibration code on hardware.
    - As can be seen in the examples, the user can be shown the plot obtained from the experimental data, and decide if the data shown in the plot is 
      satisfactory or not. An important improvement would be allowing the user more options when evaluating the plot: for example, in the AllXY experiment,
      the plot can hint to what has gone well and wrong in the calibration sequence. The engineers who use the automatic calibration algorithm are train
      to recognize these hints and should be allowed to point the algorithm in the right direction, instead of just replying yes or no when asked 
      if the plot is good. 
      See this paper for more details on this AllXY example: https://arxiv.org/pdf/1311.6759.pdf
    - Machine learning could be very useful in some parts of the algorithm. An ML model, trained in collaboration with the engineers who handle calibration,
      could recognize a good plot from a bad one. Consider the ALLXY example from the previous point: the ML model could do what the engineer does in that
      example, making automatic calibration even more efficient. Again, see the paper linked above for more information.
        
        
Finally, some **unsolicited advice** to whomever takes over the development of automatic calibration: after skimming the docs of this code and getting an idea 
of what qubit calibration does, I'd recommend spending one day with the hardware team and just observing as they calibrate. It will give you an idea of
how useful it is to automate calibration, and most importantly what is the workflow: how they change things if a calibration experiment doesn't give good 
results, how the different parameters of the runcard affect the data, what the patterns are, etc...

If something in the code, the docs, or the examples is completely obscure and incomprehensible, feel free to contact me at *mparadina10* *at* *gmail* *dot* *com* and I'll try to help.

Good luck!


.. currentmodule:: qililab.automatic_calibration

Calibration-related methods
~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~visualize_calibration_graph
    ~get_timestamp
    ~is_timeout_expired
    ~get_random_values
    ~get_raw_data 
    ~get_iq_from_raw
    ~plot_iq
    ~plot_fit
    ~get_most_recent_folder
    
Controller class
~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~Controller


CalibrationNode Class
~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: api

    ~CalibrationNode

"""

from .calibration_node import CalibrationNode
from .controller import Controller
from .calibration_utils.calibration_utils import get_timestamp, is_timeout_expired, get_random_values, get_raw_data, get_iq_from_raw, plot_iq, plot_fit, get_timestamp, get_random_values, get_most_recent_folder, visualize_calibration_graph