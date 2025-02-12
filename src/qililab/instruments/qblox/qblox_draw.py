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
import math
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

    def _handle_play_draw(self, stored_data, act_play, diction,move_reg,freq):
        if act_play[0] == "play":
            output_path1, output_path2, wait_play = map(int, act_play[1].split(','))
            #retrieve the freq value
            if freq['freq'] is not None:
                freq_value = move_reg[freq['freq']]/4
                print("freq value",freq_value)
            else: freq_value= 1
            
            #math.cos(2*math.pi*freq_value)

            # retrieve the wavform data
            for waveform_key, waveform_value in diction:
                
                if waveform_value['index'] == output_path1:
                    x = np.linspace(0,1,len(waveform_value['data']))
                    carrier = np.cos(2 * np.pi * freq_value * x)
                    stored_data[0] = np.append(stored_data[0], np.array(waveform_value['data'])*carrier)
                elif waveform_value['index'] == output_path2:
                    x = np.linspace(0,1,len(waveform_value['data']))
                    carrier = np.cos(2 * np.pi * freq_value * x)
                    stored_data[1] = np.append(stored_data[1], np.array(waveform_value['data'])*carrier)
        return stored_data
    
    def _handle_acquire_draw(self, stored_data, act_play): #is it always 4ns, in one case it is 12ns ??????????????????????????
        if act_play[0] == "acquire_weighed":
            y_wait = np.linspace(0, 0, 4)
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

    def _handle_freq_draw(self, freq, act_freq): #data is latched  only updated under specific conditions, handle case where more than 1 freq, and handle the case where no freq is given
        if act_freq[0] == "set_freq":
            freq['freq'] = act_freq[1]
        print(freq)
        return freq

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
        Q1ASM_ordered = self._parse_program(result.sequences.copy())
        data_draw = {}
        # [0]: action to be taken
        # [1]: value
        # [2]: label of the loops
        # [3]: index

        for bus, bus_data in Q1ASM_ordered.items():
            print("BUS",bus)
            # bus="drive"
            wf1 = []
            wf2 = []
            run_items = []
            freq = {'freq':None}
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
                _, value, label, index = item
                for l in label:
                    if l not in appearance:
                        appearance[l] = [index, index, None]  # First and last index, plus second arg in a list
                    else:
                        appearance[l][1] = index  # Update last appearance
                        appearance[l][2] = value.split(",")[0]
                sorted_labels = sorted(appearance.items(), key=lambda x: x[1][0])

            for item in Q1ASM_ordered[bus]["program"]["main"]:
                wf = Q1ASM_ordered[bus]['waveforms'].items()

                def process_loop(recursive_input,i):
                    (label, [start, end, value]) = recursive_input
                    if label not in label_done:
                        label_done.append(label)
                    print(label,start,end,value,move_reg[value])
                    # if there is in label done a label that has a start greater than the current label you should drop it from label label_done
                    #remove the necessary labels from label done:
                    print("top level running")
                    for x in range(move_reg[value], 0, -1):
                        print("TOPPPPP", x, move_reg)
                        current_idx = start
                        while current_idx <= end:
                            print("idx",current_idx,end,"x:",x)
                            item = Q1ASM_ordered[bus]["program"]["main"][current_idx]
                            wf = Q1ASM_ordered[bus]['waveforms'].items()
                            _, value, label, _ = item
                            for la in label:
                                if la not in label_done:
                                    new_label = la
                                    result = next((element for element in sorted_labels if element[0] == new_label), None) #retrieve the start/end/variable of the new label
                                    print("going into the recursive with input",result)
                                    current_idx = process_loop(result,current_idx)
                                    print("exit the recursive")
                                    label_index = {}
                                    #check if there is a nested loop, if yes need to remove it from label_dne, otherwise it wont loop over in the next iteration of the parent
                                    for a in label_done:
                                        element = next((e for e in sorted_labels if e[0] == a), None)[1][0]
                                        label_index[a]=int(element)
                                    max_value = max(label_index.values())
                                    max_keys = [key for key, value in label_index.items() if value == max_value]
                                    label_done.remove(max_keys[0])

                            print("label done",label_done)

                            item = Q1ASM_ordered[bus]["program"]["main"][current_idx]
                            wf = Q1ASM_ordered[bus]['waveforms'].items()
                            print("run item",item)
                            run_items.append(item[-1])
                            print(run_items)
                            self._handle_freq_draw(freq,item)
                            data_draw[bus] = self._handle_play_draw(data_draw[bus], item, wf, move_reg,freq)
                            data_draw[bus] = self._handle_acquire_draw(data_draw[bus], item)
                            data_draw[bus] = self._handle_wait_draw(data_draw[bus], item)
                            self._handle_add_draw(move_reg, item)
                            current_idx +=1
                    return current_idx

                if item[2] and item[2][-1] not in label_done and item[-1] not in run_items:  # if there is a loop label
                    index=0
                    print("running the initial loop",item)
                    process_loop(sorted_labels[0],index) #TO DO: the 0 might cause problems if some loops arent nested

                elif item[-1] not in run_items: #ensure not running the ones that have already been ran
                    print("should not play this",item)
                    self._handle_freq_draw(freq,item)
                    data_draw[bus] = self._handle_play_draw(data_draw[bus], item, wf, move_reg,freq)
                    data_draw[bus] = self._handle_acquire_draw(data_draw[bus], item)
                    data_draw[bus] = self._handle_wait_draw(data_draw[bus], item)
                    self._handle_add_draw(move_reg, item)
                    
                else:
                    pass

            # #data treatment
            # #frequency
            # data[bus] = {'frequency':self._get_value(freq['freq'],move_reg)}
            # print(data)

        # Plot the waveforms with plotly
        # print()
        data_keys = list(data_draw.keys())
        print("data_keys",data_keys)

        # Create subplots
        fig = make_subplots(rows=len(data_keys), cols=1, subplot_titles=data_keys)
        legend_IQ = ["I","Q"]
        # Add traces
        for idx, key in enumerate(data_keys):
            for i, arr in enumerate(data_draw[key]):
                fig.add_trace(go.Scatter(y=arr, mode='lines', name=f'{key} {legend_IQ[i]}',legendgroup=idx), row=idx + 1, col=1)

        # Add axis titles
        for i, key in enumerate(data_keys):
            fig.update_xaxes(title_text="Time (ns)", row=i + 1, col=1)  # X-axis title at the bottom
            fig.update_yaxes(title_text="Amplitude", row=i + 1, col=1)  # Y-axis title for each subplot

        # Update layout
        fig.update_layout(height=300 * len(data_keys), width=1100, legend_tracegroupgap = 180, title_text="Oscillator simulation")
        fig.show()
        return data_draw
