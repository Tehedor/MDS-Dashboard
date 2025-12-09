# utils/clean_functions/_1_assign_timestamp.py
import logging
import pandas as pd

def assign_timestamp_index(subdataset):
    """
    Usa subdataset.df y subdataset.metadata['timestamp_col']
    para convertir el timestamp en índice.
    """
    df = subdataset.df
    timestamp_col = subdataset.metadata.get("timestamp_col", "Timestamp")

    if timestamp_col not in df.columns:
        raise RuntimeError(
            f"[assign_timestamp_index] Columna timestamp '{timestamp_col}' no encontrada"
        )

    # convertir a datetime
    df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors="coerce")

    before = len(df)
    df = df.dropna(subset=[timestamp_col])
    logging.info(f"[0] assign_timestamp_index → limpiadas {before - len(df)} filas corruptas")

    # ordenar
    df = df.sort_values(timestamp_col)

    # colocar índice
    df = df.set_index(timestamp_col)

    logging.info(f"[0] Timestamp index aplicado → dtype: {df.index.dtype}")

    # devolver el dataframe para que SubDataset lo guarde como self.df
    return df
