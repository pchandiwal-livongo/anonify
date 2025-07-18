def null_column(df, column):
    """
    Null the specified column in the dataframe.
    
    :param df: DataFrame to process.
    :param column: Column to null.
    :return: DataFrame with nulled column.
    """
    if column in df.columns:
        df[column] = None
    else:
        raise ValueError(f"Column '{column}' does not exist in the DataFrame")
    return df
