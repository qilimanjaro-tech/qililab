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

"""Nested Dictionary Iterator"""
from typing import Generator

import pandas as pd


def nested_dict_to_path_tuples(dict_obj: dict) -> Generator:
    """This function accepts a nested dictionary as argument and iterate over all values of nested dictionaries and
    lists, returning a tuple where each element contains the full path until arriving to the value.
    """

    for key, value in dict_obj.items():
        if isinstance(value, dict):
            # If value is dict then iterate over all its values
            for pair in nested_dict_to_path_tuples(value):
                yield key, *pair

        elif isinstance(value, (list, tuple)):
            # If value is list then iterate over its enumeration, adding the indices as keys to the dict
            for pair in ((index, value) for (index, value) in enumerate(value)):
                yield key, *pair

        else:
            # If value is not dict type then yield the value
            yield key, value


def nested_dict_to_path_value_list(dict_obj: dict) -> list:
    """Transform a nested dict into a list of [key0, keyN, value] into a list using the nested_dict_to_path_tuples
    generator"""
    return list(nested_dict_to_path_tuples(dict_obj=dict_obj))


def nested_dict_to_pandas_dataframe(dict_obj: dict) -> pd.DataFrame:
    """Transform a nested dict into a pandas dataframe, with a (multi)index as `key0/key1/.../keyN`, and a single
    column `value`. A more classical table structure can be easily recovered by calling the `.reset_index()` method of
    the dataframe instance."""
    path_value_list = nested_dict_to_path_value_list(dict_obj)

    indices = (unnested_result[:-1] for unnested_result in path_value_list)
    values = (unnested_result[-1:] for unnested_result in path_value_list)

    pandas_index = pd.MultiIndex.from_frame(pd.DataFrame(indices))
    return pd.DataFrame(values, index=pandas_index, columns=["value"])
