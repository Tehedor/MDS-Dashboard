import pandas as pd

def clean_and_unify_duplicates(df: pd.DataFrame, df_name: str) -> pd.DataFrame:
    """
    Finds duplicate timestamps in a DataFrame, displays them, and then
    unifies the values by averaging them to ensure a unique index.

    Args:
        df (pd.DataFrame): The input DataFrame to clean.
        df_name (str): The name of the DataFrame for display messages.

    Returns:
        pd.DataFrame: The cleaned DataFrame with a unique index.
    """
    is_duplicate_index = df.index.duplicated(keep=False)
    duplicate_rows = df[is_duplicate_index].sort_index()

    print(f"\n--- Checking for duplicates in DataFrame {df_name} ---")
    if not duplicate_rows.empty:
        print(f"Found {duplicate_rows.shape[0]} rows with duplicate timestamps in {df_name}.")
        # Optionally display some of them: display(duplicate_rows.head())
    else:
        print(f"No rows with duplicate timestamps were found in {df_name}.")

    rows_before = len(df)
    # Unify rows by index by averaging their values
    df_unified = df.groupby(df.index).mean()
    rows_after = len(df_unified)

    if rows_before > rows_after:
        print(f"{rows_before - rows_after} duplicate rows were unified in {df_name}.")
        print(f"Rows before: {rows_before} -> Rows after: {rows_after}")
    else:
        print("The index was already unique. No changes were made to the number of rows.")

    return df_unified