import os
import glob
import pandas as pd
from tqdm import tqdm

def load_and_process_data(file_pattern: str, max_files: int = None ) -> pd.DataFrame:
    """
    Loads and concatenates data from multiple CSV files into a single DataFrame,
    processes timestamps, and sorts the data.

    Args:
        file_pattern (str): Glob pattern to find the data files (e.g., "data/*.csv").

    Returns:
        pd.DataFrame: A pandas DataFrame with the combined data and a datetime index.
    """
    file_list = glob.glob(file_pattern)

    # Filtrar por año en el nombre
    # if year_filter:
    #     file_list = [f for f in file_list if year_filter in os.path.basename(f)]
    #     print(f"📅 Filtering files containing '{year_filter}' in name → {len(file_list)} found")

    # if not file_list:
    #     raise FileNotFoundError(f"No files found with pattern {file_pattern} and filter {year_filter}")

    # if max_files is not None:
    #     file_list = file_list[:max_files]
    #     print(f"⚙️  Limiting to first {max_files} files")

    print(f"{len(file_list)} files found:")
    for file_path in file_list:
        print(f"  -> {os.path.basename(file_path)}")
    print("-" * 50)

    data_frames = [pd.read_csv(file, sep=',', decimal='.')
                   for file in tqdm(file_list, desc="Loading files")]

    df = pd.concat(data_frames, ignore_index=True)

    # Clean column names and set a proper time index
    print("Number of rows before loading:", len(df))
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    df.dropna(subset=['Timestamp'], inplace=True)
    print("Number of rows after deleting rows with invalid timestamps:", len(df))
    df.set_index('Timestamp', inplace=True)
    df.sort_index(inplace=True)

    return df