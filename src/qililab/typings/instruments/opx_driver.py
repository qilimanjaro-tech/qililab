# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Quantum Machines OPX driver."""
from qcodes.utils.dataset.doNd import do0d
from qcodes import load_or_create_experiment
from qualang_tools.external_frameworks.qcodes.opx_driver import OPX as QuantumMachinesOPX
from qililab.qprogram import QProgram
from qililab.typings.instruments.device import Device


class OPXDriver(QuantumMachinesOPX, Device):
    """Typing class of the QCoDeS driver for the Quantum Machines OPX instrument."""

    def execute(self, program: QProgram):
        experiment = load_or_create_experiment(
            experiment_name="opx_experiment", sample_name="opx_sample"
        )
        # Execute program
        self.qua_program = program
        do0d(
            self.run_exp,
            self.resume,
            self.get_measurement_parameter(),
            self.halt,
            do_plot=True,
            exp=experiment,
        )
