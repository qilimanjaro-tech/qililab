import pandas as pd


def insert_index_level_into_dataframe(dataframe: pd.DataFrame, default_value: str | int, position: int = 0, ):
    """ Modify a dataframe adding to it an index level with a default value.

    Args:
        dataframe (pd.DataFrame): dataframe to modify
        default_value (str): value to set into the index
        position (int): position this index should be placed into

    Returns:
        None
    """
    dataframe_index = dataframe.index.to_frame()
    dataframe_index.insert(position, 'result', [default_value] * dataframe_index.shape[0])
    dataframe.index = pd.MultiIndex.from_frame(dataframe_index)
