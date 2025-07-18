def null_column(df, column):
    """
    Null the specified column in the dataframe.
    
    :param df: DataFrame to process.
    :param column: Column to null.
    :return: DataFrame with nulled column.
    """
    if column in df.columns:
        # Create a copy to avoid modifying the original
        df_copy = df.copy()
        df_copy[column] = None
        return df_copy
    else:
        raise ValueError(f"Column '{column}' does not exist in the DataFrame")
