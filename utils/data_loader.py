# utils/data_loader.py
import pandas as pd
import numpy as np
import logging
from pathlib import Path

def cargar_y_formatear_datasets(dataset_paths, timestamp_col='Timestamp'):
    """
    Carga, concatena y marca valores anómalos y vacíos.
    - No rellena la columna de tiempo.
    - Convierte timestamps de forma segura.
    - Elimina filas con timestamp inválido (NaT) para evitar '1970-01-01'.
    """
    dataframes = []
    for path in dataset_paths:
        logging.info(f"Cargando dataset: {path}")
        df = pd.read_csv(path)

        # Detectar si la columna de tiempo existe (case-insensitive)
        posibles_col = [c for c in df.columns if c.lower() == timestamp_col.lower()]
        if not posibles_col:
            raise ValueError(f"No se encontró la columna de timestamp en {path}")
        col_real = posibles_col[0]

        # Convertir a datetime de forma robusta
        df[col_real] = pd.to_datetime(df[col_real], errors='coerce')

        # Aviso si hay timestamps no convertidos en este archivo
        n_invalid = df[col_real].isna().sum()
        if n_invalid > 0:
            logging.warning(f"{path}: {n_invalid} filas con timestamp no válido (NaT). Serán eliminadas al unir.")

        # Rellenar NaN en las demás columnas (no sobre la columna de tiempo)
        otras_cols = [c for c in df.columns if c != col_real]
        if otras_cols:
            df[otras_cols] = df[otras_cols].fillna(999999.0)

        dataframes.append(df)

    # Concatenar
    df_merged = pd.concat(dataframes, ignore_index=True)

    # Determinar columna temporal real en el merged (por si cambió)
    posibles_col_merged = [c for c in df_merged.columns if c.lower() == timestamp_col.lower()]
    col_real_merged = posibles_col_merged[0] if posibles_col_merged else timestamp_col

    # Asegurarse de que la columna timestamp es datetime (si algo quedó raro)
    df_merged[col_real_merged] = pd.to_datetime(df_merged[col_real_merged], errors='coerce')

    # Eliminar filas sin timestamp (evita fechas tipo 1970)
    n_before = len(df_merged)
    df_merged = df_merged.dropna(subset=[col_real_merged]).reset_index(drop=True)
    n_after = len(df_merged)
    n_dropped = n_before - n_after
    if n_dropped > 0:
        logging.info(f"Se han eliminado {n_dropped} filas sin timestamp válido tras la unión.")

    # Ordenar por timestamp
    df_merged = df_merged.sort_values(col_real_merged).reset_index(drop=True)

    return df_merged
