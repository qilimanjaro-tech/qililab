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

import re

import numpy as np
import plotly.graph_objects as go


class QbloxDraw:
    def _call_handlers(self, program_line, param, register, data_draw, waveform_seq):
        """Calls the handlers.

        Args:
            program_line (tuple): line of the Q1ASM program parsed.
            param (dictionary): parameters of the bus (IF, phase, offset, hardware modulation).
            register (dictionary): registers of the Q1ASM.
            data_draw (list): nested list for each waveform, data points until current time.
            waveform_seq (Dict items): waveform data as provided by the sequencer
        """

        action_type = program_line[0]
        if action_type == "set_freq":
            param = self._handle_freq_phase_draw(program_line, param, register, "intermediate_frequency")
        elif action_type == "set_ph":
            param = self._handle_freq_phase_draw(program_line, param, register, "phase")
        elif action_type == "reset_ph":
            param = self._handle_reset_phase_draw(param)
        elif action_type == "set_awg_offs":
            param = self._handle_offset(program_line, param)
        elif action_type == "set_awg_gain":
            param = self._handle_gain_draw(program_line, param, register)
        elif action_type == "play":
            data_draw = self._handle_play_draw(data_draw, program_line, waveform_seq, param)
        elif action_type == "wait":
            data_draw = self._handle_wait_draw(data_draw, program_line, param)
        elif action_type == "upd_param":
            data_draw = self._handle_wait_draw(data_draw, program_line, param)
        elif action_type == "add":
            self._handle_add_draw(register, program_line)
        return param, register, data_draw

    def _calculate_scaling_and_offsets(self, param, i_or_q):
        if i_or_q == "I":
            scaling_factor, max_voltage = self._get_scaling_factors(
                param, param.get("q1asm_offset_i", 0), param.get("ac_offset_i", 0)
            )
            gain = param.get("gain_i", 1)
        elif i_or_q == "Q":
            scaling_factor, max_voltage = self._get_scaling_factors(
                param, param.get("q1asm_offset_q", 0), param.get("ac_offset_q", 0)
            )
            gain = param.get("gain_q", 1)
        return scaling_factor, max_voltage, gain

    def _get_scaling_factors(self, param, dynamic_off, ac_off):
        if param["hardware_modulation"]:
            return (
                (param["max_voltage"] / (np.sqrt(2)), param["max_voltage"] / (np.sqrt(2)))
                if dynamic_off == 0 and ac_off == 0
                else (param["max_voltage"] / (np.sqrt(2)), param["max_voltage"])
            )
        return (param["max_voltage"], param["max_voltage"])  # (scaling factor, max voltage)

    def _handle_play_draw(self, data_draw, program_line, waveform_seq, param):
        """Play a waveform by appending the stored data list.

        Args:
            data_draw (list): nested list for each waveform, data points until current time.
            program_line (tuple): line of the Q1ASM program parsed with a play instruction.
            waveform_seq (Dict items): waveform data as provided by the sequencer
            param (dictionary): parameters of the bus (IF, phase, offset, hardware modulation).

        Returns:
            Appended data_draw considering the play, the gain and the offset.
            And appended the IF and phase keys of the param dictionary. Each of these is a np array where 1 data point represents 1 ns (same as the waveforms).
        """
        output_path1, output_path2, _ = map(int, program_line[1].split(","))
        # modify and store the wf data
        for idx, output_path in enumerate([output_path1, output_path2]):
            for _, waveform_value in waveform_seq:
                index = waveform_value["index"]
                if index == output_path:
                    iq = "I" if idx == 0 else "Q"
                    scaling_factor, max_voltage, gain = self._calculate_scaling_and_offsets(param, iq)
                    scaled_array = np.array(waveform_value["data"]) * scaling_factor
                    modified_waveform = np.clip(scaled_array * gain, -max_voltage, max_voltage)
                    data_draw[idx] = np.append(data_draw[idx], modified_waveform)

        # extend the IF and phase by the length of the wf
        for key in ["intermediate_frequency", "phase", "q1asm_offset_i", "q1asm_offset_q"]:
            if param.get(f"{key}_new", False) is True:
                param[key].extend([param[key][-1]] * (len(scaled_array) - 1))
                param[f"{key}_new"] = False
            else:
                param[key].extend([param[key][-1]] * len(scaled_array))
        return data_draw

    def _handle_wait_draw(self, data_draw, program_line, param):
        """Play a wwait by appending the stored data list.

        Args:
            data_draw (list): nested list for each waveform, data points until current time.
            program_line (tuple): line of the Q1ASM program parsed with a wait instruction.
            param (dictionary): parameters of the bus (IF, phase, offset, hardware modulation).

        Returns:
            Appended data_draw considering the wait and the offset.
            And appended the IF and phase keys of the param dictionary. Each of these is a np array where 1 data point represents 1 ns (same as the waveforms).
        """

        y_wait = np.linspace(0, 0, int(program_line[1]))
        data_draw[0] = np.append(data_draw[0], (y_wait))
        data_draw[1] = np.append(data_draw[1], (y_wait))

        # extend the IF and phase by the length of the wf
        for key in ["intermediate_frequency", "phase", "q1asm_offset_i", "q1asm_offset_q"]:
            if param.get(f"{key}_new", False) is True:
                param[key].extend([param[key][-1]] * (len(y_wait) - 1))
                param[f"{key}_new"] = False
            else:
                param[key].extend([param[key][-1]] * len(y_wait))
        return data_draw

    def _handle_gain_draw(self, program_line, param, register):
        """Updates the param dictionary when a gain is set in the program

        Args:
            data_draw (list): nested list for each waveform, data points until current time.
            program_line (tuple): line of the Q1ASM program parsed with a gain or offset instruction.
            param (dictionary): parameters of the bus (IF, phase, offset, hardware modulation).

        Returns:
            Appends the param dictionary
        """
        i_val, q_val = program_line[1].split(", ")
        i_val = float(self._get_value(i_val, register)) / 32767
        q_val = float(self._get_value(q_val, register)) / 32767
        param["gain_i"], param["gain_q"] = i_val, q_val
        return param

    def _handle_offset(self, program_line, param):
        """Updates the param dictionary when an offset is set in the program

        Args:
            data_draw (list): nested list for each waveform, data points until current time.
            program_line (tuple): line of the Q1ASM program parsed with an offset instruction.
            param (dictionary): parameters of the bus (IF, phase, offset, hardware modulation).

        Returns:
            Appends the param dictionary
        """
        offi, offq = map(int, program_line[1].split(","))

        if param["hardware_modulation"]:
            scaling_offset = param["max_voltage"] / np.sqrt(2)
        else:
            scaling_offset = param["max_voltage"]

        for x, off in zip(["q1asm_offset_i", "q1asm_offset_q"], [offi, offq]):
            new_key = f"{x}_new"
            if param[new_key]:
                param[x][-1] = off * scaling_offset / 32767
            else:
                param[x].append(off * scaling_offset / 32767)
            param[new_key] = True
        return param

    def _handle_freq_phase_draw(self, program_line, param, register, key):
        """Updates the param dictionary when a freq or phase is set in the program

        Args:
            data_draw (list): nested list for each waveform, data points until current time.
            program_line (tuple): line of the Q1ASM program parsed with a freq or phase instruction.
            param (dictionary): parameters of the bus (IF, phase, offset, hardware modulation).
            key (string): the key is freq or phase.

        Returns:
            Appends the param dictionary.
        """
        new_key = f"{key}_new"
        if param[new_key]:
            param[key][-1] = self._get_value(program_line[1], register)
        else:
            param[key].append(self._get_value(program_line[1], register))
        param[new_key] = True
        return param

    def _handle_reset_phase_draw(self, param):
        """Handles a reset phase

        Args:
            param (dictionary): parameters of the bus (IF, phase, offset, hardware modulation).

        Returns:
            Sets the phase as 0 in the param dictionary.
        """
        if param["phase_new"]:
            param["phase"][-1] = 0
        else:
            param["phase"].append(0)
        param["phase_new"] = True
        return param

    def _handle_add_draw(self, register, program_line):
        """Updates the register dictionary when a line of the parsed program has a move command.

        Args:
            register (dictionary): registers of the Q1ASM.
            program_line (tuple): line of the Q1ASM program parsed with a freq or phase instruction.

        Returns:
            Updated register.
        """
        a, b, destination = program_line[1].split(", ")
        register[destination] = self._get_value(a, register) + self._get_value(b, register)
        return register

    def _get_value(self, x, register):
        """
        Args:
            x (string|int|float): desired value or variable.
            register (dictionary): registers of the Q1ASM.

        Returns:
            If the input is a number it returns a float; if the input is a key of the registery it returns th evalue as a float
        """
        if x is not None:
            if x.isdigit():
                return float(x)
            if x in register:
                return float(register[x])
        return None

    def _parse_program(self, sequences):
        """Parses the program dictionary of the sequence.
        Args:
            sequences (dictionary): for each bus, it is made up of nested dictionaries (waveforms,weights,acquisitions and program)

        Returns:
            Returns seq_parsed_program with each section (setup/main) as a list of tuple (instruction, numerical value, (tuple of loop label), index)
            Example: Q1ASM has play 0,1,30 -  the equivalent seq_parsed_program is (play,'0,1,30', (),1)
                where 1 is the index and () is a tuple of the loop labels
                ie: (avg_0, loop_0) meaning the current isntruction is part of 2 loops, avg_0 as top and loop_0 as nested.

        """
        seq_parsed_program = {}
        for bus in sequences:  # Iterate through the bus of the sequences
            sequence = sequences[bus].todict()
            program_line = sequence["program"].split("\n")
            processed_lines = []

            # parse all lines of qprogram and deal with special case of reset phase
            for line in program_line:
                stripped_line = line.strip()
                if stripped_line.startswith("reset_ph"):
                    processed_lines.append("reset_ph             2")
                elif stripped_line.startswith("nop"):
                    processed_lines.append("nop             2")
                else:
                    processed_lines.append(stripped_line)
            line_data = "\n".join(processed_lines)
            pattern = r"(\w+):|(\w+)(?:\s+([^\n]*))?"
            matches = re.findall(pattern, line_data)  # (section/loop, instruction, numerical value)

            program_parsed = {
                "setup": [],
                "main": [],
            }  # each section is a list of tuples (instruction, numerical value, (tuple of loop label), index)
            index = 0  # Track execution order
            # Create a list of the program section made of tuples (command, args, index)
            loop_label = ()
            for section, instruction, numerical_value in matches:
                if section:
                    if section == "setup":
                        current_section = section
                        index = 0
                    if section == "main":
                        current_section = section
                        index = 0
                    elif section not in ["setup", "main"]:
                        loop_label += (section,)  # add the label of the loop
                elif instruction:
                    numerical_value = numerical_value if numerical_value else ""
                    program_parsed[current_section].append(
                        (instruction, numerical_value, loop_label, index)
                    )  # Store index
                    index += 1  # Increment order index
                    for la in loop_label:  # remove the @, eg: Q1ASM has @loop_0 and we want loop_0
                        if ("@" + la) in numerical_value:
                            loop_label = tuple(l for l in loop_label if l != la)
                sequence["program"] = program_parsed
            del sequence[
                "program"
            ][
                "main"
            ][
                -3:
            ]  # delete the last 3 lines of the Q1ASM that are always hardcoded - tempers with the _new flag later on if not removed here
            seq_parsed_program[bus] = sequence
        return seq_parsed_program

    def draw(self, sequencer, runcard_data=None, averages_displayed=False) -> dict:
        """Parses the program dictionary of the sequence, plots the waveforms and generates waveform data.
        Args:
            sequencer: The compiled qprogram, either at the platform or qprogram level.
            runcard_data (dictionary): parameters of the bus (IF, phase, offset, hardware modulation) retrieved from the runcard if using the platform
                This gets renamed as param to overwrite/add values from the sequencer.
            averages_displayed (bool): Determines how looping variables are handled. If False (default), all loops
                on the sequencer starting with `avg_` will only iterate once. If True, all iterations are displayed.
            loops_displayed (bool): Determines how looping variables are handled. If False (default), all loops
                on the sequencer starting with `loop_` will only iterate once. If True, all iterations are displayed.


        Returns:
            data_draw (dictionary): A dictionary where keys are bus aliases and values are lists containing numpy arrays for
                the I and Q components. This includes all data points used for plotting the waveforms.

        Note:
            This function also **plots** the waveforms using the generated data.

        """
        Q1ASM_ordered = self._parse_program(
            sequencer.sequences.copy()
        )  # (instruction, value, label of the loops, index)
        data_draw = {}
        parameters = {}
        for bus, _ in Q1ASM_ordered.items():
            # Load data from the runcard or create the keys of the dict containing all paraemters (frequency, phase, offsets, gains, etc...)
            if runcard_data is not None:
                parameters[bus] = {
                    key: runcard_data[bus][key] for key in runcard_data[bus]
                }  # retrieve runcard data if the qblox draw is called when a platform has been built
                IF = parameters[bus]["intermediate_frequency"] * 4
                parameters[bus]["intermediate_frequency"] = [IF]
                parameters[bus]["ac_offset_i"] = parameters[bus]["offset_i"]
                parameters[bus]["ac_offset_q"] = parameters[bus]["offset_q"]
                if parameters[bus]["instrument_name"] in {"QCM", "QCM-RF"}:
                    parameters[bus]["max_voltage"] = 2.5
                elif parameters[bus]["instrument_name"] in {"QRM", "QRM-RF"}:
                    parameters[bus]["max_voltage"] = 0.5
            else:  # no runcard uploaded- running qp directly
                parameters[bus] = {}
                parameters[bus]["intermediate_frequency"] = [0]
                parameters[bus]["ac_offset_i"] = [0]
                parameters[bus]["ac_offset_q"] = [0]
                parameters[bus]["dac_offset_i"] = [0]
                parameters[bus]["dac_offset_q"] = [0]
                parameters[bus]["hardware_modulation"] = True  # if plotting directly from qp, plot i and q
                parameters[bus]["max_voltage"] = 1
                parameters[bus]["instrument_name"] = "QProgram"
            parameters[bus]["q1asm_offset_i"] = [0]
            parameters[bus]["q1asm_offset_q"] = [0]
            parameters[bus]["phase"] = [0]

            # flags to determine if the phase or freq has been updated
            parameters[bus]["phase_new"] = True
            parameters[bus]["intermediate_frequency_new"] = True
            parameters[bus]["q1asm_offset_i_new"] = True
            parameters[bus]["q1asm_offset_q_new"] = True

            wf1: list[float] = []
            wf2: list[float] = []
            param = parameters[bus]
            instructions_ran = []  # keep track of the instructions that have been done
            data_draw[bus] = [wf1, wf2]
            label_done = []  # list to keep track of the label once they have been looped over
            wf = Q1ASM_ordered[bus]["waveforms"].items()

            # Loop through the program to store the register and have the information on the loops
            register = {}
            register["avg_no_loop"] = 1
            loop_info = {}
            for Q1ASM_line in Q1ASM_ordered[bus]["program"]["main"]:
                if Q1ASM_line[0] == "move":
                    reg = Q1ASM_line[1].split(",")[1].strip()
                    value = Q1ASM_line[1].split(",")[0].strip()
                    register[reg] = int(value)

                # sorted labels (label, [start index, end index, register key])
                _, value, label, index = Q1ASM_line
                for l in label:
                    if l not in loop_info:
                        loop_info[l] = [index, index, None]
                    else:
                        loop_info[l][1] = index
                        loop_info[l][2] = value.split(",")[0]
                        if l.startswith("avg") and not averages_displayed:
                            loop_info[l][2] = "avg_no_loop"
                sorted_labels = sorted(loop_info.items(), key=lambda x: x[1][0])

            for Q1ASM_line in Q1ASM_ordered[bus]["program"]["main"]:

                def process_loop(recursive_input, i):
                    (label, [start, end, value]) = recursive_input
                    if label not in label_done:
                        label_done.append(label)
                    for x in range(register[value], 0, -1):
                        current_idx = start
                        while current_idx <= end:
                            item = Q1ASM_ordered[bus]["program"]["main"][current_idx]
                            wf = Q1ASM_ordered[bus]["waveforms"].items()
                            _, value, label, _ = item
                            for la in label:
                                if la not in label_done:  # nested loop
                                    new_label = la
                                    result = next(
                                        (element for element in sorted_labels if element[0] == new_label), None
                                    )  # retrieve the start/end/variable of the new label
                                    current_idx = process_loop(result, current_idx)
                                    label_index = {}
                                    # check if there is a nested loop, if yes need to remove it from label_dne, otherwise it wont loop over in the next iteration of the parent
                                    for a in label_done:
                                        element = next((e for e in sorted_labels if e[0] == a), None)[1][0]
                                        label_index[a] = int(element)
                                    max_value = max(label_index.values())
                                    max_keys = [key for key, value in label_index.items() if value == max_value]
                                    label_done.remove(max_keys[0])

                            item = Q1ASM_ordered[bus]["program"]["main"][current_idx]
                            wf = Q1ASM_ordered[bus]["waveforms"].items()
                            instructions_ran.append(item[-1])
                            self._call_handlers(item, param, register, data_draw[bus], wf)
                            current_idx += 1
                    return current_idx

                if (
                    Q1ASM_line[2] and Q1ASM_line[-1] not in instructions_ran
                ):  # if there is a loop label and if the index has not been ran before
                    index = 0
                    for x in sorted_labels:
                        if x[0] == Q1ASM_line[2][0]:
                            input_recursive = x
                            break  # Stop as soon as the first match is found
                    process_loop(input_recursive, index)

                elif Q1ASM_line[-1] not in instructions_ran:  # run if no loop label
                    self._call_handlers(Q1ASM_line, param, register, data_draw[bus], wf)

            # remove the latest freq, phase and offset data points if nothing played after
            for key in ["intermediate_frequency", "phase", "q1asm_offset_i", "q1asm_offset_q"]:
                if param[f"{key}_new"]:
                    param[key].pop()
            parameters[bus] = param

        data_draw = self._oscilloscope_plotting(data_draw, parameters)
        return data_draw

    def _oscilloscope_plotting(self, data_draw, parameters):
        """Plots the waveform data and applies the phase and frequency np array to the data
        Args:
            parameters (dictionary): parameters of all buses (IF, phase, offset, hardware modulation).
            data_draw (dictionary): A dictionary where keys are bus aliases and values are lists containing numpy arrays for
                the I and Q components. This includes all data points used for plotting the waveforms.

        Returns:
            data_draw (dictionary): A dictionary where keys are bus aliases and values are lists containing numpy arrays for
                the I and Q components. This includes all data points used for plotting the waveforms. This function modifies this dictionary,
                it adds the offsets, the phase and the frequency to the waveforms.

        Note:
            This function also **plots** the waveforms using the generated data.
        """

        data_keys = list(data_draw.keys())

        fig = go.Figure()

        for idx, key in enumerate(data_keys):
            q1asm_offset_i = np.array(parameters[key]["q1asm_offset_i"])
            q1asm_offset_q = np.array(parameters[key]["q1asm_offset_q"])
            volt_bounds = parameters[key]["max_voltage"]
            dac_offset_i, dac_offset_q = parameters[key]["dac_offset_i"], parameters[key]["dac_offset_q"]
            ac_offset_i, ac_offset_q = (
                parameters[key]["ac_offset_i"] * volt_bounds / np.sqrt(2),
                parameters[key]["ac_offset_q"] * volt_bounds / np.sqrt(2),
            )
            if not parameters[key]["hardware_modulation"]:  # if hardware modulation is disabled, do not plot Q
                ac_offset_i = ac_offset_i * volt_bounds
                waveform_flux = np.clip(
                    (np.array(data_draw[key][0]) + q1asm_offset_i + ac_offset_i + dac_offset_i),
                    -volt_bounds,
                    volt_bounds,
                )
                data_draw[key][0] = waveform_flux
                data_draw[key][1] = None
                fig.add_trace(go.Scatter(y=waveform_flux, mode="lines", name="Flux"))
            else:
                ac_offset_i, ac_offset_q = (
                    ac_offset_i * volt_bounds / np.sqrt(2),
                    ac_offset_q * volt_bounds / np.sqrt(2),
                )
                wf1, wf2 = data_draw[key][0], data_draw[key][1]
                fs = 1e9  # sampling frequency of the qblox
                t = np.arange(0, len(wf1)) / fs

                # make freq and phase np arrays and convert from qblox values
                freq = np.array(parameters[key]["intermediate_frequency"]) / 4
                phase = np.array(parameters[key]["phase"]) * (2 * np.pi / 1e9)

                cos_term = np.cos(2 * np.pi * freq * t + phase)
                sin_term = np.sin(2 * np.pi * freq * t + phase)

                # Add the offsets to the waveforms and ensure it is in the voltage range of the instrument
                wf1_offsetted = np.clip((np.array(wf1) + q1asm_offset_i), -volt_bounds, volt_bounds)
                wf2_offsetted = np.clip((np.array(wf2) + q1asm_offset_q), -volt_bounds, volt_bounds)
                path0 = (
                    (cos_term * np.array(wf1_offsetted) - sin_term * np.array(wf2_offsetted))
                    + dac_offset_i
                    + ac_offset_i
                )
                path1 = (
                    (sin_term * np.array(wf1_offsetted) + cos_term * np.array(wf2_offsetted))
                    + dac_offset_q
                    + ac_offset_q
                )

                # clip the final signal
                path0_clipped = np.clip(path0, -volt_bounds, volt_bounds)
                path1_clipped = np.clip(path1, -volt_bounds, volt_bounds)

                data_draw[key][0], data_draw[key][1] = path0_clipped, path1_clipped

                fig.add_trace(go.Scatter(y=path0_clipped, mode="lines", name=f"{key} I"))
                fig.add_trace(go.Scatter(y=path1_clipped, mode="lines", name=f"{key} Q"))

        if parameters[key]["instrument_name"] == "QProgram":
            fig.update_yaxes(title_text="Amplitude [a.u.]")
        else:
            fig.update_yaxes(title_text="Voltage [V]")
        fig.update_xaxes(title_text="Time [ns]")

        # Update layout
        fig.update_layout(
            height=200 * len(data_keys),
            width=1100,
            title_text="QBlox Oscillator simulation",
            showlegend=True,
        )
        fig.show()

        return data_draw
