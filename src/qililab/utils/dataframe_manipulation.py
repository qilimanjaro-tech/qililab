"""Utilities for usual dataframe manipulation"""
import pandas as pd


def concatenate_creating_new_index_name(dataframe_list: list[pd.DataFrame], new_index_name: str) -> pd.DataFrame:
    """Concatenates an ordered list of dataframes into a single one, adding a new named column copying the index of
     the final concatenated dataframe.

     The result dataframe will have as columns the union of the original dataframes plus the new column with a copy
     of the final index.

     The index structure of the dataframes will not be considered when creating the new one (as opposed to when
     normally using a dataframe, where you would get a multiindex if previous index was structured).

     Example:
                                                                    new_index_name (copy of left index)
                                                                                   v
     df0                                df1                                      |NEW' BIN Q   I   A Phase
       | BIN Q   I   A   Phase            | BIN Q   I   A   Phase              0 | 0 ' 0   1   1   1   0   ] df0
     0 | 0   1   1   1   0        +     0 | 0   0   0   0   0          =       1 | 1 ' 1   1   1   1   0   ]
     1 | 1   1   1   1   0              1 | 1   0   0   0   0                  2 | 2 ' 0   0   0   0   0     ] df1
                                                                               3 | 3 ' 1   0   0   0   0     ]

     Args:
         dataframe_list (list[df]): list of dataframes to concatenate
         new_index_name (str): name to be given to the new column containing the copy of the final index

    Returns:
        pd.Dataframe: the new dataframe
    """
    concatenated_df = pd.concat(dataframe_list, ignore_index=True)
    concatenated_df.index.rename(new_index_name, inplace=True)
    concatenated_df.reset_index(inplace=True)
    return concatenated_df


def concatenate_creating_new_concatenation_index_name(
    dataframe_list: list[pd.DataFrame], new_concatenation_index_name: str
) -> pd.DataFrame:
    """Concatenates an ordered list of dataframes into a single one, adding a new named colum containing the position
     from the concatenation_list.

     The result dataframe will have as columns the union of the original dataframes plus the new column that tells you
     from which element of the concatenation_list it came.

     Example:
                                                        new_concatenation_index_name (position of concatenation)
                                                                                   v
     df0                                df1                                      |NEW' BIN Q   I   A Phase
       | BIN Q   I   A   Phase            | BIN Q   I   A   Phase              0 | 0 ' 0   1   1   1   0   ] df0
     0 | 0   1   1   1   0        +     0 | 0   0   0   0   0          =       1 | 0 ' 1   1   1   1   0   ]
     1 | 1   1   1   1   0              1 | 1   0   0   0   0                  2 | 1 ' 0   0   0   0   0     ] df1
                                                                               3 | 1 ' 1   0   0   0   0     ]

     Args:
         dataframe_list (list[df]): list of dataframes to concatenate
         new_concatenation_index_name (str): name of the new column containing the position from the concatenation_list.

    Returns:
        pd.Dataframe: the new dataframe
    """
    for index, dataframe in enumerate(dataframe_list):
        dataframe[new_concatenation_index_name] = index
        col = dataframe.pop(new_concatenation_index_name)
        dataframe.insert(0, col.name, col)

    return pd.concat(dataframe_list, ignore_index=True)


def concatenate_creating_new_index_name_and_concatenation_index_name(
    dataframe_list: list[pd.DataFrame], new_index_name: str, new_concatenation_index_name: str
) -> pd.DataFrame:
    """Concatenates an ordered list of dataframes into a single one, adding two new named columns, one that copies
     the index of the final concatenated dataframe and another that contains the position from the concatenation_list.

     The result dataframe will have as columns the union of the original dataframes plus the two new columns of the
     "concatenate_creating_new_index_name", "concatenate_creating_new_concatenation_index_name" functions defined above.

     The index structure of the dataframes will not be considered when creating the new one (as opposed to when
     normally using a dataframe, where you would get a multiindex if previous index was structured).

     Example:                                                          new_index_name
                                                                                   v   new_concatenation_index_name
                                                                                   v    v
     df0                                df1                                      |NEW1 NEW2' BIN Q   I   A Phase
       | BIN Q   I   A   Phase            | BIN Q   I   A   Phase              0 | 0    0  ' 0   1   1   1   0   ] df0
     0 | 0   1   1   1   0        +     0 | 0   0   0   0   0          =       1 | 1    0  ' 1   1   1   1   0   ]
     1 | 1   1   1   1   0              1 | 1   0   0   0   0                  2 | 2    1  ' 0   0   0   0   0     ] df1
                                                                               3 | 3    1  ' 1   0   0   0   0     ]

     Args:
         dataframe_list (list[df]): list of dataframes to concatenate
         new_index_name (str):  name to be given to the new column containing the copy of the final index
         new_concatenation_index_name (str): name of the new column containing the position from the concatenation_list.
    Returns:
        pd.Dataframe: the new dataframe
    """
    dataframe_list = [
        concatenate_creating_new_concatenation_index_name(
            dataframe_list=dataframe_list,
            new_concatenation_index_name=new_concatenation_index_name,
        )
    ]

    return concatenate_creating_new_index_name(dataframe_list=dataframe_list, new_index_name=new_index_name)
