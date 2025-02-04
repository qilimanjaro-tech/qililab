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

# TODO:
# binary conversion
# way to plot all methods at once
# add other methods


class QbloxDraw:
    # def __init__(self,sequences):
    #     self.sequences = sequences
    # def __init__(self):
    #     # self.sequences = sequences
    #     self._QbloxCompiler: QbloxCompiler

    def _handle_play_draw(self, stored_data, act_play, diction):
        if act_play[0] == "play":
            output_path1, output_path2, wait_play = map(int, act_play[1].split(','))
            # retrieve the wavform data
            for waveform_key, waveform_value in diction:
                if waveform_value['index'] == output_path1:
                    stored_data[0] = np.append(stored_data[0], np.array(waveform_value['data']))
                elif waveform_value['index'] == output_path2:
                    stored_data[1] = np.append(stored_data[1], np.array(waveform_value['data']))
            y_wait = np.linspace(0, 0, wait_play)
            stored_data = [np.append(stored_data[0], y_wait), np.append(stored_data[1], y_wait)]
        return stored_data

    def _handle_wait_draw(self, stored_data, act_wait):
        if act_wait[0] == "wait":
            y_wait = np.linspace(0, 0, int(act_wait[1]))
            stored_data[0] = np.append(stored_data[0], y_wait)
            stored_data[1] = np.append(stored_data[1], y_wait)
        return stored_data

    def _handle_add_draw(self, move_reg, act_add):
        if act_add[0] == "add":
            a, b, destination = act_add[1].split(", ")
            move_reg[destination] = self._get_value(a, move_reg) + self._get_value(b, move_reg)
        return move_reg

    # def _handle_freq_draw(self, freq, act_freq):
    #     if act_freq[0] == "set_freq":
    #         freq['freq'] = act_freq[1]
    #     return freq

    def _get_value(self, x, move_reg):
        if x is not None:
            if x.isdigit():
                return int(x)
            if x in move_reg:
                return int(move_reg[x])
        return None

    def _parse_program(self, sequences):
        # sequences = QbloxCompilationOutput.sequences
        # make the Q1ASM data easier to read
        Q1ASM_ordered = {}
        for bus in sequences:  # Iterate through the dictionary
            content_dict = sequences[bus].todict()
            lines = content_dict["program"].split("\n")
            processed_lines = []
            for line in lines:
                stripped_line = line.strip()
                if stripped_line.startswith("nop"):
                    processed_lines.append("nop             2")
                else:
                    processed_lines.append(stripped_line)
            content_dict["program"] = "\n".join(processed_lines)  # Update mutable dictionary
            sequences[bus] = content_dict

        for bus in sequences:
            Q1ASM_ordered[bus] = None  # Initialize
            dict_bus = sequences[bus]
            pattern = r'(\w+):|(\w+)(?:\s+([^\n]*))?'  # Captures labels and commands
            matches = re.findall(pattern, dict_bus["program"])
            command_dict = {"setup": [], "main": []}  # Sections with ordered lists
            current_section = "setup"  # Default to setup
            index = 0  # Track execution order
            # Create a list of the program section made of tuples (command, args, index)
            sub_label = ()
            for label, command, arguments in matches:
                if label:
                    if label == "main":
                        current_section = label  # Switch to new section (e.g., "main")
                        index = 0
                    elif label != "setup" and label != "main":
                        sub_label += (label,)
                elif command:
                    args = arguments if arguments else ""
                    command_dict[current_section].append((command, args, sub_label, index))  # Store index
                    index += 1  # Increment order index
                    for la in sub_label:
                        if ("@" + la) in args:
                            sub_label = tuple(l for l in sub_label if l != la)
                dict_bus["program"] = command_dict
            Q1ASM_ordered[bus] = dict_bus  # Store structured result
        return Q1ASM_ordered

    def draw_data(self, result):
        Q1ASM_ordered = self._parse_program(result.sequences)
        data_draw = {}
        # [0]: action to be taken
        # [1]: value
        # [2]: label of the loops
        # [3]: index
        index_label = 0

        for bus, bus_data in Q1ASM_ordered.items():
            wf1 = []
            wf2 = []
            # freq = {'freq':None}
            # index_label[bus] = {}
            index_label = 0
            # data = {bus: None}
            data_draw[bus] = [wf1, wf2]
            label_done = []  # list to keep track of the label once they have been looped over

            # create a dict to get all the variables assigned to a registery through move
            move_reg = {}
            for action in Q1ASM_ordered[bus]["program"]["main"]:
                if action[0] == "move":
                    reg = action[1].split(",")[1].strip()
                    value = action[1].split(",")[0].strip()
                    move_reg[reg] = int(value)
            appearance = {}
            # get the index for the loop - might be replaced with a while loop, ie: while the label is still on keep doing that and then have a for loop inside
            for item in Q1ASM_ordered[bus]["program"]["main"]:
                # for item in Q1ASM_ordered[bus]["program"]["main"]:
                _, value, label, index = item
                # print("top",value)
                for l in label:
                    if l not in appearance:
                        appearance[l] = [index, index, None]  # First and last index, plus second arg in a list
                    else:
                        appearance[l][1] = index  # Update last appearance
                        appearance[l][2] = value.split(",")[0]
                sorted_labels = sorted(appearance.items(), key=lambda x: x[1][0])
            # print("sorted",sorted_labels)

            for item in Q1ASM_ordered[bus]["program"]["main"]:
                wf = Q1ASM_ordered[bus]['waveforms'].items()

                def process_loop(start, end, value_init, current_label):
                    """Process a loop from start to end index."""
                    value = value_init
                    for x in range(move_reg[value], 0, -1):
                        move_reg[value_init] = x
                        i = start
                        while i < end:
                            item = Q1ASM_ordered[bus]["program"]["main"][i]
                            wf = Q1ASM_ordered[bus]['waveforms'].items()
                            _, value, label, _ = item
                            data_draw[bus] = self._handle_play_draw(data_draw[bus], item, wf)
                            data_draw[bus] = self._handle_wait_draw(data_draw[bus], item)
                            self._handle_add_draw(move_reg, item)
                            # self._handle_freq_draw(freq,item)

                            # loop throught the labels to see if recursion is needed; if new label and hasnt been covered before (ie: not in label_done) then yes
                            for la in label:
                                if la == current_label or la in label_done:
                                    pass
                                else:
                                    new_label = la
                                    result = next((item for item in sorted_labels if item[0] == new_label), None)
                                    (new_label, [new_start, new_end, new_value]) = result
                                    label_done.append(new_label)
                                    # current_label=new_label
                                    process_loop(new_start + 1, new_end, new_value, new_label)  # recursive loop if there is a new label
                            i += 1

                if item[2]:  # if there is a loop label
                    if index_label >= len(sorted_labels):
                        pass
                    else:
                        (label, [start, end, value]) = sorted_labels[index_label]
                        index_label += 1
                        current_label = label
                        if label not in label_done:
                            label_done.append(label)
                            process_loop(start, end, value, current_label)
                else:
                    data_draw[bus] = self._handle_play_draw(data_draw[bus], item, wf)
                    data_draw[bus] = self._handle_wait_draw(data_draw[bus], item)
                    self._handle_add_draw(move_reg, item)
                    # self._handle_freq_draw(freq,item)

            # #data treatment
            # #frequency
            # data[bus] = {'frequency':self._get_value(freq['freq'],move_reg)}
            # print(data)

        # Plot the waveforms with plotly
        # print()
        data_keys = list(data_draw.keys())

        # Create subplots
        fig = make_subplots(rows=len(data_keys), cols=1, subplot_titles=data_keys)

        # Add traces
        for idx, key in enumerate(data_keys):
            for i, arr in enumerate(data_draw[key]):
                fig.add_trace(go.Scatter(y=arr, mode='lines', name=f'{key} {i + 1}'), row=idx + 1, col=1)

        # Add axis titles
        for i, key in enumerate(data_keys):
            fig.update_xaxes(title_text="Time (ns)", row=i + 1, col=1)  # X-axis title at the bottom
            fig.update_yaxes(title_text="Amplitude", row=i + 1, col=1)  # Y-axis title for each subplot

        # Update layout
        fig.update_layout(height=300 * len(data_keys), width=800, title_text="Oscillator Simulation")
        fig.show()
        return data_draw
