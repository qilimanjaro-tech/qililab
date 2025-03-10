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
from plotly.subplots import make_subplots

class QbloxDraw:
    def _call_handlers(self, program_line, param, register, data_draw, wf):
        action_type = program_line[0]
        if action_type == "set_freq":
            param = self._handle_freq_phase_draw(program_line, param, register, "intermediate_frequency")
        elif action_type == "set_ph":
            param = self._handle_freq_phase_draw(program_line, param, register, "phase")
        elif action_type == "reset_ph":
            param = self._handle_reset_phase_draw(param)
        elif action_type == "set_awg_offs":
            param = self._handle_gain_off_draw(program_line, param, "offset", 0)
        elif action_type == "set_awg_gain":
            param = self._handle_gain_off_draw(program_line, param, "gain", 1)
        elif action_type == "play":
            data_draw = self._handle_play_draw(data_draw, program_line, wf, register, param)
        elif action_type == "wait":
            data_draw = self._handle_wait_draw(data_draw, program_line, param)
        elif action_type == "add":
            self._handle_add_draw(register, program_line)
        return param, register, data_draw

    def calculate_scaling_and_offsets(self, param, i_or_q):
        if i_or_q == "I":
            scaling_factor, max_voltage = self._get_scaling_factors(
                param, param.get("offset_i", 0), param.get("offset_out0", 0)
            )
            gain = param.get("gain_i", 1)
            offset_scaled = param.get("offset_i", 0) * scaling_factor
            offset_out = param.get("offset_out0", 0)
        elif i_or_q == "Q":
            scaling_factor, max_voltage = self._get_scaling_factors(
                param, param.get("offset_q", 0), param.get("offset_out1", 0)
            )
            gain = param.get("gain_q", 1)
            offset_scaled = param.get("offset_q", 0) * scaling_factor
            offset_out = param.get("offset_out1", 0)
        return scaling_factor, max_voltage, gain, offset_scaled, offset_out

    def _get_scaling_factors(self, param, static_off, dynamic_off):
        if param["hardware_modulation"]:
            return (1.8, 1.8) if static_off == 0 and dynamic_off == 0 else (1.8, 2.5)
        return (2.5, 2.5)  # (scaling factor, max voltage)

    def get_value_from_metadata(self, metadata, register, key, division_factor=None):
        if key in metadata:  # metadata is the runcard
            if metadata[key] in register.keys():  # check if it's in the register
                return (
                    float(register[metadata[key]]) / float(division_factor)
                    if division_factor
                    else float(register[metadata[key]])
                )
                return float(metadata[key])
        return None

    def _handle_play_draw(self, stored_data, act_play, diction, register, param):
        output_path1, output_path2, _ = map(int, act_play[1].split(","))
        # modify and store the wf data
        for waveform_key, waveform_value in diction:
            index = waveform_value["index"]
            if index in [output_path1, output_path2]:
                iq = "I" if index == output_path1 else "Q"
                scaling_factor, max_voltage, gain, offset_scaled, offset_out = self.calculate_scaling_and_offsets(
                    param, iq
                )
                scaled_array = np.array(waveform_value["data"]) * scaling_factor
                modified_waveform = np.clip(scaled_array * gain + offset_scaled + offset_out, None, max_voltage)
                stored_data[0 if index == output_path1 else 1] = np.append(
                    stored_data[0 if index == output_path1 else 1], modified_waveform
                )

        # extend the IF and phase by the length of the wf
        for key in ["intermediate_frequency", "phase"]:
            if param.get(f"{key}_new", False) is True:
                param[key].extend([param[key][-1]] * (len(scaled_array) - 1))
                param[f"{key}_new"] = False
            else:
                param[key].extend([param[key][-1]] * len(scaled_array))
        return stored_data

    def _handle_wait_draw(self, stored_data, act_wait, param):
        # Dynamic offsets
        off_i, off_q = param.get("offset_i", 0), param.get("offset_q", 0)

        # Static offsets
        offset_out0, offset_out1 = param.get("offset_out0", 0), param.get("offset_out1", 0)

        scaling_factori, _ = self._get_scaling_factors(param, off_i, offset_out0)
        scaling_factorq, _ = self._get_scaling_factors(param, off_q, offset_out1)

        # dynamic offset
        off_i_scaled = off_i * scaling_factori
        off_q_scaled = off_q * scaling_factorq

        # static offset
        offset_out0 = param.get("offset_out0", 0)
        offset_out1 = param.get("offset_out1", 0)
        y_wait = np.linspace(0, 0, int(act_wait[1]))
        stored_data[0] = np.append(stored_data[0], (y_wait + off_i_scaled + offset_out0))
        stored_data[1] = np.append(stored_data[1], (y_wait + off_q_scaled + offset_out1))

        # extend the IF and phase by the length of the wf
        for key in ["intermediate_frequency", "phase"]:
            if param.get(f"{key}_new", False) is True:
                param[key].extend([param[key][-1]] * (len(y_wait) - 1))
                param[f"{key}_new"] = False
            else:
                param[key].extend([param[key][-1]] * len(y_wait))
        return stored_data

    def _handle_gain_off_draw(self, item, param, key, default):
        i_val, q_val = (float(x) / 32767 for x in item[1].split(","))
        param[f"{key}_i"], param[f"{key}_q"] = i_val or default, q_val or default
        return param

    def _handle_freq_phase_draw(self, item, param, register, key):
        new_key = f"{key}_new"
        if param[new_key]:
            param[key][-1] = self._get_value(item[1], register)
        else:
            param[key].append(self._get_value(item[1], register))
        param[new_key] = True
        return param

    def _handle_reset_phase_draw(self, param):
        if param["phase_new"]:
            param["phase"][-1] = 0
        else:
            param["phase"].append(0)
        param["phase_new"] = True
        return param

    def _handle_add_draw(self, register, act_add):
        a, b, destination = act_add[1].split(", ")
        register[destination] = self._get_value(a, register) + self._get_value(b, register)
        return register

    def _get_value(self, x, register):
        if x is not None:
            if x.isdigit():
                return float(x)
            if x in register:
                return float(register[x])
        return None

    def _parse_program(self, sequences):
        seq_parsed_program = {}
        for bus in sequences:  # Iterate through the bus of the sequences
            sequence = sequences[bus].todict()
            program_line = sequence["program"].split("\n")
            processed_lines = []

            # parse all lines of qprogram and deal with special cases of nop and reset phase
            for line in program_line:
                stripped_line = line.strip()
                if stripped_line.startswith("nop"):
                    processed_lines.append("nop             2")
                elif stripped_line.startswith("reset_ph"):
                    processed_lines.append("reset_ph             2")
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
            seq_parsed_program[bus] = sequence
        return seq_parsed_program

    def draw_oscilloscope(self, result, runcard_data=None, averages_displayed=False):
        Q1ASM_ordered = self._parse_program(result.sequences.copy())  # (instruction, value, label of the loops, index)
        data_draw = {}
        parameters = {}
        for bus, _ in Q1ASM_ordered.items():
            # Load data from the runcard or create the keys of the dict containing all paraemters (frequency, phase, offsets, gains, etc...)
            if runcard_data is not None:
                parameters[bus] = {
                    key: runcard_data[bus][key] for key in runcard_data[bus]
                }  # retrieve runcard data if the qblox draw is called when a platform has been built
                parameters[bus]["intermediate_frequency"] = [parameters[bus]["intermediate_frequency"]]
            else:
                parameters[bus] = {}
                parameters[bus]["intermediate_frequency"] = [0]
                parameters[bus]["hardware_modulation"] = True  # if plotting directly from qp, plot i and q
            parameters[bus]["phase"] = [0]

            # flags to determine if the phase or freq has been updated
            parameters[bus]["phase_new"] = True
            parameters[bus]["intermediate_frequency_new"] = True

            wf1 = []
            wf2 = []
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

                else:
                    pass

            # remove the latest freq and phase data points if nothing played after
            if param["intermediate_frequency_new"]:
                param["intermediate_frequency"].pop()
            parameters[bus] = param

            if param["phase_new"]:
                param["phase"].pop()
            parameters[bus] = param

        self._oscilloscope_plotting(data_draw, parameters)
        return data_draw

    def _oscilloscope_plotting(self, data_draw, parameters):
        data_keys = list(data_draw.keys())
        fig = make_subplots(rows=len(data_keys), cols=1, subplot_titles=data_keys)

        for idx, key in enumerate(data_keys):
            if not parameters[key]["hardware_modulation"]:  # if hardware modulation is disabled, do not plot Q
                fig.add_trace(
                    go.Scatter(y=np.array(data_draw[key][0]), mode="lines", name="Flux", legendgroup=idx),
                    row=idx + 1,
                    col=1,
                )
            else:
                wf1, wf2 = data_draw[key][0], data_draw[key][1]
                fs = 1e9  # sampling frequency of the qblox
                t = np.arange(0, len(wf1)) / fs
                freq = np.array(parameters[key]["intermediate_frequency"]) / 4
                phase = np.array(parameters[key]["phase"]) * (2 * np.pi / 1e9)

                cos_term = np.cos(2 * np.pi * freq * t + phase)
                sin_term = np.sin(2 * np.pi * freq * t + phase)
                path0 = cos_term * np.array(wf1) - sin_term * np.array(wf2)
                path1 = sin_term * np.array(wf1) + cos_term * np.array(wf2)

                fig.add_trace(go.Scatter(y=path0, mode="lines", name=f"{key} I", legendgroup=idx), row=idx + 1, col=1)
                fig.add_trace(go.Scatter(y=path1, mode="lines", name=f"{key} Q", legendgroup=idx), row=idx + 1, col=1)

        # Add axis titles
        for i, key in enumerate(data_keys):
            fig.update_xaxes(title_text="Time [ns]", row=i + 1, col=1)
            fig.update_yaxes(title_text="Voltage [V]", row=i + 1, col=1)

        # Update layout
        fig.update_layout(
            height=260 * len(data_keys),
            width=1100,
            legend_tracegroupgap=210,
            title_text="Oscillator simulation",
            showlegend=True,
        )
        fig.show()
