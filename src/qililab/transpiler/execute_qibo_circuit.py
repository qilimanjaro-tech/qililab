from qibo.models import Circuit

import qililab as ql


def execute_qibo_circuit(circuit: Circuit, runcard_name: str, experiment_name: str):
    """Transpile a qibo circuit to native gates and run it with qililab

    Args:
        circuit (Circuit): qibo circuit
        runcard_name (str): name of the runcard to be loaded
        experiment_name (str): name of the experiment

    Returns:
        Results : ``Results`` class containing the experiment results
    """

    # create platform
    # TODO how is the platform build if this is run on remote(?)
    platform = ql.build_platform(name=runcard_name)  # FIXME based on the comment above
    platform.connect(manual_override=False)  # if manual_override=True, it surpasses any blocked connection
    platform.initial_setup()  # Sets all the values of the Runcard to the connected instruments
    platform.turn_on_instruments()  # Turns on all instruments

    settings = ql.ExperimentSettings(
        hardware_average=1,
        repetition_duration=0,
        software_average=1,
    )

    options = ql.ExperimentOptions(
        loops=[],  # loops to run the experiment
        settings=settings,  # experiment settings
        name=experiment_name,  # name of the experiment (it will be also used for the results folder name)
    )

    # transpile and optimize circuit
    ql.translate_circuit(circuit, optimize=True)

    sample_experiment = ql.Experiment(
        platform=platform,  # platform to run the experiment
        circuits=[circuit],  # circuits to run the experiment
        options=options,  # experiment options
    )

    # build and run the experiment
    sample_experiment.build_execution()
    results = sample_experiment.run()

    platform.disconnect()  # TODO do we need to disconnect?

    return results
