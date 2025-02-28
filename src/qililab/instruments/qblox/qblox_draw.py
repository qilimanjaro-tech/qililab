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
from .qblox_module import QbloxModule
# from qililab.platform import Platform

# TODO:
# way to plot all methods at once
# add other methods offered by qblox for the q1asm - ask experimentalists if they ever use anythg else, have a list of the ones you can plot

class QbloxDraw:

    def get_value_from_metadata(self,metadata, move_reg, key, division_factor=None):
        if key in metadata: #metadata is the runcard
            if metadata[key] in move_reg.keys():#check if it's in the register
                if division_factor:
                    return float(float(move_reg[metadata[key]]) / float(division_factor))
                else:
                    return float(move_reg[metadata[key]])
            else:
                return float(metadata[key])
        return None

    def _handle_play_draw(self, stored_data, act_play, diction, move_reg, parameters):
        if act_play[0] == "play":
            output_path1, output_path2, _ = map(int, act_play[1].split(','))
            freq_value = self.get_value_from_metadata(parameters, move_reg, 'intermediate_frequency', division_factor=4)
            print("freq",freq_value)
            print(move_reg)
            # freq_value = None

            #dynamic offset
            off_i = parameters.get("offset_i", 0)
            off_q = parameters.get("offset_q", 0)

            #static offset
            offset_out0 = parameters.get("offset_out0", 0)
            offset_out1 = parameters.get("offset_out1", 0)
            
            #gains
            gain_i = parameters.get("gain_i", 0)
            gain_q = parameters.get("gain_q", 0)
            # sample_rate=1/(2e9)
            # sample_rate=5e-5
            # sample_rate = float(0.0005)
            # retrieve the wavform data
            for waveform_key, waveform_value in diction:
                if waveform_value['index'] == output_path1:
                    if freq_value is not None:
                        # x = np.linspace(0,1,len(waveform_value['data']),(1/sample_rate))
                        x = np.arange(0,1,len(waveform_value['data']))

                        carrier = np.cos(2 * np.pi * freq_value * x)
                        carrier = 1
                        # signal = np.cos(2*np.pi*freq_value)*np.array(waveform_value['data'])
                        # print(np.array(waveform_value['data']))
                        # print("signal",signal)

                    else:
                        carrier = 1
                    if parameters["hardware_modulation"] and off_i==0 and offset_out0 ==0:
                        scaling_factor = 1.8
                        max_voltage = 1.8
                    elif not parameters["hardware_modulation"]:
                        scaling_factor = 2.5
                        max_voltage = 2.5
                    else: #hardware mod on but there are some offsets applied
                        scaling_factor = 1.8
                        max_voltage = 2.5
                    scaled_array = np.array(waveform_value['data']) * scaling_factor
                    off_i_scaled = off_i * scaling_factor
                    # stored_data[0] = np.clip((np.append(stored_data[0], ((scaled_array)*gain_i + off_i_scaled + offset_out0)*carrier)),None,max_voltage)
                    stored_data[0] = np.append(stored_data[0],np.clip((((scaled_array)*gain_i + off_i_scaled + offset_out0)*carrier),None,max_voltage))
                    # stored_data[0] = np.append(stored_data[0],signal)
                    print("max",max_voltage)
                elif waveform_value['index'] == output_path2:
                    if freq_value is not None:
                        # x = np.linspace(0,1,len(waveform_value['data']))
                        # x = np.arange(0,1,len(waveform_value['data']),sample_rate)
                        # carrier = np.sin(2 * np.pi * freq_value * x)
                        carrier = 1
                    else:
                        carrier = 1
                    if parameters["hardware_modulation"] and off_q==0 and offset_out1 ==0:
                        scaling_factor = 1.8
                        max_voltage = 1.8
                    elif not parameters["hardware_modulation"]:
                        scaling_factor = 2.5
                        max_voltage = 2.5
                    else: #hardware mod on but there are some offsets applied
                        scaling_factor = 1.8
                        max_voltage = 2.5
                    scaled_array = np.array(waveform_value['data']) * scaling_factor
                    off_q_scaled = off_q * scaling_factor
                    stored_data[1] = np.clip(np.append(stored_data[1], ((scaled_array)*gain_q + off_q_scaled + offset_out1)*carrier),None,max_voltage)
                    # stored_data[1] = np.append(stored_data[1],np.clip((((scaled_array)*gain_q + off_q_scaled + offset_out1)*carrier),None,max_voltage))
                    print("max",max_voltage)
        return stored_data
    
    def _handle_acquire_draw(self, stored_data, act_play): #is it always 4ns, in one case it is 12ns ??????????????????????????
        if act_play[0] == "acquire_weighed":
            y_wait = np.linspace(0, 0, 4)
            stored_data = [np.append(stored_data[0], y_wait), np.append(stored_data[1], y_wait)]
        return stored_data

    def _handle_wait_draw(self, stored_data, act_wait, parameters):
        if act_wait[0] == "wait":
             #dynamic offset
            off_i = parameters.get("offset_i", 0)
            off_q = parameters.get("offset_q", 0)

            #static offset
            offset_out0 = parameters.get("offset_out0", 0)
            offset_out1 = parameters.get("offset_out1", 0)
            
            if parameters["hardware_modulation"] and off_i==0 and offset_out0 ==0:
                scaling_factori = 1.8
                max_voltagei = 1.8
            elif not parameters["hardware_modulation"]:
                scaling_factori = 2.5
                max_voltagei = 2.5
            else: #hardware mod on but there are some offsets applied
                scaling_factori = 1.8
                max_voltagei = 2.5
            
            if parameters["hardware_modulation"] and off_q==0 and offset_out1 ==0:
                scaling_factorq = 1.8
                max_voltageq = 1.8
            elif not parameters["hardware_modulation"]:
                scaling_factorq = 2.5
                max_voltageq = 2.5
            else: #hardware mod on but there are some offsets applied
                scaling_factorq = 1.8
                max_voltageq = 2.5

            off_i_scaled = off_i * scaling_factori
            off_q_scaled = off_q * scaling_factorq
            #dynamic offset


            #static offset
            offset_out0 = parameters.get("offset_out0", 0)
            offset_out1 = parameters.get("offset_out1", 0)
            y_wait = np.linspace(0, 0, int(act_wait[1]))
            # stored_data[0] = np.clip(np.append(stored_data[0], y_wait + off_i_scaled + offset_out0),None,max_voltagei)
            # stored_data[1] = np.clip(np.append(stored_data[1], y_wait + off_q_scaled + offset_out1),None,max_voltageq)
            stored_data[0] = np.append(stored_data[0], np.clip((y_wait + off_i_scaled + offset_out0),None,max_voltagei))
            stored_data[1] = np.append(stored_data[1], np.clip((y_wait + off_q_scaled + offset_out1),None,max_voltageq))
        return stored_data

    def _handle_gain_draw(self, item, parameters):
        if item[0] == "set_awg_gain":
           gain_i, gain_q =  map(lambda x: float(x) / 32767, item[1].split(','))
           gain = [gain_i,gain_q]
           gains = [x if x is not None else 0 for x in gain]
           parameters["gain_i"],parameters["gain_q"] = gains
        return parameters
    
    def _handle_offset_draw(self, item, parameters):
        if item[0] == "set_awg_offs":
            offset_i, offset_q =  map(lambda x: float(x) / 32767, item[1].split(','))
            off = [offset_i,offset_q]
            offsets = [x if x is not None else 0 for x in off]
            parameters["offset_i"],parameters["offset_q"] = offsets
        return parameters

    def _handle_add_draw(self, move_reg, act_add):
        if act_add[0] == "add":
            a, b, destination = act_add[1].split(", ")
            move_reg[destination] = self._get_value(a, move_reg) + self._get_value(b, move_reg)
        return move_reg

    def _handle_freq_draw(self, item, parameters): #data is latched  only updated under specific conditions, handle case where more than 1 freq, and handle the case where no freq is given
        if item[0] == "set_freq":
            parameters["intermediate_frequency"] = item[1] #overwrite the if if given in the qprogram
        return parameters
    def _get_value(self, x, move_reg):
        if x is not None:
            if x.isdigit():
                return int(x)
            if x in move_reg:
                return int(move_reg[x])
        return None

    def _parse_program(self, sequences):
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

    def draw_oscilloscope(self, result, runcard_data = None):
        Q1ASM_ordered = self._parse_program(result.sequences.copy())
        data_draw = {}
        # [0]: action to be taken
        # [1]: value
        # [2]: label of the loops
        # [3]: index
        for bus,_ in Q1ASM_ordered.items():
            if runcard_data is not None:
                parameters= {key: runcard_data[bus][key] for key in runcard_data[bus]}
            else:
                parameters = {}
            wf1 = []
            wf2 = []
            run_items = []
            data_draw[bus] = [wf1, wf2]
            # if parameters["hardware_modulation"]:
            #     data_draw[bus] = [wf1, wf2]
            # else:
            #     data_draw[bus] = [wf1]

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
            wf = Q1ASM_ordered[bus]['waveforms'].items()

            
            for item in Q1ASM_ordered[bus]["program"]["main"]:
                def process_loop(recursive_input,i):
                    (label, [start, end, value]) = recursive_input
                    if label not in label_done:
                        label_done.append(label)
                    for x in range(move_reg[value], 0, -1):
                        current_idx = start
                        while current_idx <= end:
                            item = Q1ASM_ordered[bus]["program"]["main"][current_idx]
                            wf = Q1ASM_ordered[bus]['waveforms'].items()
                            _, value, label, _ = item
                            for la in label:
                                if la not in label_done:
                                    new_label = la
                                    result = next((element for element in sorted_labels if element[0] == new_label), None) #retrieve the start/end/variable of the new label
                                    current_idx = process_loop(result,current_idx)
                                    label_index = {}
                                    #check if there is a nested loop, if yes need to remove it from label_dne, otherwise it wont loop over in the next iteration of the parent
                                    for a in label_done:
                                        element = next((e for e in sorted_labels if e[0] == a), None)[1][0]
                                        label_index[a]=int(element)
                                    max_value = max(label_index.values())
                                    max_keys = [key for key, value in label_index.items() if value == max_value]
                                    label_done.remove(max_keys[0])

                            item = Q1ASM_ordered[bus]["program"]["main"][current_idx]
                            wf = Q1ASM_ordered[bus]['waveforms'].items()
                            run_items.append(item[-1])
                            self._handle_freq_draw(item, parameters)
                            self._handle_offset_draw(item, parameters)
                            data_draw[bus] = self._handle_play_draw(data_draw[bus], item, wf, move_reg, parameters)
                            data_draw[bus] = self._handle_acquire_draw(data_draw[bus], item)
                            data_draw[bus] = self._handle_wait_draw(data_draw[bus], item, parameters)
                            self._handle_add_draw(move_reg, item)
                            current_idx +=1
                    return current_idx

                # if item[2] and item[2][-1] not in label_done and item[-1] not in run_items:  # if there is a loop label
                if item[2] and item[-1] not in run_items:  # if there is a loop label
                    index=0
                    # input = next(x for x in sorted_labels if x[0] == item[2][0])
                    for x in sorted_labels:
                        if x[0] == item[2][0]: #should only ever have to deal with the first tuple element if more than 1, then it is nested and done in the recursive function
                            input = x
                            break  # Stop as soon as the first match is found
                    process_loop(input,index)
                elif item[-1] not in run_items: #ensure not running the ones that have already been ran
                    self._handle_freq_draw(item, parameters)
                    self._handle_offset_draw(item, parameters)
                    data_draw[bus] = self._handle_play_draw(data_draw[bus], item, wf, move_reg,parameters)
                    data_draw[bus] = self._handle_acquire_draw(data_draw[bus], item)
                    data_draw[bus] = self._handle_wait_draw(data_draw[bus], item, parameters)
                    self._handle_add_draw(move_reg, item)
                else:
                    pass
        
        # arr2 = np.cos(2*np.pi*10000000)*np.array(data_draw["drive"][0])
        # print("array",arr2)
        # x = list(range(1, len(arr2) + 1))

        # import plotly.graph_objects as go


        # Create the plot
        # fig = go.Figure(data=go.Scatter(x=x, y=arr2, mode='lines+markers'))



        # # Show the plot
        # fig.show()
        # Plot the waveforms with plotly
        data_keys = list(data_draw.keys())
        # # Create subplots
        # fig = make_subplots(rows=len(data_keys), cols=1, subplot_titles=data_keys)
        # Add traces
        # for idx, key in enumerate(data_keys):
        #     if runcard_data[key]["hardware_modulation"]:
        #         legend = ["I","Q"]
        #     else:
        #         legend = ["flux"]
        x = np.arange(0,len(wf1))
        fs = 1e9  # Sampling frequency (1 GHz)
        print(len(wf1))
        
        wf1,wf2 = data_draw["drive"][0],data_draw["drive"][1]
        t = np.arange(0, len(wf1)) / fs
        a = (np.cos(2 * np.pi * 10000000*t))
        b = np.sin(2 * np.pi * 10000000*x)
        # path0 = np.array(wf1)*a-np.array(wf2)*np.sin(2 * np.pi * 10000000*x)
        # path1 = np.array(wf1)*(np.sin(2 * np.pi * 10000000*x))+np.array(wf2)*a
        path0 = np.array(wf1)*a
        path1 = np.array(wf2)*a
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        # Create a subplot figure with 2 y-axes
        # fig = make_subplots(rows=1, cols=2, subplot_titles=("Line Chart"))
        fig = go.Figure()
        # Add line chart
        fig.add_trace(go.Scatter(x=t, y=path0, mode='lines', name='Line Plot'))

        # Add bar chart
        # fig.add_trace(go.Scatter(x=x_values, y=y_values, mode='lines+markers', name='Line Plot'))

        # # Update layout
        # fig.update_layout(title_text="Dual Graphs with Plotly", showlegend=True)

        # Show figure
        fig.show()
    #     for i, arr in enumerate(data_draw[key]):
    #         if not runcard_data[key]["hardware_modulation"] and i > 0:
    #             break #don't plot the Q if hadware modulation is disabled
    #         print("arr",arr)
    #         if i ==0:
    #             x = np.arange(0,len(arr))
    #             arr2 = np.array(arr)*(np.cos(2 * np.pi * 10000000*x)*(1/np.sqrt(2)))
    #             print("mod",arr)
    #             DEBUG = np.cos(2 * np.pi * 10000000*x)
    #             # print()
    #             fig.add_trace(go.Scatter(y=arr2, mode='lines', name=f'{key} {legend[i]}',legendgroup=idx), row=idx + 1, col=1)
    #         if i ==1:
    #             x = np.arange(0,len(arr))
    #             arr2 = np.array(arr)*(np.sin(2 * np.pi * 10000000*x)*(1/np.sqrt(2)))
    #             print("mod",arr)
    #             DEBUG = np.cos(2 * np.pi * 10000000*x)
    #             # print()
    #             fig.add_trace(go.Scatter(y=arr2, mode='lines', name=f'{key} {legend[i]}',legendgroup=idx), row=idx + 1, col=1)
    #         # elif i ==1:
    #         #     x = np.arange(0,len(arr))
    #         #     arr2 = np.array(arr)*np.sin(2 * np.pi * 10000000*x)*(1/np.sqrt(2))
    #         #     print("mod",arr)
    #         #     DEBUG = np.cos(2 * np.pi * 10000000*x)
    #         #     print()
    #         #     fig.add_trace(go.Scatter(y=arr2, mode='lines', name=f'{key} {legend[i]}',legendgroup=idx), row=idx + 1, col=1)
    #         # else:
    #         #     fig.add_trace(go.Scatter(y=arr, mode='lines', name=f'{key} {legend[i]}',legendgroup=idx), row=idx + 1, col=1)

    # # Add axis titles
    # for i, key in enumerate(data_keys):
    #     fig.update_xaxes(title_text="Time (ns)", row=i + 1, col=1)  # X-axis title at the bottom
    #     fig.update_yaxes(title_text="Amplitude", row=i + 1, col=1)  # Y-axis title for each subplot

    # # Update layout
    # fig.update_layout(height=300 * len(data_keys), width=1100, legend_tracegroupgap = 180, title_text="Oscillator simulation")
        fig.show()
        return data_draw
