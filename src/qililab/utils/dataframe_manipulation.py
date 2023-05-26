"""Utilities for usual dataframe manipulation"""
import pandas as pd


def concatenate_creating_new_index_name(dataframe_list: list[pd.DataFrame], new_index_name: str) -> pd.DataFrame:
    """Concatenates an ordered list of dataframes into a single one, adding a new named column containing the index of
     the dataframe the data came from in the original list.
     The result dataframe will have as columns the union of the original dataframes plus the new column with the
     indices.
     The index structure of the dataframes will not be considered when creating the new one (as opposed to when
     normally using a dataframe, where you would get a multiindex if previous index was structured).

     Args:
         dataframe_list: list of dataframes to concatenate
         new_index_name: name to be given to the new column containing the indices

    Returns:
        pd.Dataframe: the new dataframe
    """
    concatenated_df = pd.concat(dataframe_list, ignore_index=True)
    concatenated_df.index.rename(new_index_name, inplace=True)
    concatenated_df.reset_index(inplace=True)
    return concatenated_df


def concatenate_creating_new_index_name_and_index_concatenation_name(
    dataframe_list: list[pd.DataFrame], new_index_name: str, new_concatenation_index_name: str
) -> pd.DataFrame:
    # TODO: CHANGE THIS DOCSTRING
    """Concatenates an ordered list of dataframes into a single one, adding a new named column containing the index of
     the dataframe the data came from in the original list.
     The result dataframe will have as columns the union of the original dataframes plus the new column with the
     indices.
     The index structure of the dataframes will not be considered when creating the new one (as opposed to when
     normally using a dataframe, where you would get a multiindex if previous index was structured).

     Args:
         dataframe_list: list of dataframes to concatenate
         new_index_name: name to be given to the new column containing the indices

    Returns:
        pd.Dataframe: the new dataframe
    """
    for index, df in enumerate(dataframe_list):
        df[new_concatenation_index_name] = index

    return concatenate_creating_new_index_name(dataframe_list=dataframe_list, new_index_name=new_index_name)
